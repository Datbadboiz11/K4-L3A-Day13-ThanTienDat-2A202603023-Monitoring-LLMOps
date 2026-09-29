# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Thân Tiến Đạt
- **MSSV:** 2A202603023
- **Lớp:** K4-L3A
- **Repository URL:** https://github.com/Datbadboiz11/K4-L3A-Day13-ThanTienDat-2A202603023-Monitoring-LLMOps
- **Commit SHA cuối:** HEAD
- **Challenge ID:** day13-k4-l3a-monitoring-llmops-v1
- **Tên project Langfuse cá nhân:** `day13-k4-l3a-2A202603023`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.png` |
| Log validator | `evidence/02-log-validator.png` |
| Dashboard validator | `evidence/03-dashboard-validator.png` |
| Structured log | `evidence/04-structured-log.png` |
| PII redaction | `evidence/05-pii-redaction.png` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata | `evidence/08-trace-metadata.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt rollback | `evidence/10-prompt-rollback.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.png` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.png` |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 20/100 | 100/100 | Đạt tuyệt đối: đủ schema, correlation_id propagation, enrichment và 0 PII leak |
| `validate_dashboard.py` | 6/6 | 6/6 | Hợp lệ toàn bộ 6 panel theo đúng contract `config/dashboard.yaml` |
| `pytest` | 22 passed | 24 passed | 100% test case passed, đã bổ sung test CCCD và Credit Card |
| Số traces hợp lệ | 0 | 35+ traces | Đầy đủ root, retrieval và generation trên Langfuse project cá nhân |
| Số PII leak | Còn rò rỉ | 0 leak | Scrubber làm sạch toàn bộ email, SĐT VN, CCCD 12 số, thẻ tín dụng trước khi ghi |
| Latency P95 / TTFT P95 | 156.0 ms / 50.0 ms | 731.5 ms / 50.0 ms | Hoạt động bình thường dưới ngưỡng SLO 3000ms; khi incident tăng lên 3693.8ms |
| Retrieval success rate | 100% | 100% | Toàn bộ truy vấn retrieval thành công ở chế độ hoạt động bình thường |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:**
  Triển khai trong `CorrelationIdMiddleware` ([app/middleware.py](file:///d:/AI%20th%E1%BB%B1c%20chi%E1%BA%BFn%20K4/K4-L3A-Day13-ThanTienDat-2A202603023-Monitoring-LLMOps/app/middleware.py)):
  1. Gọi `clear_contextvars()` ở đầu mỗi request để ngăn chặn triệt để hiện tượng rò rỉ context giữa các request đồng thời.
  2. Trích xuất `x-request-id` từ header nếu client truyền lên, nếu thiếu thì tự động sinh mới với định dạng `f"req-{uuid.uuid4().hex[:8]}"`.
  3. Bind correlation ID vào `structlog` contextvars qua `bind_contextvars(correlation_id=correlation_id)` và lưu vào `request.state.correlation_id`.
  4. Trả lại mã ID và thời gian thực thi cho client qua header response: `x-request-id` và `x-response-time-ms`.

- **Các metadata được ghi vào structured log:**
  Các trường bao gồm: `ts` (ISO format UTC), `level`, `service`, `event`, `correlation_id`, `user_id_hash` (băm SHA-256 an toàn), `session_id`, `feature`, `model`, `env`, `latency_ms`, `ttft_ms`, `tokens_in`, `tokens_out`, `cost_usd`, `quality_score`, `tool_name`, `tool_success`, và `payload` (chỉ chứa bản rút gọn an toàn `message_preview` / `answer_preview`).

- **Cách bảo đảm PII được scrub trước khi ghi:**
  Đăng ký processor `scrub_event` trong pipeline của `structlog` ([app/logging_config.py](file:///d:/AI%20th%E1%BB%B1c%20chi%E1%BA%BFn%20K4/K4-L3A-Day13-ThanTienDat-2A202603023-Monitoring-LLMOps/app/logging_config.py)) ngay TRƯỚC bước `JsonlFileProcessor` và `JSONRenderer`. Hàm `scrub_text` sử dụng regex nhận diện: email, số điện thoại Việt Nam (nhiều định dạng dấu cách/chấm/gạch nối), CCCD (12 chữ số) và thẻ thanh toán (16 số) để thay thế bằng thẻ `[REDACTED_<TYPE>]`. Dữ liệu nhạy cảm được che trước khi kịp ghi vào file hoặc console.

- **Cách kiểm chứng kết quả:**
  Chạy `python scripts/validate_logs.py` đạt điểm 100/100, xác nhận `Potential PII leaks detected: 0`. Chạy `pytest tests/test_pii.py` với 4 test case đều passed. Kiểm tra trực tiếp trong `data/logs.jsonl` không còn bất kỳ chuỗi PII thô nào.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:**
  Tạo project riêng tên `day13-k4-l3a-2A202603023` trên Langfuse Cloud, kết nối thông qua cặp API key cá nhân cấu hình trong `.env`. Giao diện Langfuse hiển thị rõ ràng tên project kèm mã sinh viên và user ID băm của tôi.

- **Cấu trúc root/retrieval/generation observations:**
  * **Root Observation:** `lab-agent-run` (type: `agent`) ghi nhận toàn bộ vòng đời request, tags (`lab`, `feature`, `model`) và metadata.
  * **Child Span 1:** `retrieval` (type: `retriever`) bọc hàm `retrieve(message)` đo thời gian tìm kiếm context trong RAG.
  * **Child Span 2:** `fake-llm-generate` (type: `generation`) bọc lệnh gọi `llm.generate()`, liên kết trực tiếp với managed prompt, đo thời gian TTFT, input/output tokens và chi phí `cost_details`.

- **Cách nối trace với log:**
  Trong `LabAgent.run`, truyền `correlation_id` từ `request.state` vào metadata của Trace thông qua `propagate_attributes(metadata={"correlation_id": correlation_id, ...})`. Khi mở một trace trên Langfuse, tab Attributes/Metadata hiển thị đúng mã `correlation_id` khớp từng ký tự với log trong `data/logs.jsonl`.

- **Prompt name:** `day13-chat`
- **Version/label baseline:** Version 2 (mang 2 labels: `baseline`, `production`)
- **Version/label candidate:** Version 3 (mang label: `candidate`, bổ sung chỉ dẫn trả lời ngắn gọn)
- **Trace ID của mỗi version:**
  * Baseline (v2, label `production`): `e7f0a10f037d969737b471189bc75968` (correlation_id: `req-318748eb`)
  * Candidate / Challenge: `097f0812d7402179099390e45037acb9` (correlation_id: `req-b2cc6dd5`)
- **Cách promote và rollback `production`:**
  * **Promote:** Gán label `production` cho Version 3 (candidate) trên Langfuse Cloud. Hệ thống tự động chuyển traffic sang dùng prompt v3.
  * **Rollback:** Khi cần quay lại bản ổn định, gán lại label `production` về Version 2 (baseline). Ứng dụng tự động fetch lại prompt v2 mà không cần restart server hay deploy lại mã nguồn.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:**
  Được xây dựng bằng Streamlit ([scripts/dashboard.py](file:///d:/AI%20th%E1%BB%B1c%20chi%E1%BA%BFn%20K4/K4-L3A-Day13-ThanTienDat-2A202603023-Monitoring-LLMOps/scripts/dashboard.py)) đọc trực tiếp nguồn dữ liệu chuẩn `data/logs.jsonl`:
  1. *Latency & TTFT:* P50, P95, P99 và TTFT P95 kèm biểu đồ đường (ms), threshold P95 <= 3000ms.
  2. *Request Traffic:* Tổng số request và tốc độ trung bình (req/phút) kèm biểu đồ cột.
  3. *Errors & Retrieval Success:* Tỷ lệ lỗi (%), số request fail, và tỷ lệ retrieval thành công (%).
  4. *Cost over time:* Tổng chi phí tích lũy ($) và chi phí trung bình/request kèm biểu đồ vùng, threshold <= $2.50.
  5. *Tokens:* Tổng số tokens input, tokens output và tổng cộng kèm bar chart.
  6. *Quality proxy:* Điểm chất lượng trung bình (thang điểm 0–1), threshold >= 0.75.

- **SLO và lý do chọn:**
  SLO chính trong [config/slo.yaml](file:///d:/AI%20th%E1%BB%B1c%20chi%E1%BA%BFn%20K4/K4-L3A-Day13-ThanTienDat-2A202603023-Monitoring-LLMOps/config/slo.yaml): 99.5% requests thành công có latency <= 3000ms trong chu kỳ 28 ngày.
  *Lý do:* Hệ thống AI Chat yêu cầu phản hồi nhanh dưới 3 giây để đảm bảo trải nghiệm người dùng không bị đứt đoạn, mức 99.5% là tiêu chuẩn cao trong ngành LLMOps vừa đảm bảo chất lượng vừa cho phép ngân sách lỗi hợp lý.

- **Cách tính error budget:**
  Error budget = 100% - Target SLO = 100% - 99.5% = 0.5%.
  Nghĩa là trong 10,000 requests, hệ thống cho phép tối đa 50 requests bị vi phạm (chậm > 3000ms hoặc ném lỗi).

- **Ba alert và runbook tương ứng:**
  Cấu hình trong [config/alert_rules.yaml](file:///d:/AI%20th%E1%BB%B1c%20chi%E1%BA%BFn%20K4/K4-L3A-Day13-ThanTienDat-2A202603023-Monitoring-LLMOps/config/alert_rules.yaml) và chi tiết tại [docs/alerts.md](file:///d:/AI%20th%E1%BB%B1c%20chi%E1%BA%BFn%20K4/K4-L3A-Day13-ThanTienDat-2A202603023-Monitoring-LLMOps/docs/alerts.md):
  1. `high_latency_p95` (Critical): P95 latency > 3000ms duy trì 5m $\rightarrow$ Bật cache, kiểm tra span retrieval/generation, giảm tải.
  2. `high_error_rate` (Critical): Error rate > 2% duy trì 5m $\rightarrow$ Kiểm tra error_type, khởi động lại vector store hoặc chuyển sang fallback.
  3. `low_quality_score` (Warning): Điểm chất lượng < 0.75 duy trì 10m $\rightarrow$ Kiểm tra prompt version mới và rollback về baseline.

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1`
- **Khoảng thời gian điều tra:** 2026-09-29 16:15:00 — 16:22:00 (Timestamp log: `09:17:33 UTC`)
- **Triệu chứng từ metrics:**
  Dashboard Panel 1 chuyển sang cảnh báo đỏ `🚨 ALERT (P95 > 3000ms)`. P50 latency vọt lên 2653.0ms, P95 latency đạt 3693.8ms, P99 latency đạt 3896.4ms, vượt xa ngưỡng threshold 2000ms quy định trong challenge.
- **Log line và correlation ID liên quan:**
  Mã `correlation_id`: **`req-b2cc6dd5`** (cùng nhóm `req-ba200ed4`, `req-17c7177c`, `req-7c97c45b`, `req-ff94f4e7`).
  Log line: `{"event": "response_sent", "feature": "monitoring", "latency_ms": 2653, "correlation_id": "req-b2cc6dd5", "session_id": "k4-l3a-challenge-s04", "ts": "2026-09-29T09:17:33.036936Z"}`.
- **Trace ID và span gây ảnh hưởng:**
  Trace ID: **`097f0812d7402179099390e45037acb9`**.
  Span gây nghẽn: **`retrieval` chiếm trọn 2.50s** trong tổng thời gian 2.65s của request (trong khi span `fake-llm-generate` chỉ mất 0.15s).
- **Root cause:**
  Quá trình truy vấn tài liệu trong vector store (`retrieval`) bị nghẽn (mô phỏng độ trễ 2.5 giây do sự cố `rag_slow` tại tầng cơ sở dữ liệu vector/RAG khi xử lý feature `monitoring`).
- **Fix action:**
  Tắt sự cố `rag_slow` qua API control (`python scripts/inject_incident.py --disable`), tối ưu hóa chỉ mục vector HNSW, thêm cache kết quả tìm kiếm cho các câu hỏi phổ biến, và scale thêm replica cho vector store.
- **Preventive measure:**
  Thiết lập timeout 1.5s và circuit breaker cho bước retrieval: nếu vector store không phản hồi trong 1.5s thì tự động chuyển sang fallback document tĩnh để bảo vệ latency P95 cho người dùng; đồng thời cấu hình alert cảnh báo sớm khi retrieval span latency > 1000ms.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:**
  Quyết định tách rời việc làm sạch PII (`scrub_event`) thành một processor riêng biệt nằm trước `JsonlFileProcessor` và `JSONRenderer`. Lý do: Điều này đảm bảo tính "bảo mật theo thiết kế" (Secure by Design), dữ liệu nhạy cảm bị che triệt để trước khi chạm vào ổ cứng hoặc in ra console, không phụ thuộc vào việc từng lập trình viên có nhớ tự scrub trong handler hay không.

- **Một lỗi/blocker đã gặp:**
  Khi chạy `validate_logs.py`, validator đọc toàn bộ lịch sử file `data/logs.jsonl`. Ban đầu các dòng log từ trước khi áp dụng scrubber ở CP0 vẫn còn tồn tại trong file khiến validator phát hiện PII leak cũ và trừ điểm.

- **Cách tìm nguyên nhân và xử lý:**
  Đọc mã nguồn `scripts/validate_logs.py` để hiểu cơ chế kiểm tra; sau đó thực hiện xóa sạch file log cũ `Remove-Item data/logs.jsonl` rồi chạy lại workload `load_test.py` trên mã nguồn đã có scrubber hoàn chỉnh, giúp đạt điểm tối đa 100/100.

- **Cách hiểu luồng Metrics → Logs → Traces:**
  * **Metrics** là tầng phát hiện đầu tiên: phát hiện triệu chứng diện rộng và khoanh vùng mốc thời gian (ví dụ: P95 latency vọt lên 3.6s lúc 16:17).
  * **Logs** là tầng định vị chi tiết: dùng khoảng thời gian và feature từ metrics để lọc ra request cụ thể trong log JSON và lấy mã `correlation_id`.
  * **Traces** là tầng giải phẫu nguyên nhân: dùng `correlation_id` mở cây Waterfall trên Langfuse để xem chính xác span con nào bên trong request đó bị nghẽn hoặc ném exception (`retrieval` 2.5s).

- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
  * *Prompt version & Rollback:* Giúp quản trị phiên bản và thử nghiệm prompt an toàn, có thể rollback tức thì về bản ổn định mà không cần deploy lại mã nguồn khi prompt mới làm giảm chất lượng hoặc tăng token.
  * *Token & Cost monitoring:* Giúp kiểm soát ngân sách vận hành, phát hiện kịp thời các tình trạng prompt injection hoặc vòng lặp làm bùng nổ token/chi phí.
  * *SLO:* Là cam kết chất lượng dịch vụ với người dùng, đồng thời là cơ sở để đội ngũ kỹ thuật ra quyết định khi nào được phép release tính năng mới và khi nào phải ưu tiên khắc phục độ ổn định.

- **Điều quan trọng nhất đã học:**
  Kỹ năng xây dựng hệ thống Full Observability cho ứng dụng AI/LLM, hiểu sâu sắc mối liên kết chặt chẽ giữa Structured Logging, Correlation Propagation và Distributed Tracing trong việc điều tra sự cố thực tế.

- **Hạn chế hoặc phần chưa hoàn thành, nếu có:**
  Hiện tại hệ thống sử dụng FakeLLM và Mock RAG giả lập; trong môi trường sản phẩm thực tế cần tích hợp thêm các công cụ LLM Evaluation tự động (LLM-as-a-judge) để đánh giá độ chính xác ngữ nghĩa và độ ảo giác (hallucination) thay cho heuristic quality score.

## 9. Checklist trước khi nộp

- [x] Kết quả và evidence thuộc commit SHA cuối.
- [x] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [x] Incident evidence nối đúng metric → log → trace.
- [x] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [x] Repository chạy lại được theo README.
- [x] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [x] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
