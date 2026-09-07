# Quy chuẩn thiết lập CloudWatch Alarm (Sun*)

## Lưu ý
- Bật Detailed Monitoring cho một số resource như EC2, RDS ...
- Mỗi môi trường (dev/stag/prod) nên gửi cảnh báo vào một channel/group riêng
- Nếu gửi cảnh báo vào các ứng dụng chat (Slack/Telegram/Teams…) nên cấu hình gửi All trong channel/group
- Tùy từng hệ thống điều chỉnh threshold và datapoint cho phù hợp

## Danh sách Alarm Standards

| No. | Service | Metric | Threshold | Period | DataPoint | Note |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | EC2 Instance | MemoryUtilization | Average > 80% | 1' | 2 out of 2 |  |
| 2 | EC2 Instance | StatusCheckFailed | Average > 0 | 1' | 1 out of 1 |  |
| 3 | EC2 Instance | DiskSpaceUtilization | Average > 70% | 1' | 1 out of 1 |  |
| 4 | EC2 Instance | CPUUtilization | Average > 70% | 1' | 2 out of 2 |  |
| 5 | ECS Service | MemoryUtilization | Average > 80% | 1' | 2 out of 2 |  |
| 6 | ECS Service | CPUUtilization | Average > 70% | 1' | 2 out of 2 |  |
| 7 | ALB | HTTPCode_ELB_4XX_Count | Sum > 1000 | 1' | 2 out of 2 | Nếu kiểm tra thấy không phải lỗi và không ảnh hưởng lớn hiệu năng hệ thống thì tăng dần mức cảnh báo. Nếu ảnh hưởng thì fix bug hoặc block IP |
| 8 | ALB | HTTPCode_ELB_5XX_Count | Sum > 0 | 1' | 1 out of 1 |  |
| 9 | ALB | HTTPCode_Target_5XX_Count | Sum > 0 | 1' | 1 out of 1 |  |
| 10 | ALB | TargetResponseTime | Average > 5s | 1' | 2 out of 2 | Phụ thuộc non-functional, nếu không có thì phụ thuộc functional hệ thống |
| 11 | ALB | RequestCount | Sum > 2000 | 1' | 1 out of 1 | Tăng dần cho đến khi xuất hiện cảnh báo về High Memory, High CPU trong hệ thống thì dừng |
| 12 | ALB | UnHealthyHostCount | Maximum > 0 | 1' | 1 out of 1 |  |
| 13 | Redis | EngineCPUUtilization | Average > 70% | 1' | 2 out of 2 |  |
| 14 | Redis | CPUUtilization | Average > 70% | 1' | 2 out of 2 |  |
| 15 | Redis | DatabaseMemoryUsagePercentage | Average > 70% | 1' | 1 out of 1 |  |
| 16 | Redis | CurrConnections | Maximum > 1000 | 1' | 1 out of 1 | Tăng dần cho đến khi xuất hiện cảnh báo về High Memory, High CPU trong hệ thống thì dừng. AWS limit connect 65k |
| 17 | Redis | Evictions | Sum > 2 | 1' | 1 out of 1 |  |
| 18 | Redis | ReplicationLag | Maximum > 1000 ms | 1' | 2 out of 2 |  |
| 19 | Redis | FreeableMemory | Average < 20% | 1' | 2 out of 2 |  |
| 20 | RDS | CPUUtilization | Average > 70% | 1' | 2 out of 2 |  |
| 21 | RDS | FreeableMemory | Average < 20% | 1' | 2 out of 2 |  |
| 22 | RDS | DatabaseConnections | Maximum > 60% of Max | 1' | 1 out of 1 | Từng spec sẽ có số limit default tương ứng |
| 23 | RDS | ReadIOPS | Average > 60% of Max | 1' | 2 out of 2 |  |
| 24 | RDS | WriteIOPS | Average > 60% of Max | 1' | 2 out of 2 |  |
| 25 | RDS | DiskQueueDepth | Average > 2 | 1' | 2 out of 2 |  |
| 26 | RDS | FreeStorageSpace | Average < 20% | 1' | 1 out of 1 |  |
| 27 | RDS | ReplicaLag | Average > 1000 ms | 1' | 2 out of 2 |  |
| 28 | Aurora | CPUUtilization | Average > 70% | 1' | 2 out of 2 |  |
| 29 | Aurora | FreeableMemory | Average < 20% | 1' | 2 out of 2 |  |
| 30 | Aurora | DatabaseConnections | Maximum > 60% of Max | 1' | 1 out of 1 | Từng spec sẽ có số limit default tương ứng |
| 31 | Aurora | ReadIOPS | Average > 1000 | 1' | 2 out of 2 |  |
| 32 | Aurora | WriteIOPS | Average > 1000 | 1' | 2 out of 2 |  |
| 33 | Aurora | DiskQueueDepth | Average > 2 | 1' | 2 out of 2 |  |
| 34 | Aurora | AuroraReplicaLag | Average > 1000 ms | 1' | 2 out of 2 |  |
| 35 | OpenSearch | CPUUtilization | Average > 70% | 5' | 2 out of 2 |  |
| 36 | OpenSearch | FreeStorageSpace | Average < 25% | 1' | 1 out of 1 |  |
| 37 | OpenSearch | ClusterStatus.yellow | Average >= 1 | 1' | 1 out of 1 |  |
| 38 | OpenSearch | ClusterStatus.red | Average >= 1 | 1' | 1 out of 1 |  |
| 39 | OpenSearch | ClusterIndexWritesBlocked | Sum >= 1 | 1' | 1 out of 1 |  |
| 40 | OpenSearch | Nodes | Average < x | 1' | 1 out of 1 | x là số node data + node master trong cluster |
| 41 | OpenSearch | AutomatedSnapshotFailure | Maximum >= 1 | 1' | 1 out of 1 |  |
| 42 | OpenSearch | JVMMemoryPressure | Maximum >= 95% | 1' | 3 out of 3 |  |
| 43 | OpenSearch | OldGenJVMMemoryPressure | Maximum >= 80% | 1' | 3 out of 3 |  |
| 44 | OpenSearch | MasterCPUUtilization | Maximum >= 50% | 5' | 3 out of 3 |  |
| 45 | OpenSearch | MasterJVMMemoryPressure | Maximum >= 95% | 1' | 3 out of 3 |  |
| 46 | OpenSearch | 5xx | Sum >= 1 | 1' | 1 out of 1 |  |
| 47 | OpenSearch | ThreadpoolWriteQueue | Average >= 100 | 1' | 1 out of 1 |  |
| 48 | OpenSearch | ThreadpoolSearchQueue | Average >= 500 | 1' | 1 out of 1 |  |
| 49 | OpenSearch | ThreadpoolSearchQueue | Maximum >= 5000 | 1' | 1 out of 1 |  |
| 50 | OpenSearch | ThreadpoolSearchRejected | Maximum >= 1 | 1' | 1 out of 1 | Giá trị này sẽ liên tục tăng, chỉ reset về 0 khi OpenSearch restart => Sau mỗi lần alert thì tăng giá trị lên cho phù hợp |
| 51 | OpenSearch | ThreadpoolWriteRejected | Maximum >= 1 | 1' | 1 out of 1 | Giá trị này sẽ liên tục tăng, chỉ reset về 0 khi OpenSearch restart => Sau mỗi lần alert thì tăng giá trị lên cho phù hợp |
| 52 | SES | Bounce rate | Average >= 0.02 | 1' | 1 out of 1 |  |
| 53 | SES | Complaint rate | Average >= 0.0005 | 1' | 1 out of 1 |  |
| 54 | WAF | BlockedRequests | Sum > 10 | 1' | 2 out of 2 |  |
| 55 | Budget | - | Actual cost is greater than 80% / 100% / 105% | N/A | N/A | Budget alerts không sử dụng Period/DataPoint như CloudWatch Alarm; ngưỡng được cấu hình trực tiếp trong AWS Budgets. |
| 56 | Amplify | 4xxErrors | Sum > 1000 | 1' | 1 out of 1 | Nếu kiểm tra thấy không phải lỗi và không ảnh hưởng lớn hiệu năng hệ thống thì tăng dần mức cảnh báo. Nếu ảnh hưởng thì fix bug hoặc block IP |
| 57 | Amplify | 5xxErrors | Sum > 0 | 1' | 1 out of 1 |  |
| 58 | Amplify | Latency | Average > 5s | 1' | 2 out of 2 | Phụ thuộc non-functional, nếu không có thì phụ thuộc functional hệ thống |
| 59 | Lambda | Errors | Sum > 1 | 1' | 1 out of 1 | Nếu hệ thống sử dụng lambda chỉ cho việc gửi cảnh báo thì có thể không cần monitor metric này |
| 60 | CloudFront | 5xxErrorRate | Average > 5% | 1' | 2 out of 2 |  |
| 61 | API Gateway | 5XXError | Sum > 0 | 1' | 2 out of 2 |  |
| 62 | API Gateway | Count | Sum > 2000 | 1' | 1 out of 1 | Tăng dần cho đến khi xuất hiện cảnh báo về High Memory, High CPU trong hệ thống thì dừng |
| 63 | API Gateway | Latency | Average > 5s | 1' | 2 out of 2 | Phụ thuộc non-functional, nếu không có thì phụ thuộc functional hệ thống |
