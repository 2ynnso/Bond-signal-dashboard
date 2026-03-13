# Bond Signal Dashboard

FRED API와 시장 데이터 기반으로 채권/리스크 신호를 시각화하는 Streamlit 대시보드입니다.

## Preview

대시보드 스크린샷을 `assets/bond-signal-dashboard.png`로 저장하면 아래 이미지가 README에 바로 표시됩니다.

![Bond Signal Dashboard](./assets/bond-signal-dashboard.png)

## Features

- FRED 시계열 기반 금리, VIX, 하이일드 스프레드 모니터링
- SHYG 기반 PPR(Percentile Position Risk) 계산
- `Risk On / Neutral / Risk Off` regime 분류
- 카드형 요약 지표와 시계열 차트 제공

## Stack

- Python
- Streamlit
- Pandas / NumPy
- Plotly
- FRED API
- yfinance

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

프로젝트 폴더에 `.env` 파일을 만들고 FRED API 키를 넣습니다.

```env
FRED_API_KEY=your_api_key
```

## Run

```bash
streamlit run dashboard.py
```

## Repo Name

- `bond-signal-dashboard`
