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
- **4단계 Regime 분류**: 점수 합산이 아니라 순차적 규칙 기반 분류
- **다크 테마 UI**: 가시성 최적화된 현대적인 인터페이스
- **카드형 요약 지표와 시계열 차트**: 직관적인 데이터 시각화

## Regime 분류 시스템 상세

이 대시보드는 신호별 점수를 더하는 구조가 아닙니다.  
`VIX -> OAS_Z -> PPR` 순서로 조건을 검사하는 **순차적 룰 기반 분류**입니다.

### Rule Flow

1. **VIX > 30** 이면 바로 `Regime 4: Very Risk Off`
2. 그렇지 않고 **OAS_Z >= 0** 이면 `Regime 3: Risk Off`
3. 그렇지 않고 **PPR < 0.2** 이면 `Regime 1: Very Risk On`
4. 그렇지 않고 **PPR > 0.8** 이면 `Regime 4: Very Risk Off`
5. 위 조건에 모두 해당하지 않으면 `Regime 2: Risk On`

### Interpretation Table

| 조건 | 판정 | 의미 |
|------|------|------|
| `VIX > 30` | **Very Risk Off** | 변동성 급등 시 즉시 방어 |
| `OAS_Z >= 0` | **Risk Off** | 신용 스프레드가 평균 이상으로 벌어져 방어 신호 |
| `PPR < 0.2` | **Very Risk On** | 포지셔닝 부담이 낮아 공격적 매수 가능 |
| `PPR > 0.8` | **Very Risk Off** | 포지셔닝 부담이 높아 강한 방어 필요 |
| 나머지 구간 | **Risk On** | 위험자산 선호 유지 |

### Example

- `VIX=31` 이면 다른 지표를 보지 않고 바로 `Very Risk Off`
- `VIX=24`, `OAS_Z=0.4` 이면 `Risk Off`
- `VIX=18`, `OAS_Z=-0.6`, `PPR=0.12` 이면 `Very Risk On`
- `VIX=19`, `OAS_Z=-0.3`, `PPR=0.55` 이면 `Risk On`
- `VIX=17`, `OAS_Z=-0.4`, `PPR=0.91` 이면 `Very Risk Off`

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

현재 저장소 기준 배포 연결값은 아래처럼 두면 됩니다.

- Repository: `2ynnso/Bond-signal-dashboard`
- Branch: `main`
- Main file path: `dashboard.py`

## Environment Notes

- 로컬 실행: `.env`의 `FRED_API_KEY` 사용
- Streamlit Cloud 배포: `secrets`의 `FRED_API_KEY` 사용

## Repo Name

- `bond-signal-dashboard`
