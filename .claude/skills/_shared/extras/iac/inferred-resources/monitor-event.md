# Quy chuẩn thiết lập Monitor Event (Sun*)

## Lưu ý
- Với các dịch vụ không có event native, dùng EventBridge để ghi nhận và xử lý event
- Mỗi môi trường (dev/stag/prod) nên gửi cảnh báo vào một channel/group riêng
- Nếu gửi cảnh báo vào các ứng dụng chat (Slack/Telegram/Teams…) nên cấu hình gửi All trong channel/group

## Bảng quy chuẩn

| No. | Service | Event | Note |
| --- | --- | --- | --- |
| 1 | Auto Scaling Group | Fail to Launch | |
| 2 | Auto Scaling Group | Fail to Terminate | |
| 3 | ElastiCache Redis | Notification | Có thể xem xét việc không bắn khi có SnapshotComplete (Chỉ áp dụng khi dùng Lambda gửi thông báo) |
| 4 | RDS | All event categories | Có thể xem xét việc không bắn khi có SnapshotComplete (Chỉ áp dụng khi dùng Lambda gửi thông báo) |
| 5 | Aurora | All event categories | Có thể xem xét việc không bắn khi có SnapshotComplete (Chỉ áp dụng khi dùng Lambda gửi thông báo) |
| 6 | EventBridge Rules | health | |
| 7 | EventBridge Rules | OpenSearch | |
| 8 | EventBridge Rules | ECS Service | WARN, ERROR |
| 9 | EventBridge Rules | ECS Task | STOPPED |
| 10 | EventBridge Rules | ECS Deployment | Fail |
| 11 | EventBridge Rules | Amplify deployment | STARTED / SUCCEEDED / FAILED / CANCELED / SUPERSEDED |
| 12 | CodePipeline | SUCCEEDED / SUPERSEDED / STARTED / CANCELED / FAILED | |
