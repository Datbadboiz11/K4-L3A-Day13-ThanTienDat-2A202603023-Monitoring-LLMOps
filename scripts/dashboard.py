from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="K4-L3A Day 13 Monitoring & LLMOps Dashboard",
    page_icon="📊",
    layout="wide",
)

LOG_PATH = Path("data/logs.jsonl")

st.title("📊 K4-L3A Day 13 Monitoring & LLMOps Dashboard")
st.caption("Time Range: Last 60 minutes | Source: data/logs.jsonl | Refresh Rate: 30s")

col_btn1, col_btn2 = st.columns([1, 8])
with col_btn1:
    if st.button("🔄 Refresh Data"):
        st.rerun()

# ----------------- Load & Parse Data -----------------
records = []
if LOG_PATH.exists():
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except Exception:
            continue

if not records:
    st.warning("Chưa tìm thấy log trong data/logs.jsonl. Hãy chạy load_test.py để sinh dữ liệu!")
    st.stop()

df_all = pd.DataFrame(records)
if "ts" in df_all.columns:
    df_all["dt"] = pd.to_datetime(df_all["ts"], errors="coerce")
    now_utc = datetime.now(timezone.utc)
    # Lọc trong khoảng 60 phút gần nhất (nếu log có timestamp cũ hơn thì vẫn giữ để hiển thị demo)
    cutoff = now_utc - timedelta(minutes=60)
    df_window = df_all[df_all["dt"] >= cutoff].copy()
    if df_window.empty:
        df_window = df_all.copy()
else:
    df_window = df_all.copy()

# Tách theo event
df_sent = df_window[df_window["event"] == "response_sent"].copy()
df_recv = df_window[df_window["event"] == "request_received"].copy()
df_fail = df_window[df_window["event"] == "request_failed"].copy()

# ================= PANEL 1: Latency & TTFT =================
# Threshold: p95 <= 3000 ms
st.divider()
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.subheader("1. Latency percentiles and TTFT")
    st.caption("Events: [response_sent] | Fields: latency_ms, ttft_ms | Unit: ms | Threshold: p95 <= 3000 ms")
    if not df_sent.empty and "latency_ms" in df_sent.columns:
        latencies = df_sent["latency_ms"].dropna().values
        ttfts = df_sent["ttft_ms"].dropna().values if "ttft_ms" in df_sent.columns else np.array([0])
        
        p50 = float(np.percentile(latencies, 50)) if len(latencies) else 0.0
        p95 = float(np.percentile(latencies, 95)) if len(latencies) else 0.0
        p99 = float(np.percentile(latencies, 99)) if len(latencies) else 0.0
        ttft_p95 = float(np.percentile(ttfts, 95)) if len(ttfts) else 0.0
        
        status = "✅ PASS" if p95 <= 3000 else "🚨 ALERT (P95 > 3000ms)"
        st.markdown(f"**Threshold Check:** `{status}` (P95: `{p95:.1f}ms` vs Threshold: `3000ms`)")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("P50 Latency", f"{p50:.1f} ms")
        m2.metric("P95 Latency", f"{p95:.1f} ms")
        m3.metric("P99 Latency", f"{p99:.1f} ms")
        m4.metric("TTFT P95", f"{ttft_p95:.1f} ms")
        
        if "dt" in df_sent.columns:
            chart_df = df_sent.sort_values("dt")[["dt", "latency_ms"]].set_index("dt")
            st.line_chart(chart_df, height=180)
    else:
        st.info("Chưa có sự kiện response_sent")

# ================= PANEL 2: Traffic =================
# Threshold: rate_per_minute >= 1 requests_per_minute
with row1_col2:
    st.subheader("2. Request traffic")
    st.caption("Events: [request_received] | Unit: requests_per_minute | Threshold: rate >= 1 req/min")
    total_recv = len(df_recv)
    if total_recv > 0 and "dt" in df_recv.columns:
        # Nhóm theo phút
        time_span_min = max(1.0, (df_recv["dt"].max() - df_recv["dt"].min()).total_seconds() / 60.0)
        rpm = total_recv / time_span_min
        status = "✅ PASS" if rpm >= 1.0 else "⚠️ LOW TRAFFIC"
        st.markdown(f"**Threshold Check:** `{status}` (Current: `{rpm:.2f}` vs Threshold: `1 req/min`)")
        
        c1, c2 = st.columns(2)
        c1.metric("Total Requests", f"{total_recv}")
        c2.metric("Avg Rate", f"{rpm:.2f} req/min")
        
        traffic_by_min = df_recv.set_index("dt").resample("1min").size().rename("requests")
        st.bar_chart(traffic_by_min, height=180)
    else:
        st.metric("Total Requests", f"{total_recv}")

# ================= PANEL 3: Errors & Retrieval Success =================
# Threshold: error_rate_pct <= 2%
st.divider()
row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.subheader("3. Error rate and retrieval success")
    st.caption("Events: [request_received, request_failed] | Unit: percent | Threshold: error_rate <= 2%")
    total_reqs = max(len(df_recv), len(df_sent) + len(df_fail), 1)
    failed_count = len(df_fail)
    error_rate = (failed_count / total_reqs) * 100.0
    
    # Retrieval success
    if "tool_success" in df_window.columns:
        tool_records = df_window[df_window["tool_success"].notna()]
        succ_tool = (tool_records["tool_success"] == True).sum()
        tool_succ_rate = (succ_tool / len(tool_records) * 100.0) if len(tool_records) else 100.0
    else:
        tool_succ_rate = 100.0
        
    status = "✅ PASS" if error_rate <= 2.0 else "🚨 ALERT (Error > 2%)"
    st.markdown(f"**Threshold Check:** `{status}` (Error Rate: `{error_rate:.2f}%` vs Threshold: `2%`)")
    
    e1, e2, e3 = st.columns(3)
    e1.metric("Error Rate", f"{error_rate:.2f}%")
    e2.metric("Failed Requests", f"{failed_count}")
    e3.metric("Retrieval Success", f"{tool_succ_rate:.1f}%")
    
    if failed_count > 0 and "error_type" in df_fail.columns:
        st.write("Breakdown by error_type:")
        st.dataframe(df_fail["error_type"].value_counts(), use_container_width=True)
    else:
        st.success("Không có lỗi hệ thống ghi nhận.")

# ================= PANEL 4: Cost over time =================
# Threshold: total <= 2.5 USD
with row2_col2:
    st.subheader("4. Cost over time")
    st.caption("Events: [response_sent] | Field: cost_usd | Unit: USD | Threshold: total <= $2.5")
    if not df_sent.empty and "cost_usd" in df_sent.columns:
        total_cost = float(df_sent["cost_usd"].sum())
        status = "✅ PASS" if total_cost <= 2.5 else "🚨 ALERT (Cost > $2.5)"
        st.markdown(f"**Threshold Check:** `{status}` (Total: `${total_cost:.4f}` vs Threshold: `$2.50`)")
        
        c1, c2 = st.columns(2)
        c1.metric("Total Window Cost", f"${total_cost:.4f}")
        c2.metric("Avg Cost / Request", f"${(total_cost / max(1, len(df_sent))):.5f}")
        
        if "dt" in df_sent.columns:
            cost_by_min = df_sent.set_index("dt").resample("1min")["cost_usd"].sum().rename("Cost ($)")
            st.area_chart(cost_by_min, height=180)
    else:
        st.info("Chưa có thông tin cost.")

# ================= PANEL 5: Tokens =================
# Threshold: sum_by_field <= 50000 tokens
st.divider()
row3_col1, row3_col2 = st.columns(2)

with row3_col1:
    st.subheader("5. Input and output tokens")
    st.caption("Events: [response_sent] | Fields: tokens_in, tokens_out | Unit: tokens | Threshold: <= 50000")
    if not df_sent.empty and "tokens_in" in df_sent.columns and "tokens_out" in df_sent.columns:
        total_in = int(df_sent["tokens_in"].sum())
        total_out = int(df_sent["tokens_out"].sum())
        total_tokens = total_in + total_out
        
        status = "✅ PASS" if max(total_in, total_out) <= 50000 else "🚨 ALERT (> 50,000 tokens)"
        st.markdown(f"**Threshold Check:** `{status}` (Tokens In: `{total_in}`, Out: `{total_out}`)")
        
        t1, t2, t3 = st.columns(3)
        t1.metric("Tokens In", f"{total_in:,}")
        t2.metric("Tokens Out", f"{total_out:,}")
        t3.metric("Total Tokens", f"{total_tokens:,}")
        
        token_df = pd.DataFrame({"Tokens In": [total_in], "Tokens Out": [total_out]})
        st.bar_chart(token_df, height=180)
    else:
        st.info("Chưa có thông tin tokens.")

# ================= PANEL 6: Quality Proxy =================
# Threshold: mean >= 0.75
with row3_col2:
    st.subheader("6. Quality proxy")
    st.caption("Events: [response_sent] | Field: quality_score | Unit: score_0_to_1 | Threshold: mean >= 0.75")
    if not df_sent.empty and "quality_score" in df_sent.columns:
        scores = df_sent["quality_score"].dropna().values
        mean_quality = float(np.mean(scores)) if len(scores) else 0.0
        status = "✅ PASS" if mean_quality >= 0.75 else "🚨 ALERT (Mean Quality < 0.75)"
        st.markdown(f"**Threshold Check:** `{status}` (Current: `{mean_quality:.2f}` vs Threshold: `0.75`)")
        
        q1, q2 = st.columns(2)
        q1.metric("Mean Quality Score", f"{mean_quality:.2f} / 1.0")
        q2.metric("Samples Count", f"{len(scores)}")
        
        if "dt" in df_sent.columns:
            quality_chart = df_sent.sort_values("dt")[["dt", "quality_score"]].set_index("dt")
            st.line_chart(quality_chart, height=180)
    else:
        st.info("Chưa có thông tin quality score.")
