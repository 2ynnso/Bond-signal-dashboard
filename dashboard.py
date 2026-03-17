from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
import certifi
from dotenv import load_dotenv

try:
    import yfinance as yf
except Exception:  # noqa: BLE001
    yf = None


ENV_PATH = Path(__file__).with_name(".env")
load_dotenv(ENV_PATH)

st.set_page_config(page_title="Bond Signal Board", page_icon=":bar_chart:", layout="wide")

FRED_SERIES = {
    "VIX": "VIXCLS",
    "UST_3M": "DGS3MO",
    "UST_2Y": "DGS2",
    "UST_3Y": "DGS3",
    "UST_5Y": "DGS5",
    "UST_7Y": "DGS7",
    "UST_10Y": "DGS10",
    "UST_10Y_2Y": "T10Y2Y",
    "HY_OAS": "BAMLH0A0HYM2",
    "HY_YIELD": "BAMLH0A0HYM2EY",
}
CARD_BG = {
    "good": "#1a3d2a",
    "neutral": "#1a2d4d",
    "bad": "#3d1a1a",
    "info": "#1a2d4d",
    "very_risk_on": "#0f3d1f",
    "risk_on": "#1a3d4d",
    "risk_off": "#3d3d1a",
    "very_risk_off": "#4d1a1a",
    "agg_benchmark": "#2d2d1a",  # 노란색 계열 배경
}
CARD_BORDER = {
    "good": "#4ade80",
    "neutral": "#60a5fa",
    "bad": "#ef4444",
    "info": "#60a5fa",
    "very_risk_on": "#22c55e",
    "risk_on": "#06b6d4",
    "risk_off": "#eab308",
    "very_risk_off": "#ff6b6b",
    "agg_benchmark": "#facc15",  # 노란색 테두리
}


def get_fred_api_key() -> str:
    env_key = os.getenv("FRED_API_KEY", "").strip()
    if env_key:
        return env_key

    try:
        secret_key = st.secrets.get("FRED_API_KEY", "").strip()
    except Exception:  # noqa: BLE001
        secret_key = ""

    return secret_key


def inject_css() -> None:
    st.markdown(
        """
        <style>
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
            background: #000000;
            color: #ffffff;
        }
        .block-container {max-width: 1380px; padding-top: 2.3rem; padding-bottom: 2rem;}
        [data-testid="stSidebar"] {
            background: #111111;
            border-right: 1px solid #333333;
        }
        .hero {
            padding: 10px 0 18px 0;
        }
        .hero-title {
            font-size: 2.55rem;
            font-weight: 800;
            line-height: 1.12;
            margin-bottom: 12px;
            color: #ffffff;
            padding-top: 4px;
        }
        .hero-sub {
            font-size: 1rem;
            color: #cccccc;
            max-width: 760px;
            line-height: 1.45;
            margin-bottom: 2px;
        }
        .card {
            border-radius: 18px;
            padding: 18px;
            min-height: 150px;
            border: 1px solid #333333;
            box-shadow: 0 12px 24px rgba(0,0,0,0.8);
            background: rgba(0,0,0,0.7);
        }
        .card-label {
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            color: #aaaaaa;
        }
        .card-value {
            margin-top: 10px;
            font-size: 2rem;
            font-weight: 800;
            line-height: 1.0;
            color: #ffffff;
        }
        .card-status {
            margin-top: 12px;
            font-size: 1rem;
            font-weight: 700;
            color: #ffffff;
        }
        .card-note {
            margin-top: 8px;
            font-size: 0.84rem;
            color: #888888;
            line-height: 1.4;
        }
        .regime-card {
            min-height: 200px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .regime-value {
            margin-top: 12px;
            font-size: 2.8rem;
            font-weight: 900;
            line-height: 1.1;
            color: #ffffff;
        }
        .panel {
            border-radius: 16px;
            padding: 14px 16px;
            border: 1px solid #333333;
            background: rgba(0,0,0,0.5);
        }
        h1, h2, h3, p, label, span, div { color: #ffffff; }
        .stMetric { background: rgba(0,0,0,0.3); border: 1px solid #333333; border-radius: 10px; }
        .stDataFrame { background: rgba(0,0,0,0.3); border: 1px solid #333333; }
        [data-testid="stDataFrameContainer"] { color: #ffffff; }
        table { color: #ffffff; }
        th { color: #cccccc; background: rgba(0,0,0,0.5) !important; }
        td { color: #ffffff; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def safe_zscore(series: pd.Series) -> pd.Series:
    std = series.std()
    if pd.isna(std) or std == 0:
        return pd.Series(index=series.index, data=0.0)
    return (series - series.mean()) / std


def percentile_rank_last(window: pd.Series) -> float:
    if window.isna().all():
        return np.nan
    return float((window <= window.iloc[-1]).mean())


def coerce_series(data: pd.DataFrame | pd.Series, preferred_columns: list[str] | None = None) -> pd.Series:
    if isinstance(data, pd.Series):
        series = data.copy()
    else:
        series = pd.Series(dtype=float)
        preferred_columns = preferred_columns or []

        if isinstance(data.columns, pd.MultiIndex):
            for column in data.columns:
                if column[-1] in preferred_columns or column[0] in preferred_columns:
                    series = data[column].copy()
                    break
            if series.empty and len(data.columns) > 0:
                series = data.iloc[:, 0].copy()
        else:
            for column in preferred_columns:
                if column in data.columns:
                    series = data[column].copy()
                    break
            if series.empty and len(data.columns) > 0:
                series = data.iloc[:, 0].copy()

    if isinstance(series, pd.DataFrame):
        series = series.iloc[:, 0]

    series = pd.to_numeric(series, errors="coerce")
    series.index = pd.to_datetime(series.index)
    return series.dropna().sort_index()


def format_value(value: float, suffix: str = "", decimals: int = 2) -> str:
    if pd.isna(value):
        return "N/A"
    return f"{value:.{decimals}f}{suffix}"


def format_delta(value: float, suffix: str = "", decimals: int = 2) -> str:
    if pd.isna(value):
        return "chg N/A"
    return f"chg {value:+.{decimals}f}{suffix}"


def format_signed(value: float, suffix: str = "", decimals: int = 2) -> str:
    if pd.isna(value):
        return "N/A"
    return f"{value:+.{decimals}f}{suffix}"


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_fred_api(start_date: pd.Timestamp, api_key: str) -> tuple[pd.DataFrame, list[str]]:
    frames: list[pd.Series] = []
    warnings: list[str] = []

    for name, series_id in FRED_SERIES.items():
        try:
            response = requests.get(
                "https://api.stlouisfed.org/fred/series/observations",
                params={
                    "series_id": series_id,
                    "api_key": api_key,
                    "file_type": "json",
                    "observation_start": start_date.strftime("%Y-%m-%d"),
                },
                timeout=20,
                verify=certifi.where(),
            )
            response.raise_for_status()
            payload = response.json()
            observations = payload.get("observations", [])
            raw = pd.DataFrame(observations)
            if raw.empty or "date" not in raw.columns or "value" not in raw.columns:
                raise ValueError("응답 데이터가 비어 있습니다.")
            series = pd.Series(
                pd.to_numeric(raw["value"].replace(".", np.nan), errors="coerce").values,
                index=pd.to_datetime(raw["date"]),
                name=name,
            )
            frames.append(series)
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"{name} 로드 실패: {exc}")

    if not frames:
        return pd.DataFrame(), warnings

    macro = pd.concat(frames, axis=1).sort_index().ffill()
    macro["HY_OAS_Z"] = safe_zscore(macro["HY_OAS"])
    return macro, warnings


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_ppr_series(start_date: pd.Timestamp) -> tuple[pd.Series, list[str]]:
    if yf is None:
        return pd.Series(dtype=float), ["yfinance가 설치되지 않아 PPR을 계산하지 못했습니다."]

    try:
        data = yf.download(
            "SHYG",
            start=start_date.strftime("%Y-%m-%d"),
            auto_adjust=True,
            progress=False,
            threads=False,
            timeout=10,
        )
    except Exception as exc:  # noqa: BLE001
        return pd.Series(dtype=float), [f"SHYG 로드 실패: {exc}"]

    if data.empty:
        return pd.Series(dtype=float), ["SHYG 데이터가 비어 있습니다."]

    shyg = coerce_series(data, preferred_columns=["Adj Close", "Close", "SHYG"])
    shyg = shyg.dropna().sort_index().resample("BME").last().ffill()
    rank = shyg.rolling(12, min_periods=6).apply(percentile_rank_last, raw=False)
    ppr = 1 - rank
    if isinstance(ppr, pd.DataFrame):
        ppr = ppr.squeeze()
    ppr.name = "PPR"
    return ppr, []


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_agg_series(start_date: pd.Timestamp) -> tuple[pd.Series, list[str]]:
    if yf is None:
        return pd.Series(dtype=float), ["yfinance가 설치되지 않아 AGG 가격을 불러올 수 없습니다."]

    try:
        data = yf.download(
            "AGG",
            start=start_date.strftime("%Y-%m-%d"),
            auto_adjust=True,
            progress=False,
            threads=False,
            timeout=10,
        )
    except Exception as exc:  # noqa: BLE001
        return pd.Series(dtype=float), [f"AGG 로드 실패: {exc}"]

    if data.empty:
        return pd.Series(dtype=float), ["AGG 데이터가 비어 있습니다."]

    agg = coerce_series(data, preferred_columns=["Adj Close", "Close", "AGG"])
    agg = agg.dropna().sort_index()
    agg.name = "AGG"
    return agg, []


def build_dataset(start_date: pd.Timestamp, api_key: str, include_ppr: bool) -> tuple[pd.DataFrame, list[str], str]:
    macro, warnings = fetch_fred_api(start_date, api_key)
    ppr_note = "PPR 비활성화"

    if macro.empty:
        return macro, warnings, ppr_note

    # AGG 데이터 추가
    agg, agg_warnings = fetch_agg_series(start_date)
    warnings.extend(agg_warnings)
    if not agg.empty:
        macro = macro.join(agg, how="left").ffill()

    if include_ppr:
        ppr, ppr_warnings = fetch_ppr_series(start_date)
        warnings.extend(ppr_warnings)
        if not ppr.empty:
            macro = macro.join(ppr, how="left").ffill()
            ppr_note = "PPR = 1 - SHYG 월말가격 12개월 percentile rank"
        else:
            macro["PPR"] = np.nan
            ppr_note = "PPR 로드 실패"
    else:
        macro["PPR"] = np.nan

    macro["risk_off_score"] = (
        (macro["VIX"] >= 30).astype(int)
        + (macro["HY_OAS_Z"] >= 0).astype(int)
        + (macro["PPR"] <= 0.2).fillna(False).astype(int)
    )
    macro["regime"] = np.select(
        [macro["risk_off_score"] >= 2, macro["risk_off_score"] == 1],
        ["Risk Off", "Neutral"],
        default="Risk On",
    )
    # 4단계 Regime 분류
    macro["regime_detailed"] = np.select(
        [macro["risk_off_score"] == 0, macro["risk_off_score"] == 1, macro["risk_off_score"] == 2, macro["risk_off_score"] >= 3],
        ["Regime 1: Very Risk On", "Regime 2: Risk On", "Regime 3: Risk Off", "Regime 4: Very Risk Off"],
        default="N/A",
    )
    return macro, warnings, ppr_note


def latest_value(frame: pd.DataFrame, column: str) -> float:
    series = frame[column].dropna() if column in frame.columns else pd.Series(dtype=float)
    return float(series.iloc[-1]) if not series.empty else np.nan


def latest_delta(frame: pd.DataFrame, column: str, periods: int = 5) -> float:
    series = frame[column].dropna() if column in frame.columns else pd.Series(dtype=float)
    if len(series) <= periods:
        return np.nan
    return float(series.iloc[-1] - series.iloc[-1 - periods])


def classify_regime_detailed(regime: str) -> tuple[str, str]:
    if pd.isna(regime):
        return "info", "N/A"
    if "Very Risk On" in regime:
        return "very_risk_on", "공격적 매수 시점"
    elif "Risk On" in regime:
        return "risk_on", "매수 포지션 강화"
    elif "Risk Off" in regime and "Very" not in regime:
        return "risk_off", "방어적 포지션 전환"
    else:  # Very Risk Off
        return "very_risk_off", "현금 보유 또는 방어"


def classify_vix(value: float) -> tuple[str, str, str]:
    if pd.isna(value):
        return "info", "N/A", "기준 30"
    if value >= 30:
        return "bad", "Risk Off", "30 이상"
    if value >= 20:
        return "neutral", "Watch", "20~30"
    return "good", "Stable", "20 미만"


def classify_oas_z(value: float) -> tuple[str, str, str]:
    if pd.isna(value):
        return "info", "N/A", "기준 0"
    if value >= 0:
        return "bad", "Wide", "0 이상"
    if value >= -0.5:
        return "neutral", "Near 0", "-0.5~0"
    return "good", "Tight", "-0.5 미만"


def classify_ppr(value: float) -> tuple[str, str, str]:
    if pd.isna(value):
        return "info", "N/A", "기준 0.2 / 0.8"
    if value <= 0.2:
        return "good", "Low", "0.2 이하"
    if value >= 0.8:
        return "bad", "High", "0.8 이상"
    return "neutral", "Middle", "0.2~0.8"


def classify_spread(value: float) -> tuple[str, str, str]:
    if pd.isna(value):
        return "info", "N/A", "10Y-2Y"
    if value < 0:
        return "bad", "Inverted", "음수"
    if value < 0.5:
        return "neutral", "Flat", "낮은 양수"
    return "good", "Positive", "정상 구간"


def render_card(title: str, value: str, status: str, note: str, tone: str) -> None:
    st.markdown(
        f"""
        <div class="card" style="background:{CARD_BG[tone]}; border-color:{CARD_BORDER[tone]};">
            <div class="card-label">{title}</div>
            <div class="card-value">{value}</div>
            <div class="card-status">{status}</div>
            <div class="card-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_regime_card(regime_name: str, note: str, risk_score: str, tone: str) -> None:
    st.markdown(
        f"""
        <div class="card regime-card" style="background:{CARD_BG[tone]}; border-color:{CARD_BORDER[tone]};">
            <div class="card-label">CURRENT REGIME</div>
            <div class="regime-value">{regime_name}</div>
            <div class="card-status">{note}</div>
            <div class="card-note">{risk_score}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero(date_label: str, regime: str) -> None:
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-title">Bond Signal Board</div>
            <div class="hero-sub">
                FRED API 기반 신호 대시보드. 
            </div>
            <div class="hero-sub">기준일: {date_label} | 현재 Regime: {regime}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_yield_panel(title: str, data: dict[str, float], columns_per_row: int = 4) -> None:
    st.markdown(f"**{title}**")
    labels = list(data.keys())
    values = list(data.values())

    for row_start in range(0, len(labels), columns_per_row):
        row_labels = labels[row_start : row_start + columns_per_row]
        row_values = values[row_start : row_start + columns_per_row]
        cols = st.columns(columns_per_row)
        for idx, col in enumerate(cols):
            if idx < len(row_labels):
                with col:
                    st.metric(row_labels[idx], format_value(row_values[idx], "%"))


def render_snapshot_board(title: str, items: list[dict[str, str]], columns_per_row: int = 4) -> None:
    with st.container(border=True):
        st.markdown(f"**{title}**")
        for start in range(0, len(items), columns_per_row):
            row = items[start : start + columns_per_row]
            cols = st.columns(columns_per_row)
            for idx, col in enumerate(cols):
                if idx < len(row):
                    item = row[idx]
                    delta_value = item["delta"].replace("chg ", "")
                    delta_float = None if delta_value == "N/A" else delta_value
                    with col:
                        st.metric(item["label"], item["value"], delta=delta_float, border=True)


def line_chart(frame: pd.DataFrame, columns: list[str], title: str, colors: list[str]) -> None:
    selected = [c for c in columns if c in frame.columns]
    if not selected:
        st.info(f"{title} 데이터가 없습니다.")
        return

    data = frame[selected].copy()
    for column in data.columns:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data = data.dropna(how="all")
    if data.empty:
        st.info(f"{title} 데이터가 없습니다.")
        return

    fig = go.Figure()
    for idx, column in enumerate(data.columns):
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data[column],
                mode="lines",
                name=column,
                line=dict(width=2.5, color=colors[idx % len(colors)]),
            )
        )
    fig.update_layout(
        title=dict(text=title, x=0, y=0.96, xanchor="left", yanchor="top", font=dict(size=20, color="#ffffff")),
        height=340,
        margin=dict(l=18, r=18, t=128, b=18),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.28,
            xanchor="left",
            x=0,
            font=dict(size=11, color="#cccccc"),
        ),
        paper_bgcolor="#111111",
        plot_bgcolor="#000000",
    )
    fig.update_xaxes(showgrid=False, color="#888888")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.1)", color="#888888")
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def signal_focus_chart(
    frame: pd.DataFrame,
    column: str,
    title: str,
    color: str,
    thresholds: list[tuple[float, str]],
    lookback: int = 260,
) -> None:
    if column not in frame.columns:
        st.info(f"{title} 데이터가 없습니다.")
        return

    data = pd.to_numeric(frame[column], errors="coerce").dropna().tail(lookback)
    if data.empty:
        st.info(f"{title} 데이터가 없습니다.")
        return

    fig = go.Figure()
    fill_color = "rgba(59,130,246,0.08)"
    if color == "#20a464":
        fill_color = "rgba(32,164,100,0.08)"
    elif color == "#dc2626":
        fill_color = "rgba(220,38,38,0.08)"

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data.values,
            mode="lines",
            name=title,
            line=dict(color=color, width=3),
            fill="tozeroy",
            fillcolor=fill_color,
        )
    )
    for level, dash_color in thresholds:
        fig.add_hline(y=level, line_dash="dash", line_color=dash_color, line_width=1.4)

    fig.update_layout(
        title=title,
        title_font=dict(size=18, color="#ffffff"),
        height=240,
        margin=dict(l=14, r=14, t=56, b=10),
        showlegend=False,
        paper_bgcolor="#111111",
        plot_bgcolor="#000000",
    )
    fig.update_xaxes(showgrid=False, color="#888888")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.1)", color="#888888")
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


inject_css()

default_key = get_fred_api_key()

with st.sidebar:
    st.header("Control")
    years = st.slider("조회 기간(년)", 1, 15, 8)
    include_ppr = st.toggle("PPR(SHYG) 포함", value=True)
    st.button("데이터 새로고침", type="primary")
    st.caption("로컬 `.env` 또는 Streamlit Cloud `secrets`의 `FRED_API_KEY`를 자동 사용")

if not default_key:
    st.error("`FRED_API_KEY`가 필요합니다. 로컬 `.env` 또는 Streamlit Cloud `secrets`에 설정하세요.")
    st.stop()

start_date = pd.Timestamp.today().normalize() - pd.DateOffset(years=years)
with st.spinner("FRED API 데이터 불러오는 중..."):
    macro, warnings, ppr_note = build_dataset(start_date, default_key, include_ppr)

for warning in warnings:
    st.warning(warning)

if macro.empty:
    st.error("데이터를 불러오지 못했습니다.")
    st.stop()

latest = macro.dropna(how="all").iloc[-1]
latest_date = macro.index.max().strftime("%Y-%m-%d")
render_hero(latest_date, str(latest["regime"]))

# Regime 상세 정보
regime_detailed = latest["regime_detailed"] if "regime_detailed" in latest.index else "N/A"
regime_tone, regime_note = classify_regime_detailed(regime_detailed)
st.divider()
st.markdown("### Strategy Regime")
risk_score_detail = f"Risk Score:\n• VIX({format_value(latest_value(macro, 'VIX'))}) • OAS_Z({format_value(latest_value(macro, 'HY_OAS_Z'))}) • PPR({format_value(latest_value(macro, 'PPR'))})"
render_regime_card(regime_detailed, regime_note, risk_score_detail, regime_tone)

vix_tone, vix_status, vix_note = classify_vix(latest_value(macro, "VIX"))
oas_tone, oas_status, oas_note = classify_oas_z(latest_value(macro, "HY_OAS_Z"))
ppr_tone, ppr_status, ppr_note_short = classify_ppr(latest_value(macro, "PPR"))
spread_tone, spread_status, spread_note = classify_spread(latest_value(macro, "UST_10Y_2Y"))

# AGG ETF 정보
agg_value = latest_value(macro, "AGG")
agg_delta = latest_delta(macro, "AGG", 1)  # 1일 전일대비
agg_tone = "agg_benchmark"  # 노란색 계열 고정

st.markdown("### Key Signal Indicators")
st.markdown("**3가지 위험도 지표 + 벤치마크 ETF**")

c1, c2, c3, c4 = st.columns(4)
with c1:
    render_card("VIX", format_value(latest_value(macro, "VIX")), vix_status, vix_note, vix_tone)
with c2:
    render_card("HY OAS Z", format_value(latest_value(macro, "HY_OAS_Z")), oas_status, oas_note, oas_tone)
with c3:
    ppr_display = format_value(latest_value(macro, "PPR"))
    render_card("PPR", ppr_display, ppr_status, ppr_note_short, ppr_tone)
with c4:
    render_card("AGG ETF", format_value(agg_value, "$"), format_signed(agg_delta, "$"), "Benchmark ETF", agg_tone)

st.caption(ppr_note)

st.markdown("### Treasury Snapshot")

render_snapshot_board(
    "US Treasury Curve",
    [
        {"label": "3M", "value": format_value(latest_value(macro, "UST_3M"), "%"), "delta": format_delta(latest_delta(macro, "UST_3M"), "%")},
        {"label": "2Y", "value": format_value(latest_value(macro, "UST_2Y"), "%"), "delta": format_delta(latest_delta(macro, "UST_2Y"), "%")},
        {"label": "3Y", "value": format_value(latest_value(macro, "UST_3Y"), "%"), "delta": format_delta(latest_delta(macro, "UST_3Y"), "%")},
        {"label": "5Y", "value": format_value(latest_value(macro, "UST_5Y"), "%"), "delta": format_delta(latest_delta(macro, "UST_5Y"), "%")},
        {"label": "7Y", "value": format_value(latest_value(macro, "UST_7Y"), "%"), "delta": format_delta(latest_delta(macro, "UST_7Y"), "%")},
        {"label": "10Y", "value": format_value(latest_value(macro, "UST_10Y"), "%"), "delta": format_delta(latest_delta(macro, "UST_10Y"), "%")},
        {"label": "10Y-2Y", "value": format_value(latest_value(macro, "UST_10Y_2Y"), "%"), "delta": format_delta(latest_delta(macro, "UST_10Y_2Y"), "%")},
        {"label": "HY Yield", "value": format_value(latest_value(macro, "HY_YIELD"), "%"), "delta": format_delta(latest_delta(macro, "HY_YIELD"), "%")},
    ],
)

st.markdown("### Signal Change Snapshot")
render_snapshot_board(
    "Short-Term Change",
    [
        {"label": "VIX 5d", "value": format_signed(latest_delta(macro, "VIX")), "delta": format_delta(latest_delta(macro, "VIX"))},
        {"label": "OAS Z 5d", "value": format_signed(latest_delta(macro, "HY_OAS_Z")), "delta": format_delta(latest_delta(macro, "HY_OAS_Z"))},
        {"label": "US 10Y 5d", "value": format_signed(latest_delta(macro, "UST_10Y"), "%"), "delta": format_delta(latest_delta(macro, "UST_10Y"), "%")},
        {"label": "PPR 1m", "value": format_signed(latest_delta(macro, "PPR", 1)), "delta": format_delta(latest_delta(macro, "PPR", 1))},
    ],
)

st.markdown("### Signal Focus")
f1, f2, f3 = st.columns(3)
with f1:
    signal_focus_chart(macro, "VIX", "VIX", "#3b82f6", [(20, "#f59e0b"), (30, "#dc2626")])
with f2:
    signal_focus_chart(macro, "HY_OAS_Z", "HY OAS Z", "#3b82f6", [(0, "#dc2626")])
with f3:
    signal_focus_chart(macro, "PPR", "PPR", "#20a464", [(0.2, "#dc2626"), (0.8, "#20a464")])

st.markdown("### Curve And Credit")
g1, g2 = st.columns(2)
with g1:
    line_chart(macro, ["UST_3Y", "UST_5Y", "UST_7Y", "UST_10Y"], "US Treasury Curve History", ["#3b82f6", "#22c55e", "#14b8a6", "#0f766e"])
with g2:
    line_chart(macro, ["HY_OAS", "HY_YIELD"], "High Yield Credit", ["#dc2626", "#14b8a6"])

g3, g4 = st.columns(2)
with g3:
    line_chart(macro, ["UST_10Y_2Y"], "Curve Slope History", ["#3b82f6"])
with g4:
    signal_history = macro[[c for c in ["VIX", "HY_OAS_Z", "PPR", "UST_10Y_2Y", "regime", "regime_detailed"] if c in macro.columns]].tail(12)
    st.subheader("Recent Signal Table")
    st.dataframe(signal_history.reset_index(), use_container_width=True, hide_index=True)
