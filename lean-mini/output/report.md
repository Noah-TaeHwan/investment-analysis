# LEAN 백테스트 미니 리포트

```text
[local] 2024-01-01 ~ 2025-01-01 백테스트: 시작 1,000,000 → 끝 973,600 (Net Profit -2.640%), 최대낙폭 3.800%, Sharpe -3.919, Sortino -4.661 | 주문 1건 (최초 2024-01-03 Buy 1주 @ 79,600)
```

## 핵심 지표

| 지표 | 값 |
|---|---|
| 전략 이름 | local |
| 백테스트 기간 | 2024-01-01 ~ 2025-01-01 |
| 계정 통화 | USD |
| 시작 잔고 | 1000000 |
| 종료 잔고 | 973600 |
| Net Profit | -2.640% |
| Compounding Annual Return | -2.641% |
| 최대낙폭 (Drawdown) | 3.800% |
| Sharpe Ratio | -3.919 |
| Sortino Ratio | -4.661 |
| Information Ratio | -0.974 |
| Probabilistic Sharpe | 0.000% |
| Win Rate / Loss Rate | 0% / 0% |
| 총 주문 수 | 1 |
| 포트폴리오 회전율 | 0.02% |
| 실현 수수료 | -$0.00 |
| 보유 가치 (Holdings) | $53,200.00 |
| 미실현 손익 | $-26,400.00 |
| 마지막 주문내역 | 2024-01-03 Buy 1주 @ 79,600 |
| 백테스트 상태 | Completed |

## 참고

- 이 백테스트는 교육용 예제로, KRX 수수료·배당·거래일·환율 모델을 **포함하지 않습니다** (강사 repo `lean-samsung/README.md` 명시).
- 순자산곡선은 LEAN 결과 JSON(`SamsungBuyAndHold.json`)의 Strategy Equity 에서 추출했습니다.
- 삼성 종가(`005930.KS`) 오버레이는 yfinance 데이터 기준입니다.

- 가격 데이터: 2024-01-02 ~ 2024-12-30 (244 거래일)
