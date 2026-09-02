from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP_VERSION = "1.0.0"
MODEL_START = date(2026, 9, 1)
DEFAULT_BALANCE = 20.71
DEFAULT_DEPOSIT = 10.0
DEFAULT_NEXT_PAYCHECK = date(2026, 9, 11)

BLUE = "#087cf2"
PANEL = "#075fd7"
DEEP = "#0647aa"
CYAN = "#55efff"
RED = "#e51b23"
ORANGE = "#ff6a00"
YELLOW = "#ffe600"
GREEN = "#24bd2d"
PURPLE = "#7a28ce"


@dataclass(frozen=True)
class AccountConfig:
    start_date: date
    current_balance: float
    next_paycheck_date: date
    frequency_days: int
    high_apy: float = 0.10
    high_limit: float = 1000.0
    excess_apy: float = 0.001


def daily_rate(apy: float) -> float:
    return (1 + apy) ** (1 / 365) - 1


def daily_interest(balance: float, cfg: AccountConfig) -> float:
    premium = min(balance, cfg.high_limit)
    excess = max(balance - cfg.high_limit, 0.0)
    return premium * daily_rate(cfg.high_apy) + excess * daily_rate(cfg.excess_apy)


def project(cfg: AccountConfig, deposit_amount: float, end_date: date) -> pd.DataFrame:
    d = cfg.start_date
    balance = cfg.current_balance
    next_deposit = cfg.next_paycheck_date
    rows = [{"date": d, "balance": balance, "deposit": 0.0, "interest": 0.0}]
    while d < end_date:
        d += timedelta(days=1)
        dep = 0.0
        if d == next_deposit:
            dep = float(deposit_amount)
            balance += dep
            next_deposit += timedelta(days=cfg.frequency_days)
        interest = daily_interest(balance, cfg)
        balance += interest
        rows.append({"date": d, "balance": balance, "deposit": dep, "interest": interest})
    return pd.DataFrame(rows)


def first_goal_date(frame: pd.DataFrame, goal: float = 1000.0):
    hit = frame[frame["balance"] >= goal]
    return None if hit.empty else hit.iloc[0]["date"]


def next_dividend_forecast(cfg: AccountConfig, deposit_amount: float, payout_date: date = date(2026, 9, 30)):
    d = cfg.start_date
    balance = cfg.current_balance
    next_deposit = cfg.next_paycheck_date
    rows = []
    accrued = 0.0
    while d <= payout_date:
        dep = 0.0
        if d == next_deposit:
            dep = float(deposit_amount)
            balance += dep
            next_deposit += timedelta(days=cfg.frequency_days)
        day_interest = daily_interest(balance, cfg)
        accrued += day_interest
        rows.append({"date": d, "balance_for_dividend": balance, "deposit": dep, "estimated_dividend_accrual": day_interest})
        d += timedelta(days=1)
    return accrued, pd.DataFrame(rows)


def scenario_table(cfg: AccountConfig, amounts: list[int]) -> pd.DataFrame:
    rows = []
    for amount in amounts:
        f = project(cfg, amount, cfg.start_date + timedelta(days=3650))
        hit = first_goal_date(f)
        if hit:
            thru = f[f["date"] <= hit]
            months = (hit - cfg.start_date).days / 30.4375
            rows.append({"Deposit": amount, "Goal Date": hit.strftime("%b %d, %Y"), "Months": round(months, 1), "Interest": float(thru["interest"].sum())})
    return pd.DataFrame(rows)


def project_two_bucket(cfg: AccountConfig, amount: float, next_apy: float, end_date: date) -> pd.DataFrame:
    d = cfg.start_date
    orsa = cfg.current_balance
    bucket2 = 0.0
    next_deposit = cfg.next_paycheck_date
    next_daily = daily_rate(next_apy)
    rows = [{"date": d, "ORSA": orsa, "Bucket #2": bucket2, "Total": orsa + bucket2}]
    while d < end_date:
        d += timedelta(days=1)
        if d == next_deposit:
            room = max(cfg.high_limit - orsa, 0.0)
            to_orsa = min(amount, room)
            orsa += to_orsa
            bucket2 += max(amount - to_orsa, 0.0)
            next_deposit += timedelta(days=cfg.frequency_days)
        orsa += daily_interest(orsa, cfg)
        bucket2 += bucket2 * next_daily
        if orsa > cfg.high_limit:
            bucket2 += orsa - cfg.high_limit
            orsa = cfg.high_limit
        rows.append({"date": d, "ORSA": orsa, "Bucket #2": bucket2, "Total": orsa + bucket2})
    return pd.DataFrame(rows)


def style_chart(fig: go.Figure, height: int = 440):
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=28, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=DEEP,
        font_color="white",
        xaxis=dict(gridcolor="#62dfff55", linecolor=CYAN),
        yaxis=dict(gridcolor="#62dfff55", linecolor=CYAN),
        legend=dict(orientation="h", y=1.08),
        hovermode="x unified",
    )


st.set_page_config(page_title="High-Yield Savings Project", page_icon="💰", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
<style>
.stApp{background:linear-gradient(180deg,#087cf2 0%,#075dcc 46%,#05378c 100%);color:white}
.block-container{max-width:1180px;padding:.35rem .45rem 3rem}header,footer{visibility:hidden}
.hero-copy,.hero-savings{min-height:330px;border:3px solid #ffe600;border-radius:22px;box-shadow:0 8px 24px #00347c88}
.hero-copy{padding:24px;background:linear-gradient(125deg,#e51b23 0%,#d70d18 30%,#087cf2 31%,#075dcc 72%,#7a28ce 100%)}
.kicker{display:inline-block;background:#ff6a00;border:2px solid #ffe600;border-radius:999px;padding:7px 11px;font-weight:1000;font-size:.72rem}
.hero-copy h1{margin:12px 0 6px;font-size:clamp(2.35rem,5vw,4.7rem);line-height:.92;letter-spacing:-.055em;font-weight:1000}.blue{color:#55efff}.orange{color:#fff200}.hero-copy p{color:white;font-size:1rem;line-height:1.48}.hero-copy b{color:#fff200}
.hero-savings{padding:18px;background:radial-gradient(circle at 80% 18%,#ff6a0077,transparent 30%),linear-gradient(145deg,#0647aa,#075fd7 58%,#7a28ce);display:flex;flex-direction:column;justify-content:center}
.s-label{font-size:.75rem;font-weight:1000;letter-spacing:.09em;color:#fff200}.s-balance{font-size:3.35rem;line-height:1;font-weight:1000;margin:6px 0}.s-arrow{font-size:1.15rem;font-weight:1000;color:#55efff}.s-goal{font-size:2.15rem;font-weight:1000;color:#fff200;margin:2px 0 12px}.s-strip{display:grid;grid-template-columns:1fr 1fr;gap:8px}.s-chip{background:#053b98;border:2px solid #55efff;border-radius:14px;padding:10px}.s-chip b{display:block;font-size:1.12rem}.s-chip span{font-size:.72rem;font-weight:900;color:#dff9ff}
[data-testid="stMetric"]{background:linear-gradient(180deg,#075fd7,#0647aa);border:2px solid #55efff;border-radius:17px;padding:14px;box-shadow:0 7px 18px #00296388}[data-testid="stMetricLabel"]{color:white!important;font-weight:900}[data-testid="stMetricValue"]{color:white!important;font-weight:1000}
.dividend-card{background:linear-gradient(120deg,#0b8f2b,#075fd7 52%,#7a28ce);border:4px solid #ffe600;border-radius:22px;padding:18px 20px;margin:13px 0;box-shadow:0 9px 24px #00347c88}.dividend-title{font-size:.8rem;font-weight:1000;letter-spacing:.08em;color:#fff200}.dividend-amount{font-size:3.6rem;font-weight:1000;line-height:1;margin:5px 0}.dividend-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:12px}.div-mini{background:#0647aa;border:2px solid #55efff;border-radius:13px;padding:10px}.div-mini span{display:block;font-size:.7rem;font-weight:900;color:#dff9ff}.div-mini b{font-size:1.05rem}.div-copy{font-size:.86rem;font-weight:800;margin-top:10px}
.stTabs [data-baseweb="tab-list"]{gap:6px;background:#075fd7;border:2px solid #55efff;border-radius:15px;padding:6px}.stTabs [data-baseweb="tab"]{border-radius:11px;color:white;font-weight:950}.stTabs [aria-selected="true"]{background:linear-gradient(90deg,#e51b23,#ff6a00)!important;color:white!important;border:2px solid #ffe600}
[data-testid="stPlotlyChart"]{border:2px solid #55efff;border-radius:18px;overflow:hidden;box-shadow:0 7px 18px #00296388}.goalbar{height:18px;background:#0647aa;border:2px solid #55efff;border-radius:999px;overflow:hidden}.goalfill{height:100%;background:linear-gradient(90deg,#24bd2d,#55efff,#ff6a00,#e51b23)}.caption{font-size:.8rem;color:white;font-weight:800}.status{background:linear-gradient(90deg,#13a52a,#075bd0);border:3px solid #ffe600;border-radius:18px;padding:14px 16px;margin:10px 0 14px}.status strong{color:#fff200}.section{font-size:1.35rem;font-weight:1000}.sub{color:#e9f8ff;font-size:.88rem;font-weight:700;margin-bottom:.65rem}.next{border:2px solid #55efff;background:linear-gradient(135deg,#0b72ed,#0649b0);border-radius:15px;padding:14px;margin:8px 0}.step{display:inline-grid;place-items:center;width:29px;height:29px;border-radius:50%;background:#ff6a00;border:2px solid #ffe600;font-weight:1000;margin-right:8px}.note{border:3px solid #ffe600;background:linear-gradient(120deg,#e51b23,#ff6a00);padding:12px 14px;border-radius:15px;font-weight:800}
@media(max-width:760px){.hero-copy,.hero-savings{min-height:280px}.hero-copy h1{font-size:2.4rem}.dividend-grid{grid-template-columns:1fr}}
</style>
""", unsafe_allow_html=True)

left, right = st.columns([1.18, .82], gap="medium")
with left:
    st.markdown(f"<div class='hero-copy'><div class='kicker'>💰 PERSONAL SAVINGS CONTROL CENTER • v{APP_VERSION}</div><h1><span class='blue'>HIGH-YIELD</span><br>SAVINGS <span class='orange'>PROJECT</span></h1><p>Fill the <b>10% APY $1,000 zone</b> first. Change the amount coming from every paycheck and instantly see how fast you reach the cap — then keep capitalizing in the next savings bucket.</p></div>", unsafe_allow_html=True)
with right:
    st.markdown("""
    <div class='hero-savings'>
      <div class='s-label'>CURRENT HIGH-YIELD SAVINGS</div><div class='s-balance'>$20.71</div><div class='s-arrow'>AUTOMATIC SAVING →</div><div class='s-goal'>$1,000 TARGET</div>
      <div class='s-strip'><div class='s-chip'><span>PREMIUM APY</span><b>10.00%</b></div><div class='s-chip'><span>PAYCHECK PLAN</span><b>$10 / CHECK</b></div></div>
    </div>""", unsafe_allow_html=True)

c1,c2,c3,c4 = st.columns([1.2,1,1,1])
with c1: deposit_amount = st.slider("Deposit every paycheck", 5, 150, int(DEFAULT_DEPOSIT), 5)
with c2: starting_balance = st.number_input("Current balance", min_value=0.0, value=DEFAULT_BALANCE, step=5.0, format="%.2f")
with c3: next_paycheck = st.date_input("Next paycheck deposit", value=DEFAULT_NEXT_PAYCHECK)
with c4: frequency = st.selectbox("Deposit frequency", [7,14,15,30], index=1, format_func=lambda x:{7:"Weekly",14:"Every 2 weeks",15:"About twice monthly",30:"Monthly"}[x])

cfg = AccountConfig(MODEL_START, float(starting_balance), next_paycheck, int(frequency))
frame = project(cfg, float(deposit_amount), MODEL_START + timedelta(days=3650))
hit = first_goal_date(frame)
thru = frame[frame["date"] <= hit] if hit else frame
interest_to_goal = float(thru["interest"].sum()) if hit else 0.0
months = ((hit - MODEL_START).days / 30.4375) if hit else None
progress = min(float(starting_balance) / 1000.0, 1.0)

sept_dividend, sept_detail = next_dividend_forecast(cfg, float(deposit_amount))
sept_deposits = sept_detail[sept_detail["deposit"] > 0]
next_dep_dates = ", ".join(d.strftime("%b %d") for d in sept_deposits["date"].tolist()) or "None"
pre_dividend_balance = float(starting_balance) + float(sept_detail["deposit"].sum())

st.markdown(f"""
<div class='dividend-card'>
  <div class='dividend-title'>💵 NEXT MONTHLY DIVIDEND FORECAST • EXPECTED AROUND SEP 30 / OCT 1</div>
  <div class='dividend-amount'>≈ ${sept_dividend:.2f}</div>
  <div class='dividend-grid'>
    <div class='div-mini'><span>STARTING SEPTEMBER BALANCE</span><b>${starting_balance:,.2f}</b></div>
    <div class='div-mini'><span>SEPTEMBER AUTO DEPOSITS</span><b>${sept_detail['deposit'].sum():,.2f}</b></div>
    <div class='div-mini'><span>BALANCE BEFORE DIVIDEND</span><b>≈ ${pre_dividend_balance:,.2f}</b></div>
  </div>
  <div class='div-copy'>At ${deposit_amount:.0f} per paycheck, the model includes deposits on <b>{next_dep_dates}</b>. Change the slider and this next-dividend estimate updates immediately.</div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"<div class='goalbar'><div class='goalfill' style='width:{progress*100:.2f}%'></div></div><div class='caption'>{progress*100:.1f}% of the $1,000 premium-rate zone filled</div>", unsafe_allow_html=True)

m1,m2,m3,m4,m5 = st.columns(5)
m1.metric("CURRENT", f"${starting_balance:,.2f}")
m2.metric("PER PAYCHECK", f"${deposit_amount}")
m3.metric("10% ZONE LEFT", f"${max(1000-starting_balance,0):,.2f}")
m4.metric("PROJECTED $1K", hit.strftime("%b %d, %Y") if hit else "Beyond model")
m5.metric("INTEREST TO $1K", f"${interest_to_goal:,.2f}" if hit else "—")
if hit:
    st.markdown(f"<div class='status'>💥 <b>${deposit_amount} every {frequency} days</b> projects to <strong>$1,000 on {hit.strftime('%B %d, %Y')}</strong> — about <b>{months:.1f} months</b>. Roughly <strong>${interest_to_goal:,.2f}</strong> comes from interest.</div>", unsafe_allow_html=True)

plan_tab, dividend_tab, race_tab, next_tab, history_tab = st.tabs(["💰 YOUR PLAN","💵 NEXT DIVIDEND","🏁 DEPOSIT RACE","🚀 AFTER $1,000","🧾 ACTUAL HISTORY"])

with plan_tab:
    end = min(MODEL_START + timedelta(days=365*5), hit + timedelta(days=180) if hit else MODEL_START + timedelta(days=365*5))
    p = frame[frame["date"] <= end]
    deps = p[p["deposit"] > 0]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=p["date"], y=p["balance"], mode="lines", name="Projected savings", line=dict(color=CYAN, width=6), fill="tozeroy", fillcolor="rgba(85,239,255,.22)"))
    fig.add_trace(go.Scatter(x=deps["date"], y=deps["balance"], mode="markers", name="Paycheck deposit", marker=dict(color=ORANGE, size=9, line=dict(color=YELLOW, width=2))))
    fig.add_hline(y=1000, line_dash="dash", line_color=RED, line_width=5, annotation_text="💰 $1,000 PREMIUM ZONE FILLED", annotation_font_color=YELLOW)
    style_chart(fig)
    fig.update_yaxes(tickprefix="$")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

with dividend_tab:
    detail = sept_detail.copy()
    detail["cumulative_dividend"] = detail["estimated_dividend_accrual"].cumsum()
    figd = go.Figure()
    figd.add_trace(go.Scatter(x=detail["date"], y=detail["cumulative_dividend"], mode="lines", name="Estimated dividend accrued", line=dict(color=YELLOW, width=6), fill="tozeroy", fillcolor="rgba(255,230,0,.18)"))
    drows = detail[detail["deposit"] > 0]
    figd.add_trace(go.Scatter(x=drows["date"], y=drows["cumulative_dividend"], mode="markers+text", name="Auto deposit", marker=dict(color=ORANGE, size=13, line=dict(color="white", width=2)), text=drows["deposit"].map(lambda x:f"+${x:.0f}"), textposition="top center"))
    style_chart(figd, 400)
    figd.update_yaxes(tickprefix="$", tickformat=".2f")
    st.plotly_chart(figd, use_container_width=True, config={"displayModeBar":False})
    a,b,c = st.columns(3)
    a.metric("EXPECTED PAYOUT", f"≈ ${sept_dividend:.2f}")
    b.metric("DEPOSITS BEFORE PAYOUT", f"${sept_detail['deposit'].sum():,.0f}")
    c.metric("EST. BALANCE AFTER PAYOUT", f"${pre_dividend_balance + sept_dividend:,.2f}")
    st.caption("Estimate assumes 10% APY remains unchanged and deposits post on the selected dates. Actual ORSA rounding/posting can differ by a cent or two.")

with race_tab:
    amounts = sorted(set([5,10,15,20,25,30,40,50,75,100,125,150,int(deposit_amount)]))
    sc = scenario_table(cfg, amounts)
    colors = [GREEN if a<25 else CYAN if a<50 else ORANGE if a<100 else RED for a in sc["Deposit"]]
    f2 = go.Figure(go.Bar(x=sc["Deposit"], y=sc["Months"], marker=dict(color=colors, line=dict(color=YELLOW,width=1)), text=sc["Months"].map(lambda x:f"{x:.1f} mo"), textposition="outside"))
    style_chart(f2, 430)
    f2.update_xaxes(title="Automatic deposit each paycheck ($)")
    f2.update_yaxes(title="Months to $1,000")
    st.plotly_chart(f2, use_container_width=True, config={"displayModeBar":False})
    table = sc.copy()
    table["Deposit"] = table["Deposit"].map(lambda x:f"${x:,.0f}")
    table["Interest"] = table["Interest"].map(lambda x:f"${x:,.2f}")
    st.dataframe(table, hide_index=True, use_container_width=True)

with next_tab:
    a,b = st.columns(2)
    with a: next_apy = st.number_input("Next savings account APY (%)", 0.0, 20.0, 4.50, .10)
    with b: total_goal = st.number_input("Total cash-savings goal", 1000.0, 50000.0, 5000.0, 500.0)
    strategy = project_two_bucket(cfg, float(deposit_amount), next_apy/100.0, MODEL_START + timedelta(days=365*12))
    orsa_rows = strategy[strategy["ORSA"] >= 1000]
    orsa_hit = None if orsa_rows.empty else orsa_rows.iloc[0]["date"]
    goal_rows = strategy[strategy["Total"] >= float(total_goal)]
    goal_hit = None if goal_rows.empty else goal_rows.iloc[0]["date"]
    q1,q2,q3,q4 = st.columns(4)
    q1.metric("ORSA TARGET","$1,000")
    q2.metric("REDIRECT START",orsa_hit.strftime("%b %d, %Y") if orsa_hit else "—")
    q3.metric("TOTAL SAVINGS GOAL",f"${total_goal:,.0f}")
    q4.metric("GOAL DATE",goal_hit.strftime("%b %d, %Y") if goal_hit else "Beyond model")
    st.markdown("<div class='next'><span class='step'>1</span><b>Fill ORSA's 10% APY bucket.</b></div><div class='next'><span class='step'>2</span><b>Redirect every future paycheck deposit to Savings Bucket #2.</b></div><div class='next'><span class='step'>3</span><b>Keep building until your emergency-fund target is reached.</b></div>", unsafe_allow_html=True)
    s = strategy[strategy["date"] <= min(MODEL_START + timedelta(days=365*6), goal_hit + timedelta(days=120) if goal_hit else MODEL_START + timedelta(days=365*6))]
    f3 = go.Figure()
    f3.add_trace(go.Scatter(x=s["date"], y=s["ORSA"], stackgroup="one", name="ORSA 10% bucket", line=dict(color=CYAN,width=3), fillcolor="rgba(85,239,255,.50)"))
    f3.add_trace(go.Scatter(x=s["date"], y=s["Bucket #2"], stackgroup="one", name="Savings Bucket #2", line=dict(color=ORANGE,width=3), fillcolor="rgba(255,106,0,.55)"))
    f3.add_hline(y=float(total_goal), line_dash="dot", line_color=YELLOW, line_width=4, annotation_text=f"🔥 ${total_goal:,.0f} TOTAL SAVINGS GOAL", annotation_font_color=YELLOW)
    style_chart(f3,470)
    f3.update_yaxes(tickprefix="$")
    st.plotly_chart(f3,use_container_width=True,config={"displayModeBar":False})
    st.markdown("<div class='note'><b>Strategy:</b> once the 10% tier is full, change the destination — not the automatic-saving behavior.</div>", unsafe_allow_html=True)

with history_tab:
    hp = Path("data/savings_transactions.csv")
    if hp.exists():
        hist = pd.read_csv(hp)
        hist["date"] = pd.to_datetime(hist["date"])
        hist = hist.sort_values("date", ascending=False)
        st.dataframe(hist, hide_index=True, use_container_width=True)
    else:
        st.info("Savings transaction history file is not present yet.")

st.markdown(f"<div class='caption' style='text-align:center;margin-top:20px'>High-Yield Savings Project v{APP_VERSION} • standalone repository</div>", unsafe_allow_html=True)
