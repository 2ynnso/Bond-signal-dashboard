# Bond Signal Dashboard

FRED API와 시장 데이터 기반으로 채권/리스크 신호를 시각화하는 Streamlit 대시보드입니다.

## Preview

대시보드 스크린샷 두 장을 아래처럼 함께 확인할 수 있습니다.

![Bond Signal Dashboard](./assets/bond-signal-dashboard.png)
![Bond Signal Dashboard 2](./assets/bond-signal-dashboard-2.png)



## Features

- **실시간 시장 데이터 모니터링**: FRED 시계열 기반 금리, VIX, 하이일드 스프레드 모니터링
- **벤치마크 ETF 추적**: AGG ETF 가격 및 전일대비 변동률 실시간 확인
- **PPR 계산**: SHYG 기반 Percentile Position Risk 계산 (12개월 롤링 백분위수)
- **4단계 Regime 분류**: Risk Score 기반 정교한 시장 상황 평가
- **다크 테마 UI**: 가시성 최적화된 현대적인 인터페이스
- **카드형 요약 지표와 시계열 차트**: 직관적인 데이터 시각화

## Regime 분류 시스템 상세

대시보드는 3가지 주요 위험 지표를 종합하여 **Risk Score(0-3점)**를 계산하고, 이를 기반으로 4단계 시장 Regime을 분류합니다.

### Risk Score 계산 방식
점수는 다음 3가지 지표의 조건 충족 여부에 따라 부여됩니다:

1. **VIX (변동성 지수)**: 30 이상이면 +1점
2. **HY OAS Z (하이일드 신용 스프레드 Z-점수)**: 0 이상이면 +1점
3. **PPR (Percentile Position Risk)**: 0.2 이하면 +1점

### 4단계 Regime 분류

| Regime | Risk Score | 시장 상황 | 투자 전략 | 색상 |
|--------|------------|-----------|-----------|------|
| **Regime 1: Very Risk On** | 0점 | 매우 안정적, 위험 회피 심리 낮음 | 공격적 매수 시점 | 초록색 |
| **Regime 2: Risk On** | 1점 | 안정적, 긍정적 시장 심리 | 매수 포지션 강화 | 시안색 |
| **Regime 3: Risk Off** | 2점 | 불안정, 위험 회피 심리 높음 | 방어적 포지션 전환 | 노란색 |
| **Regime 4: Very Risk Off** | 3점 | 매우 불안정, 극심한 위험 회피 | 현금 보유 또는 방어 | 빨간색 |

**예시**: VIX=25, HY_OAS_Z=-0.5, PPR=0.3 → Risk Score=0점 → Very Risk On

## Stack

- **Frontend**: Streamlit (다크 테마 UI)
- **Backend**: Python 3.8+
- **Data Processing**: Pandas, NumPy
- **Visualization**: Plotly
- **Data Sources**: 
  - FRED API (경제 지표)
  - yfinance (ETF 가격 데이터)
- **Environment**: python-dotenv, certifi

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

앱은 접속 시 자동으로 데이터를 불러옵니다.

## Share As Web Page

가장 빠른 방법은 Streamlit Community Cloud 배포입니다.

1. 이 폴더를 GitHub 저장소로 푸시합니다.
2. [Streamlit Community Cloud](https://share.streamlit.io/)에서 GitHub 저장소를 연결합니다.
3. Main file path를 `dashboard.py`로 지정합니다.
4. 앱 설정의 Secrets에 아래 값을 넣습니다.

```toml
FRED_API_KEY="your_api_key"
```

배포가 끝나면 공개 URL이 생성되고, 그 링크를 그대로 사람들에게 공유하면 됩니다.

## Environment Notes

- 로컬 실행: `.env`의 `FRED_API_KEY` 사용
- Streamlit Cloud 배포: `secrets`의 `FRED_API_KEY` 사용

## Repo Name

- `bond-signal-dashboard`
