"""Vietnamese prose for the docs reading-order index. Data only (locale module).

See _nav_strings_en for the key contract. role_labels keyed by _nav_strings.ROLES.
"""
from __future__ import annotations

STRINGS = {
    "title": "Mục lục tài liệu — Thứ tự đọc",
    "intro": (
        "Mục lục này liệt kê tài liệu được sinh ra theo thứ tự đọc khuyến nghị. "
        "Đọc từ trên xuống: định hướng trước, chi tiết sau. Số thứ tự là lộ "
        "trình gợi ý, không phải ràng buộc bắt buộc."
    ),
    "quick_path_label": "Đọc nhanh tối thiểu",
    "col_headers": ("#", "Tài liệu", "Trả lời câu hỏi gì"),
    "roles_heading": "Đọc theo vai trò",
    "role_labels": {
        "new_dev": "Dev mới — vào việc nhanh",
        "reviewer": "Reviewer — quy tắc, phân quyền, contract",
        "pm": "PM / BA — phạm vi và hành vi",
    },
    "layer_labels": {
        1: "Định hướng — hệ thống là gì và tại sao",
        2: "Mô hình nghiệp vụ — thực thể, tính năng, user story",
        3: "Giao diện & hành vi — màn hình, API, quy tắc, phân quyền",
        4: "Đào sâu — luồng, đặc tả từng tính năng, từng màn hình",
    },
    "layer_intros": {
        1: ("Bắt đầu ở đây nếu bạn mới vào. Layer này trả lời hệ thống là gì và "
            "có hình hài ra sao, trước khi đi vào chi tiết."),
        2: ("Từ vựng nghiệp vụ — thực thể, danh mục tính năng và user story mà "
            "mọi thứ khác tham chiếu tới."),
        3: ("Hệ thống hành xử thế nào ở rìa: màn hình người dùng chạm vào, bề "
            "mặt API, quy tắc nghiệp vụ nó áp đặt, và ai được làm gì."),
        4: ("Đào sâu khi bạn cần chi tiết về một luồng, một tính năng hay một "
            "màn hình cụ thể — đọc sau khi các layer trên đã cho bạn bản đồ."),
    },
    "principles_label": "Nguyên tắc",
    "principles": [
        "Đọc từ trên xuống: định hướng (Lớp 1) trước khi đào sâu (Lớp 4).",
        "Thứ tự đánh số là lộ trình gợi ý, không phải phụ thuộc cứng.",
        "Tài liệu chưa có sẽ bị bỏ qua — chạy pass tương ứng để sinh ra.",
    ],
    "footnote": "Các dòng của pass chưa chạy được bỏ qua khỏi mục lục này.",
    # Khối "cách đọc một tính năng" nhiều dòng, render (prune theo entry features/*/)
    # dạng blockquote dưới bảng lớp 4. Thay cho dòng feature_reading_note ở A2. Độ
    # dài list là skeleton — test parity yêu cầu len() bằng nhau giữa các locale.
    "feature_traversal": [
        "Cách đọc một tính năng: mở thư mục của nó, đọc functional-spec.md trước — "
        "làm gì, hành vi ra sao, màn hình hiển thị gì — rồi đọc technical-spec.md để "
        "biết cách triển khai (endpoint, pseudocode, trích dẫn Source).",
        "Để đào sâu một màn hình liệt kê trong functional-spec.md § 5, theo mã SCR### "
        "trong hàng của nó tới docs/screens/SCR###/spec.md (spec liên kết ngược qua "
        "header **Feature**).",
        "Xem generated/screen-flow.md để biết các màn hình của tính năng này nối "
        "với nhau ra sao — màn hình vào, sở hữu và ra.",
    ],
    # Mệnh đề nhân quả "vì sao đọc ở đây" cho bảng thứ tự đọc đơn-thành-phần
    # (chỉ lớp 1-3). Khóa theo "key" của entry trong READING_ORDER. Nối vào ô
    # "trả lời câu hỏi gì" dạng " — <mệnh đề>". Lớp 4 không có mệnh đề ở đây.
    "reading_why": {
        "system_overview": (
            "Đọc đầu tiên — xác định mục đích, phạm vi và các actor chính của sản "
            "phẩm trước khi đi vào bất kỳ chi tiết cấu trúc hay hành vi nào."
        ),
        "architecture": (
            "Đọc sau tổng quan vì sơ đồ tầng, tech stack và luồng dữ liệu chỉ có "
            "nghĩa khi bạn đã biết hệ thống dùng để làm gì."
        ),
        "glossary": (
            "Đọc sau tổng quan để các thuật ngữ dùng chung và dễ nhầm được chốt "
            "trước khi các tài liệu sâu hơn dựa vào chúng."
        ),
        "entities": (
            "Đọc sau khi định hướng — các thực thể dữ liệu cốt lõi là từ vựng mà "
            "danh mục tính năng, user story và API đều tham chiếu tới."
        ),
        "feature_list": (
            "Đọc sau thực thể vì mỗi tính năng được mô tả qua dữ liệu nó chạm vào; "
            "đây là danh mục mà mọi thứ khác trỏ vào."
        ),
        "user_stories": (
            "Đọc sau danh mục tính năng — các story mở rộng mỗi F### thành mục tiêu "
            "cụ thể của actor và ý định nghiệm thu."
        ),
        "screen_list": (
            "Đọc sau các story vì màn hình là nơi những mục tiêu đó trở thành thứ "
            "người dùng nhìn thấy và chạm vào được."
        ),
        "screen_flow": (
            "Đọc sau danh sách màn hình để biết các màn hình trước khi lần theo "
            "cách điều hướng và trạng thái di chuyển giữa chúng."
        ),
        "route_list": (
            "Đọc sau màn hình vì các route là bề mặt backend mà những màn hình đó "
            "gọi tới."
        ),
        "api_map": (
            "Đọc sau danh sách route — nó nhóm các route thô theo resource và thêm "
            "background job, tạo nên hình hài của API."
        ),
        "api_contracts": (
            "Đọc sau bản đồ API khi bạn cần hình dạng request và response chính xác "
            "đằng sau mỗi endpoint đã nhóm."
        ),
        "behavior_logic": (
            "Đọc sau bề mặt API vì các đơn vị BL### mô tả logic async và nền mà các "
            "endpoint và job đó kích hoạt."
        ),
        "permissions_matrix": (
            "Đọc sau các quy tắc — nó chốt vai trò nào được thực hiện mỗi hành động "
            "mà phần còn lại của hệ thống mở ra."
        ),
    },
    # Chú giải định hướng tĩnh (A3): giải thích đồ thị tham chiếu chéo giữa các hệ
    # ID và NƠI mỗi liên kết được ghi lại. KHÔNG phải bảng sinh theo repo. Render
    # (dạng bullet dưới tiêu đề) chỉ khi có feature-list hoặc screen-list.
    "relationship_map_heading": "Các hệ ID liên hệ với nhau ra sao",
    "relationship_map": [
        "**F###** (tính năng) — đơn vị hành vi sản phẩm; liệt kê trong "
        "generated/feature-list.md.",
        "**SCR###** (màn hình) — bề mặt UI mà một tính năng sở hữu; kiểm kê trong "
        "generated/screen-list.md, chi tiết ở docs/screens/SCR###/spec.md.",
        "**ROUTE###** (route) — endpoint backend mà một tính năng sở hữu; kiểm kê "
        "trong generated/route-list.md qua cột Owner F### (api-map.md và "
        "api-contracts.md là các view riêng, không bị ràng buộc — không đối chiếu ở đây).",
        "**US###** (user story) — mục tiêu actor mà một tính năng thỏa mãn; trong "
        "generated/user-stories.md.",
        "Bản đồ trực tiếp theo tính năng (màn hình vào / sở hữu / ra) nằm ở "
        "generated/screen-flow.md § Feature Entry Points.",
    ],
    # A6 — ghi chú theo vai trò, khóa theo ROLES key. Chỉ nối vào dòng của vai trò
    # khi mục cổng (glob features, entry 15) còn sau khi prune.
    "role_notes": {
        "new_dev": (
            "sau mục tính năng, chọn một tính năng và đọc trọn vẹn — xem "
            "“Cách đọc một tính năng” bên dưới"
        ),
    },
    # A4 — README từng tính năng. Khóa file_purposes là (các) tệp vệ tinh (skeleton).
    "feature_readme": {
        "title": "Tính năng {feature} — Hướng dẫn đọc",
        "intro": (
            "Đọc các tệp của tính năng này theo thứ tự, rồi mở đặc tả đầy đủ của "
            "bất kỳ màn hình nào từ bảng dưới."
        ),
        "order_heading": "Thứ tự đọc",
        "screens_heading": "Màn hình trong tính năng này",
        "col_screen": "Màn hình",
        "col_scr": "SCR",
        "col_spec": "Đặc tả",
        "unresolved": "—",
        # Bảng Route/API (v25.0.0) — cùng hình dạng bảng Màn hình ở trên, nhưng mỗi
        # dòng đều trỏ đến route-list.md dùng chung (route không có file đặc tả
        # riêng như spec.md của màn hình).
        "routes_heading": "Route dùng bởi tính năng này",
        "col_route": "Route",
        "col_route_owner": "Method + Path",
        "col_route_spec": "Đặc tả",
        "file_purposes": {
            "functional-spec.md": "làm gì, hành vi ra sao, màn hình hiển thị gì",
            "technical-spec.md": "được triển khai ra sao",
            "test-cases.md": "được kiểm thử ra sao (UT/IT/UAT — tùy chọn)",
        },
    },
    # A5 — mục lục docs/features/README.md.
    "features_index": {
        "title": "Tính năng — Mục lục",
        "intro": (
            "Mọi tính năng trong sản phẩm. Mở một cái và đọc trọn vẹn qua hướng "
            "dẫn đọc của nó."
        ),
    },
    "components_index": {
        "title": "Mục lục thành phần — Thứ tự đọc",
        "intro": (
            "Liệt kê mọi module thành phần theo thứ tự đọc khuyến nghị: "
            "điểm vào / gateway trước, sau đó là domain service, frontend, "
            "fullstack, và node tái sử dụng cuối cùng."
        ),
        "col_num": "#",
        "col_module": "Module",
        "col_role": "Vai trò",
        "role_labels": {
            "gateway": "Gateway",
            "api-gateway": "API Gateway",
            "api_gateway": "API Gateway",
            "backend": "Backend service",
            "service": "Service",
            "frontend": "Frontend",
            "fullstack": "Fullstack",
        },
        "reused_marker": "(tái sử dụng)",
        "system_readme_title": "Tài liệu hệ thống — Thứ tự đọc",
    },
    "aggregate_index": {
        "title": "Hệ thống các hệ thống — Thứ tự đọc",
        "intro": (
            "Mục lục này bao quát tài liệu tổng hợp đa dịch vụ. "
            "Đọc từ trên xuống: tổng quan hệ thống trước, rồi danh mục, "
            "kiến trúc, sở hữu dữ liệu, luồng, từ điển và độ tin cậy."
        ),
        "components_pointer_label": "Tất cả thành phần",
        "components_pointer_desc": (
            "Mục lục tài liệu từng thành phần — tài liệu riêng của mỗi thành phần, "
            "theo thứ tự đọc gợi ý"
        ),
        "roles_heading": "Đọc theo vai trò",
        "parent_pointer": "Thứ tự đọc đầy đủ: [system/README.md](system/README.md).",
        "read_first_heading": "Nên đọc dịch vụ nào trước",
        "read_first_intro": (
            "Thứ tự đọc gợi ý giữa các dịch vụ — đọc điểm vào và các dịch vụ được "
            "phụ thuộc nhiều nhất trước, các thành phần tái sử dụng đọc sau cùng."
        ),
        "rationale_gateway": "Điểm vào — bắt đầu từ đây; {n} dịch vụ phụ thuộc vào nó.",
        "rationale_backend": "Dịch vụ backend — được {n} dịch vụ khác gọi tới.",
        "rationale_frontend": "Frontend / client — đọc sau các dịch vụ backend của nó.",
        "rationale_reused": "Thành phần tái sử dụng — đọc sau các dịch vụ sử dụng nó.",
        "read_first_intro_no_deps": (
            "Không phát hiện được phụ thuộc giữa các dịch vụ một cách tĩnh{stack_hint}. "
            "Các dịch vụ được liệt kê theo thứ tự bảng chữ cái — thứ tự đọc không có ý nghĩa đặc biệt."
        ),
    },
    "aggregate_why": {
        "overview": (
            "Đọc đầu tiên — xác định mục đích, phạm vi và các actor của hệ thống "
            "trước khi đi vào bất kỳ chi tiết cấu trúc nào."
        ),
        "component_catalog": (
            "Đọc sau tổng quan — liệt kê từng thành phần với vai trò và trách nhiệm, "
            "cung cấp từ vựng mà các tài liệu kiến trúc và sở hữu dữ liệu sẽ dùng."
        ),
        "architecture": (
            "Đọc sau danh mục — sơ đồ tầng và topology tham chiếu đến các thành phần "
            "đã được liệt kê; cần có ngữ cảnh để hiểu ranh giới dịch vụ và luồng dữ liệu."
        ),
        "data_ownership_map": (
            "Đọc sau kiến trúc — ánh xạ quyền sở hữu thực thể và các ứng viên tương quan "
            "giữa các dịch vụ mà ranh giới vừa được vẽ."
        ),
        "cross_service_flows": (
            "Đọc sau bản đồ sở hữu dữ liệu — các saga từ đầu đến cuối và chuỗi bàn giao "
            "trải rộng trên các dịch vụ và thực thể đã được giới thiệu trước."
        ),
        "glossary": (
            "Đọc sau các luồng — các thuật ngữ dùng chung và dễ nhầm lẫn giờ có đầy đủ "
            "ngữ cảnh hệ thống để phân biệt rõ ràng giữa các dịch vụ."
        ),
        "per_component_confidence": (
            "Đọc cuối cùng — điểm tin cậy và khoảng trống phủ sóng chỉ có nghĩa sau "
            "khi bạn đã biết các thành phần, vai trò của chúng và những gì đã được tác giả."
        ),
    },
    "artifact_descriptions": {
        "system_overview": "Mục tiêu sản phẩm, phạm vi, actor chính, bức tranh tổng thể — đọc đầu tiên",
        "architecture": "Sơ đồ tầng, tech stack, ranh giới service, luồng dữ liệu chính",
        "glossary": "Thuật ngữ nghiệp vụ dùng chung / dễ nhầm, định nghĩa một lần",
        "entities": "Thực thể dữ liệu cốt lõi, trường chính và quan hệ giữa chúng",
        "feature_list": "Danh mục tính năng F### đầy đủ, mỗi mục một dòng tóm tắt",
        "user_stories": "User story US### nhóm theo tính năng và actor",
        "screen_list": "Danh sách mọi màn hình SCR### trong sản phẩm",
        "screen_flow": "Màn hình nối với nhau ra sao — đường điều hướng và chuyển trạng thái",
        "route_list": "Mọi route API backend expose, kèm method và path",
        "api_map": "Bề mặt API nhóm theo resource, kèm background job",
        "api_contracts": "Hình dạng request/response cho endpoint REST/GraphQL/gRPC",
        "behavior_logic": "Đơn vị logic nền/async BL### và thứ kích hoạt chúng",
        "permissions_matrix": "Vai trò nào được làm hành động nào (ma trận RBAC)",
        "flows": "Luồng xử lý xuyên suốt nhiều tính năng",
        "features": "Đặc tả sâu từng tính năng — functional-spec + technical-spec mỗi tính năng (xem ghi chú dưới)",
        "screens": "Đặc tả chi tiết UI và hành vi từng màn hình",
        "traceability_matrix": "Mỗi F### một dòng, xâu chuỗi SCR###/US###/BL###/ROUTE###/PERM### (+TC###) — mạch truy vết đầu-cuối của tính năng",
    },
    # Crosswalk W5 (phase-01, 27.11.0) — nhóm lại CÙNG các tài liệu ở trên theo hướng BA/QA
    # ("bạn đang có câu hỏi loại gì" — thứ tự waterfall: Yêu cầu -> Thiết kế ngoài -> Thiết kế
    # trong -> Đặc tả kiểm thử) thay vì theo thứ tự đọc. Render dưới dạng '## Document Map'
    # trong CÙNG vùng sinh tự động.
    "document_map": {
        "heading": "Bản đồ tài liệu",
        "intro": (
            "Mọi tài liệu được sinh ra, nhóm theo đúng cách một bộ tài liệu chuẩn được nhóm — "
            "định hướng theo câu hỏi bạn đang có, không theo tên file."
        ),
        "buckets": {
            "requirements": {"label": "Yêu cầu", "who": "Người đọc: BA / QA."},
            "external_design": {
                "label": "Thiết kế ngoài",
                "who": "Người đọc: BA / QA / Dev — hệ thống trông ra sao và kết nối thế nào từ bên ngoài.",
            },
            "internal_design": {
                "label": "Thiết kế trong",
                "who": "Người đọc: Dev / SA — hệ thống được xây dựng bên trong ra sao.",
            },
            "test_spec": {"label": "Đặc tả kiểm thử", "who": "Người đọc: QA."},
        },
        "entries": {
            "functional_spec": "Mỗi tính năng phải làm gì, và vì sao? (user story US###, theo từng tính năng)",
            "screen_list": "Sản phẩm có những màn hình nào?",
            "screen_flow": "Các màn hình nối với nhau ra sao?",
            "entities": "Có những thực thể dữ liệu nào và quan hệ ra sao? (ER)",
            "api_map": "Backend expose bề mặt API nào?",
            "feature_list": "Sản phẩm gồm những tính năng nào?",
            "architecture": "Hệ thống được cấu trúc theo từng tầng ra sao?",
            "technical_spec": "Mỗi tính năng được triển khai ra sao? (theo từng tính năng)",
            "behavior_logic": "Logic nền/nghiệp vụ nào chạy, và khi nào?",
            "crud_matrix": "Tính năng nào đọc/ghi bảng nào?",
            "api_contracts": "Hình dạng request/response chính xác là gì?",
            "test_cases": "Mỗi tính năng được kiểm thử ra sao? (test case TC###, theo từng tính năng)",
        },
        "trace_pointer": (
            "**Muốn lần theo một tính năng từ đầu đến cuối?** Xem [{link}]({link}) — mỗi dòng "
            "một F###, nối màn hình, story, quy tắc, route, phân quyền và test case."
        ),
    },
    # Chrome giao diện cho bundle client `--package` (plan
    # `260826-1601-package-reading-layers-index-pager`, phase-03b). Xem
    # _nav_strings_en cho hợp đồng key.
    "package_ui": {
        "start_here": "Bắt đầu tại đây",
        "appendix": "Phụ lục — Tài liệu trong kho mã",
        "drill_labels": {
            "flows": "Luồng",
            "features": "Tính năng",
            "screens": "Màn hình",
            "traceability_matrix": "Truy vết",
        },
        "pager": {
            "prev": "‹ Trước",
            "next": "Tiếp ›",
            "reading": "Đang đọc",
            "back_to_index": "về mục lục",
            "end_of_spine": "Đã hết thứ tự đọc",
        },
        # Chrome for the `--package` click-to-zoom diagram viewer
        # (assets/package-zoom.js, plan `260827-0811-package-html-diagram-zoom`).
        # Read CLIENT-side from a JSON island the page emits, not by any Node
        # renderer. Consumers treat this block as OPTIONAL — `isUsableUi()` in
        # reading-spine.cjs deliberately does NOT require it, so a sidecar written
        # before this existed still validates instead of silently dropping its
        # whole corpus to the no-sidecar fallback.
        "zoom": {
            "title": "Trình xem sơ đồ",
            "open": "Mở sơ đồ này ở chế độ phóng to",
            "close": "Đóng",
            "zoom_in": "Phóng to",
            "zoom_out": "Thu nhỏ",
            "fit": "Vừa màn hình",
            "actual_size": "Kích thước thật",
            "hint": "Cuộn để phóng · kéo để di chuyển · Esc để đóng",
        },
    },
}
