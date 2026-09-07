# Quy chuẩn thiết lập Monitor Log (Sun*)

## Lưu ý quan trọng

### THỐNG NHẤT VỚI DEV TEAM
Ngoài các log phía hạ tầng thì cần trao đổi với team Dev để có được danh sách các loại log phía Application cần được lưu trữ + các keyword cần giám sát trong log

### CHI PHÍ
- Một số log type có thể tốn nhiều chi phí khi đẩy lên CloudWatch (ví dụ: RDS General log, Audit log)
- Cân nhắc lưu trữ log ở S3 để tiết kiệm chi phí nếu không cần query thường xuyên
- Sử dụng Log Retention policies để tự động xóa log cũ

## Khuyến nghị chung
- **Recommend**: Bắt buộc phải thực hiện cho môi trường Production
- **Optional**: Tùy yêu cầu dự án và ngân sách
- Sử dụng CloudWatch Logs Subscription Filters kết hợp AWS Lambda để gửi alert khi phát hiện keyword nguy hiểm trong log
- Lưu trữ log lâu dài trên S3 với lifecycle policy để tối ưu chi phí

## Bảng quy chuẩn

| No. | Platform | Service | Priority | Solution |
| --- | --- | --- | --- | --- |
| 1 | AWS | ECS | Recommend | Đẩy stdout và stderr lên CloudWatch Log → Sử dụng Subscription filters tới Lambda để gửi alert |
| 2 | AWS | EC2 | Recommend | Đẩy system log, command log, application log lên CloudWatch Log → Sử dụng Subscription filters tới Lambda để gửi alert |
| 3 | AWS | RDS | Recommend | Đẩy Error và Slow query lên CloudWatch Log |
| 4 | AWS | RDS | Optional | Tùy yêu cầu của từng dự án thì xem xét đẩy General và Audit log lên CloudWatch Log (Lưu ý: có thể tốn nhiều chi phí) |
| 5 | AWS | ELB | Recommend | Đẩy Access log lên S3 lưu trữ |
| 6 | AWS | S3 | Recommend | Bật Access log và lưu log ở 1 bucket khác (không áp dụng với bucket chỉ lưu log) |
| 7 | AWS | CloudFront | Recommend | Đẩy Access log lên S3 lưu trữ |
| 8 | AWS | VPC | Optional | Đẩy Flow log lên S3 lưu trữ |
| 9 | AWS | WAF | Recommend | Đẩy log của WAF với rule action là Block lên CloudWatch Log |
| 10 | AWS | OpenSearch | Recommend | Đẩy Index slow, Search slow và Error lên CloudWatch Log |
| 11 | AWS | OpenSearch | Optional | Đẩy Audit log lên CloudWatch Log |
| 12 | AWS | CloudTrail | Recommend | Đẩy log lên S3 lưu trữ |
| 13 | AWS | Lambda | Recommend | Đẩy log lên CloudWatch Log |
| 14 | AWS | CodeBuild | Recommend | Đẩy log lên CloudWatch Log |
