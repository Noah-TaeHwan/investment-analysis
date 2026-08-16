#!/usr/bin/env python3
"""
lean_mini — QuantConnect LEAN 백테스트 결과(lean-results) 요약·시각화
이스트캠프 AI퀀트 4기 미니프로젝트
  "lean-results 로 데이터가 남는구나. 그걸 어떻게 써 볼까?"
  → LEAN 결과 JSON 을 파싱해서 한 줄 요약 + 지표 + 순자산곡선 리포트 생성

사용법:
    python3 lean_mini.py                      # 기본: ../lean-results / ./output
    python3 lean_mini.py -r ../lean-results -o output

산출물 (output/):
    lean_report.png   순자산곡선 + 낙폭 (+ 삼성 실가 오버레이, samsung.csv 있으면)
    summary.csv       핵심 지표 테이블
    report.md         마크다운 리포트 (한 줄 요약 포함)
"""
from __future__ import annotations

import argparse
import csv
import json
import pathlib

import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# macOS 한글 폰트 (없으면 영문 폰트로 폴백)
for fam in ("AppleGothic", "NanumGothic", "Malgun Gothic"):
    if fam in {f.name for f in matplotlib.font_manager.fontManager.ttflist}:
        plt.rcParams["font.family"] = fam
        break
plt.rcParams["axes.unicode_minus"] = False


def load_lean_result(path: pathlib.Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def extract_equity(result: dict) -> pd.DataFrame:
    """charts.Strategy Equity.Equity.values = [[ts,o,h,l,c], ...] → DataFrame[Date, Equity]"""
    vals = result["charts"]["Strategy Equity"]["series"]["Equity"]["values"]
    ts, eq = [], []
    for v in vals:
        ts.append(pd.to_datetime(v[0], unit="s", utc=True).tz_localize(None))
        eq.append(float(v[-1]))
    return pd.DataFrame({"Date": ts, "Equity": eq})


def extract_orders(result: dict) -> pd.DataFrame:
    rows = []
    for oid, o in result.get("orders", {}).items():
        rows.append(
            {
                "order_id": oid,
                "time": o.get("time", ""),
                "symbol": o.get("symbol", {}).get("permtick", ""),
                "side": "Buy" if o.get("direction", 0) == 0 else "Sell",
                "quantity": o.get("quantity", 0),
                "price": o.get("price", 0),
                "value": o.get("value", 0),
            }
        )
    return pd.DataFrame(rows)


def one_line(result: dict) -> str:
    st = result["statistics"]
    rt = result["runtimeStatistics"]
    cfg = result["algorithmConfiguration"]
    orders = extract_orders(result)
    order_desc = "주문 없음"
    if not orders.empty:
        o = orders.iloc[0]
        order_desc = (
            f"주문 {len(orders)}건 (최초 {o['time'][:10]} {o['side']} {o['quantity']:g}주 @ {o['price']:,.0f})"
        )
    return (
        f"[{cfg.get('name','LEAN')}] {cfg['startDate'][:10]} ~ {cfg['endDate'][:10]} "
        f"백테스트: 시작 {float(st['Start Equity']):,.0f} → 끝 {float(st['End Equity']):,.0f} "
        f"(Net Profit {st['Net Profit']}), 최대낙폭 {st['Drawdown']}, Sharpe {st['Sharpe Ratio']}, "
        f"Sortino {st['Sortino Ratio']} | {order_desc}"
    )


def summary_rows(result: dict) -> list[tuple[str, str]]:
    st = result["statistics"]
    rt = result["runtimeStatistics"]
    cfg = result["algorithmConfiguration"]
    state = result["state"]
    order = "없음"
    orders = extract_orders(result)
    if not orders.empty:
        o = orders.iloc[0]
        order = f"{o['time'][:10]} {o['side']} {o['quantity']:g}주 @ {o['price']:,.0f}"
    rows = [
        ("전략 이름", cfg.get("name", "-")),
        ("백테스트 기간", f"{cfg['startDate'][:10]} ~ {cfg['endDate'][:10]}"),
        ("계정 통화", cfg.get("accountCurrency", "-")),
        ("시작 잔고", st.get("Start Equity", "-")),
        ("종료 잔고", st.get("End Equity", "-")),
        ("Net Profit", st.get("Net Profit", "-")),
        ("Compounding Annual Return", st.get("Compounding Annual Return", "-")),
        ("최대낙폭 (Drawdown)", st.get("Drawdown", "-")),
        ("Sharpe Ratio", st.get("Sharpe Ratio", "-")),
        ("Sortino Ratio", st.get("Sortino Ratio", "-")),
        ("Information Ratio", st.get("Information Ratio", "-")),
        ("Probabilistic Sharpe", st.get("Probabilistic Sharpe Ratio", "-")),
        ("Win Rate / Loss Rate", f"{st.get('Win Rate','-')} / {st.get('Loss Rate','-')}"),
        ("총 주문 수", st.get("Total Orders", "-")),
        ("포트폴리오 회전율", st.get("Portfolio Turnover", "-")),
        ("실현 수수료", rt.get("Fees", "-")),
        ("보유 가치 (Holdings)", rt.get("Holdings", "-")),
        ("미실현 손익", rt.get("Unrealized", "-")),
        ("마지막 주문내역", order),
        ("백테스트 상태", state.get("Status", "-")),
    ]
    return rows


def load_samsung_price(csv_path: pathlib.Path) -> pd.DataFrame | None:
    """yfinance 멀티헤더 CSV(skiprows) → DataFrame[Date, Close]; 없으면 None"""
    if not csv_path.exists():
        return None
    try:
        df = pd.read_csv(csv_path, skiprows=[1, 2])
        df = df.rename(columns={df.columns[0]: "Date"})
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
        return df[["Date", "Close"]].dropna()
    except Exception:
        return None


def plot_report(equity: pd.DataFrame, price: pd.DataFrame | None, out_png: pathlib.Path) -> None:
    eq = equity.set_index("Date")["Equity"]
    dd = (eq / eq.cummax() - 1) * 100  # 낙폭(%)

    fig, axes = plt.subplots(2, 1, figsize=(11, 7), dpi=130, sharex=True,
                             gridspec_kw={"height_ratios": [3, 1]})
    ax, axdd = axes

    ax.plot(eq.index, eq.values, lw=1.6, color="#2563eb", label="LEAN Equity")
    if price is not None:
        ax2 = ax.twinx()
        ax2.plot(price["Date"], price["Close"], lw=1.1, ls="--", color="#ea580c",
                 alpha=0.85, label="005930.KS Close")
        ax2.set_ylabel("삼성전자 종가 (원)", color="#ea580c")
        ax2.tick_params(axis="y", labelcolor="#ea580c")
        ax2.grid(False)
    ax.set_ylabel("전략 잔고 (포인트)")
    ax.set_title("Samsung Buy & Hold — QuantConnect LEAN 백테스트", fontsize=13)
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(alpha=0.3)

    axdd.fill_between(dd.index, dd.values, 0, color="#ef4444", alpha=0.4)
    axdd.set_ylabel("Drawdown (%)")
    axdd.grid(alpha=0.3)

    axdd.xaxis.set_major_formatter(mdates.DateFormatter("%y-%m"))
    fig.tight_layout()
    fig.savefig(out_png, bbox_inches="tight")
    plt.close(fig)


def write_outputs(result: dict, out_dir: pathlib.Path,
                 price: pd.DataFrame | None) -> tuple[pathlib.Path, pathlib.Path, pathlib.Path]:
    out_dir.mkdir(parents=True, exist_ok=True)

    # summary.csv
    csv_path = out_dir / "summary.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["metric", "value"])
        w.writerows(summary_rows(result))

    # report.md
    md_path = out_dir / "report.md"
    md = [
        "# LEAN 백테스트 미니 리포트",
        "",
        f"```text",
        one_line(result),
        f"```",
        "",
        "## 핵심 지표",
        "",
        "| 지표 | 값 |",
        "|---|---|",
    ]
    for k, v in summary_rows(result):
        md.append(f"| {k} | {v} |")
    md += [
        "",
        "## 참고",
        "",
        "- 이 백테스트는 교육용 예제로, KRX 수수료·배당·거래일·환율 모델을 **포함하지 않습니다** (강사 repo `lean-samsung/README.md` 명시).",
        "- 순자산곡선은 LEAN 결과 JSON(`SamsungBuyAndHold.json`)의 Strategy Equity 에서 추출했습니다.",
        "- 삼성 종가(`005930.KS`) 오버레이는 yfinance 데이터 기준입니다.",
        "",
    ]
    if price is not None:
        md.append(f"- 가격 데이터: {price['Date'].min().date()} ~ {price['Date'].max().date()} ({len(price)} 거래일)")
        md.append("")
    md_path.write_text("\n".join(md), encoding="utf-8")

    # PNG
    equity = extract_equity(result)
    png_path = out_dir / "lean_report.png"
    plot_report(equity, price, png_path)

    return csv_path, md_path, png_path


def main() -> None:
    ap = argparse.ArgumentParser(description="LEAN 백테스트 결과 요약·시각화")
    ap.add_argument("-r", "--results", default="../lean-results", help="lean-results 폴더")
    ap.add_argument("-o", "--out", default="output", help="결과 출력 폴더")
    ap.add_argument("--json", default="SamsungBuyAndHold.json", help="결과 JSON 파일명")
    args = ap.parse_args()

    result_dir = pathlib.Path(args.results)
    result = load_lean_result(result_dir / args.json)
    price = load_samsung_price(result_dir / "samsung.csv")

    csv_path, md_path, png_path = write_outputs(result, pathlib.Path(args.out), price)

    print("=" * 64)
    print(one_line(result))
    print("=" * 64)
    print(f"✓ report : {md_path}")
    print(f"✓ chart  : {png_path}")
    print(f"✓ csv    : {csv_path}")


if __name__ == "__main__":
    main()
