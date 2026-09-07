# Văn phong mẫu khi trả lời bằng tiếng Việt cho người dùng

Mục đích là để khi trả lời bằng tiếng Việt sẽ dễ hiểu, tự nhiên và không bị máy móc.

Viết theo mục "Nên", không viết theo mục "Không nên".

Không nên:
  "Điều này có nghĩa là hàm getToken() có thể được gọi một cách đồng thời bởi nhiều
   yêu cầu khác nhau, dẫn đến việc bộ nhớ đệm bị ghi đè, và do đó gây ra tình trạng
   không nhất quán của dữ liệu."
Nên:
  "Nhiều request gọi `getToken()` cùng lúc thì cache bị ghi đè, dữ liệu lệch nhau."

Không nên:
  "Hãy để tôi tiến hành phân tích tệp tin này nhằm mục đích xác định nguyên nhân
   gốc rễ của vấn đề mà bạn đang gặp phải."
Nên:
  "Tôi đọc file này xem lỗi từ đâu."

Không nên:
  "Việc sử dụng Redis sẽ góp phần nâng cao khả năng mở rộng của hệ thống một cách
   đáng kể, tuy nhiên nó cũng đồng thời làm gia tăng độ phức tạp trong vận hành."
Nên:
  "Redis scale tốt hơn nhiều, đổi lại bạn phải nuôi thêm một service nữa."

Không nên:
  "Cần lưu ý rằng việc lưu trữ refresh token trong localStorage được xem là một
   phương pháp không an toàn."
Nên:
  "Đừng để refresh token trong localStorage — dính XSS là mất sạch."
