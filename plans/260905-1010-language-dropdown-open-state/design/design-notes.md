# Design notes — Dropdown-ngôn ngữ (`hUyaaugye2` / figma `721:4942`)

## Node tree

```
721:4942  Dropdown-ngôn ngữ (FRAME)
└── 525:11713  mms_A_Dropdown-List (INSTANCE, componentSet 563:8216)
    ├── I525:11713;362:6085  mms_A.1_tiếng Việt   (componentId 186:1692)  ← SELECTED
    │   └── ...;186:1821 Button → ...;186:1937 Frame 485 (gap 4)
    │       ├── ...;186:1709 IC → "VN - Vietnam" flag
    │       └── ...;186:1439 TEXT "VN"
    └── I525:11713;362:6128  mms_A.2_tiếng Anh    (componentId 186:1694)  ← option
        └── ...;186:1903 Button → ...;186:1937 Content (gap 4)
            ├── ...;186:1709 IC → "GB-NIR" flag (Union Jack)
            └── ...;186:1439 TEXT "EN"
```

## Đo được (không suy đoán)

| Node | Thuộc tính | Giá trị |
|---|---|---|
| `525:11713` | background | `#00070C` (`--Details-Container-2`) |
| `525:11713` | border | `1px solid #998C5F` (`--Details-Border`) |
| `525:11713` | border-radius / padding | `8px` / `6px` |
| `525:11713` | box | `122 × 124` @ (47,90)→(169,214) |
| `I525:11713;362:6085` | box / radius | `108 × 56` / `2px` |
| `I525:11713;362:6085` | background | `rgba(255,234,158,0.2)` |
| `I525:11713;362:6128` | box / radius | `110 × 56` / `0` — nền trong suốt |
| `...;186:1937` | gap | `4px`, cờ 24px + nhãn |
| `...;186:1439` | font | Montserrat 700, 16px/24px, ls 0.15px, `#FFFFFF` |

Nội dung mục căn giữa: đo padding trái 27px / phải 28px (VN), 29/29 (EN).

## Quan sát quan trọng

1. **Hàng VN dùng CHUNG `componentId 186:1692` với nút trigger đóng** trên màn Login
   (`GzbNeVGJHz` node `I662:14391;186:1696`, cũng `108×56`). Design ngụ ý panel đè lên
   trigger. **User đã chọn thả xuống dưới thay vì đè** — xem clarifications.md.
2. Hàng trong panel KHÔNG có chevron (Frame 485 chỉ có IC + TEXT). Chevron chỉ thuộc trigger.
3. Design không vẽ trạng thái hover → token hover do user chốt.
4. Frame không có test case nào (`download_test_cases` trả về rỗng) → hợp đồng hành vi lấy
   từ `description` của spec item + clarifications.
