<!-- layout-exempt: rebuild-spec owns all docs/system|features|generated|flows paths — all references here are output targets or internal definitions -->
# Glossary

Thuật ngữ nghiệp vụ thực tế xuất hiện trong copy và code của ứng dụng SAA 2025 — không suy diễn
thêm thuật ngữ nào ngoài những gì đọc được ở dictionary (`lib/i18n/messages/`), `lib/awards.ts`,
và các feature spec đã promote.

| Term | Definition | Used In |
|------|------------|---------|
| SAA / SAA 2025 | Viết tắt của "Sun* Annual Awards 2025" — lễ trao giải thường niên nội bộ của Sun*, chủ đề mùa này là "Root Further". | [F002_HomepageSaa/functional-spec.md](../../docs/features/F002_HomepageSaa/functional-spec.md) |
| Sunner | Cách gọi người thuộc tổ chức Sun* (nhân sự Sun*) trong copy sản phẩm — ví dụ "mọi Sunner đều là problem-solver". | `lib/i18n/messages/vi.ts`, `lib/i18n/messages/en-home.ts:26` |
| Root Further | Chủ đề chính thức của SAA 2025 — ẩn dụ về việc "cắm rễ sâu hơn" để phát triển năng lực trong kỷ nguyên AI. Hiển thị thành một khối nội dung riêng trên trang chủ, tách đoạn văn quanh một pull-quote cố định. | `app/_components/root-further-block.tsx:20-21`, [F002_HomepageSaa/functional-spec.md § FR-203](../../docs/features/F002_HomepageSaa/functional-spec.md) |
| Sun* Kudos | Hoạt động ghi nhận/cảm ơn đồng nghiệp, lần đầu triển khai cho mọi Sunner (dự kiến tháng 11/2025) — nội dung Sunner gửi trên hệ thống do BTC công bố là chất liệu để Hội đồng Heads tham khảo khi chọn người đạt giải. Trang chủ chỉ có khối quảng bá + liên kết `/kudos` (placeholder), chưa có nội dung Kudos thật. | `lib/i18n/messages/vi-home.ts:69-78`, `app/_components/kudos-promo.tsx`, [F002_HomepageSaa/functional-spec.md § FR-205](../../docs/features/F002_HomepageSaa/functional-spec.md) |
| Hệ thống giải thưởng (Award system) | 6 hạng mục giải thưởng cố định của SAA 2025, hiển thị dạng lưới thẻ trên trang chủ, mỗi thẻ dẫn tới `/awards-information#<slug>`. | `lib/awards.ts:27-42`, [F002_HomepageSaa/functional-spec.md § FR-204](../../docs/features/F002_HomepageSaa/functional-spec.md) |
| Top Talent | Một trong 6 hạng mục giải thưởng (slug `top-talent`). | `lib/awards.ts:28` |
| Top Project | Một trong 6 hạng mục giải thưởng (slug `top-project`). | `lib/awards.ts:29` |
| Top Project Leader | Một trong 6 hạng mục giải thưởng (slug `top-project-leader`). | `lib/awards.ts:30-34` |
| Best Manager | Một trong 6 hạng mục giải thưởng (slug `best-manager`). | `lib/awards.ts:35` |
| Signature 2025 - Creator | Một trong 6 hạng mục giải thưởng (slug `signature-2025-creator`). | `lib/awards.ts:36-40` |
| MVP (Most Valuable Person) | Một trong 6 hạng mục giải thưởng (slug `mvp`). | `lib/awards.ts:41` |
| Locale | Ngôn ngữ hiển thị của giao diện — hai giá trị `vi` (mặc định, xem là ngôn ngữ gốc/authoritative) và `en`. Lưu ở cookie `NEXT_LOCALE`, đọc lại ở mỗi Server Component qua `_page-context.ts`, không có URL segment hay thư viện i18n đứng sau. | `lib/i18n/locales.ts:10-14`, [architecture.md](architecture.md) |
| Session | Trạng thái đăng nhập Supabase (GoTrue) của một trình duyệt — được refresh trên mọi request bởi `proxy.ts`, xác định qua sự tồn tại (không null) của `user`. Không phải một khái niệm nghiệp vụ riêng của app — mượn nguyên khái niệm session của Supabase Auth. | `lib/supabase/update-session.ts`, [permissions.md](permissions.md) |
| Admin (role) | Giá trị `"admin"` của trường `user.app_metadata.role`, đọc để quyết định có hiện mục "Admin Dashboard" trong menu tài khoản hay không. Không được ghi bởi bất kỳ code nào trong repo — cấp phát ngoài băng trong Supabase. **Không phải một ranh giới phân quyền** — xem [permissions.md](permissions.md). | `app/_page-context.ts:40`, `app/_components/account-menu.tsx:99-107` |
| Coming Soon (placeholder) | Shell dùng chung cho 5 route chưa có nội dung thật (`/awards-information`, `/kudos`, `/standards`, `/profile`, `/admin`) — có header/footer thật, chỉ phần thân là thông báo "sắp ra mắt". | `app/_components/coming-soon.tsx` |
