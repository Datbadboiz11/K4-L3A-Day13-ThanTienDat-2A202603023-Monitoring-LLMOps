# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1

- Tên: HighLatencyP95
- Severity: critical
- Duration: 5m
- Kênh thông báo: Slack (#llmops-alerts)
- SLI/SLO liên quan: fast_successful_requests (SLO: latency <= 3000ms cho 99.5% requests)
- Điều kiện và thời gian duy trì: Latency P95 > 3000ms liên tục trong 5 phút.
- Ảnh hưởng tới người dùng: Người dùng nhận phản hồi rất chậm, có nguy cơ timeout trên client.
- Ba bước kiểm tra đầu tiên:
  1. Mở Dashboard kiểm tra panel Latency và TTFT xem độ trễ tăng đột biến từ lúc nào.
  2. Lọc file `data/logs.jsonl` tìm correlation_id các request có `latency_ms > 3000`.
  3. Mở Langfuse trace tương ứng kiểm tra span con: nghẽn ở `retrieval` (vector store) hay `fake-llm-generate`.
- Mitigation tạm thời: Giảm tải hệ thống, scale tài nguyên hoặc kích hoạt cache cho truy vấn phổ biến.
- Owner: oncall-llmops

## Alert 2

- Tên: HighErrorRate
- Severity: critical
- Duration: 5m
- Kênh thông báo: Slack (#llmops-alerts)
- SLI/SLO liên quan: Error rate guardrail (< 2%), Retrieval success rate (> 90%)
- Điều kiện và thời gian duy trì: Tỷ lệ lỗi 5xx hoặc failure rate > 2% liên tục trong 5 phút.
- Ảnh hưởng tới người dùng: Người dùng bị gián đoạn, nhận lỗi hệ thống 500 hoặc không nhận được kết quả trả lời.
- Ba bước kiểm tra đầu tiên:
  1. Kiểm tra Dashboard panel Errors để xem loại lỗi `error_type` và tỷ lệ `tool_success_rate_pct`.
  2. Lọc các sự kiện `request_failed` trong `data/logs.jsonl` để trích xuất `correlation_id` và message lỗi.
  3. Mở Trace trên Langfuse để xác định span bị ném exception (thường là timeout hoặc exception ở retrieval).
- Mitigation tạm thời: Chuyển hướng sang fallback document cố định, tạm ngắt tool bị lỗi hoặc restart vector service.
- Owner: oncall-llmops

## Alert 3

- Tên: LowQualityScore
- Severity: warning
- Duration: 10m
- Kênh thông báo: Slack (#llmops-alerts)
- SLI/SLO liên quan: Quality proxy guardrail (mean quality score >= 0.75)
- Điều kiện và thời gian duy trì: Điểm chất lượng trung bình `quality_score` < 0.75 duy trì liên tục trong 10 phút.
- Ảnh hưởng tới người dùng: Câu trả lời bị giảm chất lượng, thông tin cụt lủn hoặc không đúng trọng tâm câu hỏi.
- Ba bước kiểm tra đầu tiên:
  1. Kiểm tra Dashboard panel Quality xem xu hướng suy giảm điểm số bắt đầu từ thời điểm nào.
  2. Lọc các bản ghi `response_sent` có `quality_score < 0.75` trong `data/logs.jsonl` và xem payload preview.
  3. Kiểm tra Trace trên Langfuse xem có phiên bản prompt mới (candidate) được áp dụng gần đây không.
- Mitigation tạm thời: Rollback label `production` về phiên bản prompt baseline trước đó trên Langfuse.
- Owner: model-evaluation-team
