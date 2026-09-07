#!/usr/bin/env python3
"""Tests for the OOXML extractors used by tkm:index-docs.

Stdlib `unittest` on purpose — the modules under test have no dependencies, so their
tests should not introduce one either. Runs with either:

    python3 -m unittest discover claude/skills/index-docs/scripts/tests
    python3 -m pytest claude/skills/index-docs/scripts/tests
"""

import binascii
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import extract_embedded_media as media  # noqa: E402
import ooxml_text as text  # noqa: E402

DRAWING_NS = 'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
WORD_NS = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
SHEET_NS = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'


def png(colour: int = 0) -> bytes:
    """Smallest valid PNG. `colour` varies the bytes so hashes differ."""
    def chunk(tag: bytes, payload: bytes) -> bytes:
        body = tag + payload
        return struct.pack(">I", len(payload)) + body + struct.pack(
            ">I", binascii.crc32(body) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    pixel = bytes([0x78, 0x9C, 0x62, 0x60 + colour, 0x60, 0x60, 0x00, 0x00, 0x00, 0x04, 0x00, 0x01])
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", pixel) + chunk(b"IEND", b"")


def slide_xml(title: str, bullets: list[str]) -> str:
    runs = "".join(f"<a:p><a:r><a:t>{b}</a:t></a:r></a:p>" for b in bullets)
    return (f"<p:sld {DRAWING_NS} xmlns:p=\"p\"><p:cSld><p:spTree>"
            f"<p:sp><a:p><a:r><a:t>{title}</a:t></a:r></a:p></p:sp>"
            f"<p:sp>{runs}</p:sp></p:spTree></p:cSld></p:sld>")


class OoxmlTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def write_zip(self, name: str, entries: dict[str, bytes | str]) -> Path:
        path = self.tmp / name
        with zipfile.ZipFile(path, "w") as archive:
            for member, payload in entries.items():
                archive.writestr(member, payload)
        return path


class TestExtractEmbeddedMedia(OoxmlTestCase):
    def test_deduplicates_repeated_images_by_content(self) -> None:
        """A slide master repeats its logo; identical bytes must be written once."""
        deck = self.write_zip("deck.pptx", {
            "ppt/media/image1.png": png(), "ppt/media/image2.png": png(),
            "ppt/media/image3.png": png(),
        })
        result = media.run([deck], self.tmp / "out", cap=20)
        self.assertEqual(result["occurrences"], 3)
        self.assertEqual(result["unique"], 1)
        self.assertEqual(result["deduplicated"], 2)

    def test_distinct_images_are_all_kept(self) -> None:
        deck = self.write_zip("deck.pptx", {
            "ppt/media/image1.png": png(0), "ppt/media/image2.png": png(1),
        })
        self.assertEqual(media.run([deck], self.tmp / "out", cap=20)["unique"], 2)

    def test_cap_limits_extraction_and_is_reported(self) -> None:
        """Exceeding the cap must be visible, never a silent truncation."""
        deck = self.write_zip("deck.pptx", {
            f"ppt/media/image{i}.png": png(i) for i in range(5)
        })
        result = media.run([deck], self.tmp / "out", cap=2)
        self.assertEqual(result["unique"], 2)
        reasons = [p["reason"] for p in result["problems"]]
        self.assertIn("cap-reached", reasons)

    def test_provenance_maps_image_back_to_its_document(self) -> None:
        """Without this the graph keeps nodes pointing at a scratch path."""
        doc = self.write_zip("spec.docx", {"word/media/image1.png": png()})
        result = media.run([doc], self.tmp / "out", cap=20)
        self.assertEqual(list(result["provenance"].values()), [str(doc)])

    def test_all_three_container_layouts_are_searched(self) -> None:
        for name, member in [("a.docx", "word/media/i.png"),
                             ("b.xlsx", "xl/media/i.png"),
                             ("c.pptx", "ppt/media/i.png")]:
            with self.subTest(name=name):
                doc = self.write_zip(name, {member: png()})
                out = self.tmp / f"out-{Path(name).stem}"
                self.assertEqual(media.run([doc], out, cap=20)["unique"], 1)

    def test_non_raster_members_are_ignored(self) -> None:
        """.svg is XML text — the vision path cannot use it."""
        doc = self.write_zip("d.pptx", {"ppt/media/vector.svg": "<svg/>"})
        self.assertEqual(media.run([doc], self.tmp / "out", cap=20)["unique"], 0)

    def test_corrupt_document_is_reported_not_raised(self) -> None:
        broken = self.tmp / "broken.docx"
        broken.write_bytes(b"this is not a zip")
        result = media.run([broken], self.tmp / "out", cap=20)
        self.assertEqual(result["unique"], 0)
        self.assertEqual([p["reason"] for p in result["problems"]], ["not-a-zip"])

    def test_unrelated_suffixes_are_skipped(self) -> None:
        plain = self.tmp / "notes.md"
        plain.write_text("# hi", encoding="utf-8")
        self.assertEqual(media.run([plain], self.tmp / "out", cap=20)["unique"], 0)

    def test_directory_named_like_a_document_is_reported(self) -> None:
        """A real corpus held an unpacked deck: a directory called `<name>.pptx`.
        Skipping it silently reads exactly like a deck with no images."""
        unpacked = self.tmp / "unpacked.pptx"
        unpacked.mkdir()
        result = media.run([unpacked], self.tmp / "out", cap=20)
        self.assertEqual(result["unique"], 0)
        self.assertEqual([p["reason"] for p in result["problems"]], ["not-a-file"])


class TestOoxmlText(OoxmlTestCase):
    def test_pptx_text_is_recovered_with_slide_sections(self) -> None:
        """graphify cannot read .pptx at all, so this is the only route in."""
        deck = self.write_zip("kickoff.pptx", {
            "ppt/slides/slide1.xml": slide_xml("Kiến trúc", ["Portal gọi Ticketing"]),
        })
        body, problem = text.extract(deck)
        self.assertIsNone(problem)
        self.assertIn("## Slide 1 — Kiến trúc", body)
        self.assertIn("- Portal gọi Ticketing", body)

    def test_slides_are_ordered_numerically_not_lexically(self) -> None:
        """slide10 must follow slide2, which a plain string sort gets wrong."""
        deck = self.write_zip("deck.pptx", {
            "ppt/slides/slide2.xml": slide_xml("Second", []),
            "ppt/slides/slide10.xml": slide_xml("Tenth", []),
        })
        body, _ = text.extract(deck)
        self.assertLess(body.index("Second"), body.index("Tenth"))

    def test_docx_paragraphs_are_recovered(self) -> None:
        doc = self.write_zip("spec.docx", {
            "word/document.xml":
                f"<w:document {WORD_NS}><w:body>"
                f"<w:p><w:r><w:t>Reservation giữ 15 phút</w:t></w:r></w:p>"
                f"</w:body></w:document>",
        })
        body, problem = text.extract(doc)
        self.assertIsNone(problem)
        self.assertIn("Reservation giữ 15 phút", body)

    def test_xlsx_shared_strings_are_deduplicated(self) -> None:
        sheet = self.write_zip("req.xlsx", {
            "xl/sharedStrings.xml":
                f"<sst {SHEET_NS}><si><t>Module</t></si><si><t>Module</t></si>"
                f"<si><t>Inventory Store</t></si></sst>",
        })
        body, _ = text.extract(sheet)
        self.assertEqual(body.count("Module"), 1)
        self.assertIn("Inventory Store", body)

    def test_empty_document_yields_no_text_without_raising(self) -> None:
        deck = self.write_zip("empty.pptx", {"ppt/presentation.xml": "<p/>"})
        body, problem = text.extract(deck)
        self.assertEqual(body, "")
        self.assertIsNone(problem)

    def test_corrupt_document_is_reported_not_raised(self) -> None:
        broken = self.tmp / "broken.pptx"
        broken.write_bytes(b"nope")
        self.assertEqual(text.extract(broken), ("", "not-a-zip"))

    def test_unsupported_suffix_is_reported(self) -> None:
        plain = self.tmp / "notes.md"
        plain.write_text("hi", encoding="utf-8")
        self.assertEqual(text.extract(plain), ("", "unsupported-suffix"))

    def test_runs_are_joined_within_a_paragraph(self) -> None:
        """Formatting changes split a sentence into runs. A real deck emitted
        'APPBOX' / 'で配信したお知らせの内容を' / 'Web' / 'サーバー側で取得可能です。'
        as four lines before the runs were joined."""
        deck = self.write_zip("real.pptx", {
            "ppt/slides/slide1.xml":
                f'<p:sld {DRAWING_NS} xmlns:p="p"><a:p><a:r><a:t>タイトル</a:t></a:r></a:p>'
                f'<a:p><a:r><a:t>APPBOX</a:t></a:r><a:r><a:t>で配信した内容を</a:t></a:r>'
                f'<a:r><a:t>Web</a:t></a:r><a:r><a:t>側で取得可能です。</a:t></a:r></a:p></p:sld>',
        })
        body, _ = text.extract(deck)
        self.assertIn("- APPBOXで配信した内容をWeb側で取得可能です。", body)

    def test_short_leading_fragment_is_not_used_as_a_title(self) -> None:
        """Decks often open with a numbering run like '3.' — not a title."""
        deck = self.write_zip("numbered.pptx", {
            "ppt/slides/slide1.xml":
                f'<p:sld {DRAWING_NS} xmlns:p="p"><a:p><a:r><a:t>3.</a:t></a:r></a:p>'
                f'<a:p><a:r><a:t>機能要件の検討</a:t></a:r></a:p></p:sld>',
        })
        body, _ = text.extract(deck)
        self.assertIn("## Slide 1 — (slide 1)", body)
        self.assertIn("- 3.", body)

    def test_xlsx_inline_strings_are_read(self) -> None:
        """Some writers emit `t="inlineStr"` cells and ship no sharedStrings table at
        all; reading only the shared table returned nothing for two real workbooks."""
        sheet = self.write_zip("inline.xlsx", {
            "xl/worksheets/sheet1.xml":
                f'<worksheet {SHEET_NS}><sheetData><row>'
                f'<c t="inlineStr"><is><t>工数</t></is></c>'
                f'<c t="inlineStr"><is><t>会員登録</t></is></c>'
                f'</row></sheetData></worksheet>',
        })
        body, problem = text.extract(sheet)
        self.assertIsNone(problem)
        self.assertIn("工数", body)
        self.assertIn("会員登録", body)


class TestSidecarNaming(OoxmlTestCase):
    def test_same_stem_in_two_directories_does_not_overwrite(self) -> None:
        """A corpus routinely holds a translated copy beside its source under the same
        stem. Naming sidecars by stem alone lost three documents on a real run."""
        payload = {"word/document.xml":
                   f"<w:document {WORD_NS}><w:body><w:p><w:r><w:t>x</w:t></w:r></w:p>"
                   f"</w:body></w:document>"}
        first, second = self.tmp / "a", self.tmp / "b"
        first.mkdir(), second.mkdir()
        for folder in (first, second):
            with zipfile.ZipFile(folder / "prd.docx", "w") as archive:
                for member, body in payload.items():
                    archive.writestr(member, body)

        out = self.tmp / "sidecars"
        text.main([str(first / "prd.docx"), str(second / "prd.docx"), "--out", str(out)])
        self.assertEqual(len(list(out.glob("*.ooxml.md"))), 2)


if __name__ == "__main__":
    unittest.main()
