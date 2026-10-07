---
name: refund-policy
description: Xử lý, tra cứu chính sách và kiểm tra điều kiện hoàn tiền dựa trên ngày mua hàng của khách hàng. Sử dụng skill này khi người dùng hỏi về điều kiện hoàn tiền, mức phí, khả năng áp dụng hoặc xử lý yêu cầu hoàn tiền cho đơn hàng.
---

# Quy trình kiểm tra điều kiện hoàn tiền

## 1. Kiểm tra thông tin đầu vào
Trước khi đưa ra kết luận, kiểm tra xem người dùng đã cung cấp đủ 3 thông tin dưới đây chưa:
1. **Ngày mua hàng**
2. **Ngày yêu cầu hoàn tiền** (dùng ngày trong câu hỏi của người dùng, không dùng ngày hiện tại)
3. **Trạng thái kích hoạt sản phẩm** (Đã kích hoạt / Chưa kích hoạt)

⚠️ **LƯU Ý QUAN TRỌNG:** 
Nếu thiếu bất kỳ thông tin nào trong 3 thông tin trên (đặc biệt là trạng thái kích hoạt), **TẬP TRUNG HỎI LẠI NGƯỜI DÙNG ĐỂ BỔ SUNG**, tuyệt đối không tự giả định "chưa kích hoạt" hay đưa ra kết luận sơ bộ.

## 2. Tìm kiếm và chọn chính sách
1. Dùng tool `list_files` liệt kê tất cả các file trong thư mục `data/policies/`. KHÔNG dùng cố định tên file vì tên file có thể bị thay đổi.
2. Dùng tool `read_file` đọc nội dung các file chính sách tìm được để kiểm tra phạm vi hiệu lực theo ngày mua:
   - Ngày mua **trước 2026-10-01**: Áp dụng chính sách áp dụng cho ngày mua trước 2026-10-01.
   - Ngày mua **từ 2026-10-01 trở đi** (bao gồm cả ngày 2026-10-01): Áp dụng chính sách áp dụng cho ngày mua từ 2026-10-01.

## 3. Tính toán số ngày và kiểm tra điều kiện
- **Số ngày đã qua** = Ngày yêu cầu hoàn tiền - Ngày mua hàng (tính bằng chênh lệch ngày lịch).
- So sánh số ngày đã qua với giới hạn thời gian trong chính sách tương ứng (bằng đúng giới hạn vẫn đủ điều kiện).
- Đánh giá điều kiện kích hoạt.

## 4. Trả lời theo mẫu
Tham khảo cấu trúc trình bày chuẩn trong file `references/answer-template.md`.