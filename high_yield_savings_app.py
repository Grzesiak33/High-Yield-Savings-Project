from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP_VERSION = "1.5.0"
START = date(2026, 9, 1)
DEFAULT_BALANCE = 20.71
DEFAULT_DEPOSIT = 10.0
DEFAULT_NEXT = date(2026, 9, 11)
BLUE = "#087CF2"
DEEP_BLUE = "#053B98"
NAVY = "#061A45"
RED = "#E51B23"
ORANGE = "#FF6A00"
YELLOW = "#FFE600"
WHITE = "#FFFFFF"

@dataclass(frozen=True)
class Cfg:
    start: date
    balance: float
    next_dep: date
    freq: int
    apy: float = 0.10
    cap: float = 1000.0
    excess_apy: float = 0.001


def daily_rate(apy: float) -> float:
    return (1 + apy) ** (1 / 365) - 1


def daily_interest(balance: float, cfg: Cfg) -> float:
    premium = min(balance, cfg.cap)
    excess = max(balance - cfg.cap, 0)
    return premium * daily_rate(cfg.apy) + excess * daily_rate(cfg.excess_apy)


def project(cfg: Cfg, amount: float, end: date) -> pd.DataFrame:
    d, bal, nxt = cfg.start, cfg.balance, cfg.next_dep
    rows = []
    while d <= end:
        dep = 0.0
        if d == nxt:
            dep = float(amount)
            bal += dep
            nxt += timedelta(days=cfg.freq)
        intr = daily_interest(bal, cfg)
        bal += intr
        rows.append({"date": d, "balance": bal, "deposit": dep, "interest": intr})
        d += timedelta(days=1)
    return pd.DataFrame(rows)


def goal_date(df: pd.DataFrame, goal: float = 1000.0):
    hit = df[df["balance"] >= goal]
    return None if hit.empty else hit.iloc[0]["date"]


def dividend_forecast(cfg: Cfg, amount: float, payout: date = date(2026, 9, 30)):
    d, bal, nxt = cfg.start, cfg.balance, cfg.next_dep
    total, rows = 0.0, []
    while d <= payout:
        dep = 0.0
        if d == nxt:
            dep = float(amount)
            bal += dep
            nxt += timedelta(days=cfg.freq)
        intr = daily_interest(bal, cfg)
        total += intr
        rows.append({"date": d, "balance": bal, "deposit": dep, "accrual": intr})
        d += timedelta(days=1)
    return total, pd.DataFrame(rows)


def scenarios(cfg: Cfg, values) -> pd.DataFrame:
    rows = []
    for amount in values:
        df = project(cfg, amount, cfg.start + timedelta(days=3650))
        hit = goal_date(df)
        if hit:
            thru = df[df["date"] <= hit]
            rows.append({
                "Deposit": amount,
                "Goal Date": hit,
                "Months": round((hit - cfg.start).days / 30.4375, 1),
                "Interest": float(thru["interest"].sum()),
            })
    return pd.DataFrame(rows)


def two_bucket(cfg: Cfg, amount: float, next_apy: float, end: date) -> pd.DataFrame:
    d, orsa, bucket2, nxt = cfg.start, cfg.balance, 0.0, cfg.next_dep
    rows = []
    while d <= end:
        if d == nxt:
            room = max(cfg.cap - orsa, 0)
            to_orsa = min(amount, room)
            orsa += to_orsa
            bucket2 += max(amount - to_orsa, 0)
            nxt += timedelta(days=cfg.freq)
        orsa += daily_interest(orsa, cfg)
        bucket2 += bucket2 * daily_rate(next_apy)
        if orsa > cfg.cap:
            bucket2 += orsa - cfg.cap
            orsa = cfg.cap
        rows.append({"date": d, "ORSA": orsa, "Bucket #2": bucket2, "Total": orsa + bucket2})
        d += timedelta(days=1)
    return pd.DataFrame(rows)


def money(v: float) -> str:
    return f"${v:,.2f}"


def style_chart(fig: go.Figure, height: int = 390):
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=32, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=NAVY,
        font_color=WHITE,
        xaxis=dict(gridcolor="#2B5AA0", tickfont=dict(color=WHITE)),
        yaxis=dict(gridcolor="#2B5AA0", tickfont=dict(color=WHITE)),
        legend=dict(orientation="h", y=1.07),
        hovermode="x unified",
    )


st.set_page_config(page_title="High-Yield Savings Project", page_icon="💰", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
:root{--blue:#087CF2;--deep:#053B98;--navy:#061A45;--red:#E51B23;--orange:#FF6A00;--yellow:#FFE600;--white:#FFFFFF}
.stApp{background:linear-gradient(180deg,#087CF2 0%,#075dcc 20%,#061A45 72%,#04102d 100%);color:white}
.block-container{max-width:1380px;padding:.35rem .7rem 3rem}header,footer{visibility:hidden}
.brand{font-family:Impact,Arial Black,sans-serif;font-size:clamp(2rem,5vw,4.1rem);line-height:.9;font-style:italic;color:white;text-shadow:3px 3px 0 #E51B23;margin:.15rem 0 .55rem}.brand span{color:#FFE600}
.hero{border:4px solid #FFE600;border-radius:20px;padding:5px;background:#061A45;box-shadow:0 8px 0 #E51B23}.hero img{width:100%;display:block;border-radius:13px}
.banner{background:linear-gradient(90deg,#E51B23,#FF6A00);color:white;border:3px solid #FFE600;border-radius:14px;padding:12px 14px;margin:12px 0;font-weight:1000;line-height:1.35}
.section-title{font-size:1.25rem;font-weight:1000;color:white;margin:.8rem 0 .35rem}.goalbar{height:20px;background:#061A45;border:2px solid white;border-radius:999px;overflow:hidden}.goalfill{height:100%;background:linear-gradient(90deg,#FFE600,#FF6A00,#E51B23)}.goalcopy{font-weight:900;color:white;margin-top:5px}
[data-testid="stVerticalBlockBorderWrapper"]{background:rgba(6,26,69,.93);border:2px solid #FF6A00!important;border-radius:16px!important}
.stButton button{width:100%;min-height:82px;background:linear-gradient(145deg,#087CF2,#053B98)!important;color:white!important;border:3px solid #FFE600!important;border-radius:15px!important;font-weight:1000!important;font-size:1rem!important;white-space:pre-line!important;line-height:1.25!important;box-shadow:0 5px 0 #E51B23!important}
.stButton button:hover,.stButton button:focus{background:linear-gradient(145deg,#E51B23,#FF6A00)!important;color:white!important;border-color:white!important}
.stButton button p{color:white!important}
.action-panel{background:#061A45;border:3px solid #FF6A00;border-left:8px solid #FFE600;border-radius:15px;padding:15px;margin:10px 0;color:white}.action-panel b{color:#FFE600}.big{font-family:Impact,Arial Black;font-size:clamp(2.5rem,7vw,4.5rem);color:white;text-shadow:3px 3px 0 #E51B23;line-height:1}
.insight{background:linear-gradient(90deg,#053B98,#087CF2);border:2px solid #FFE600;border-radius:13px;padding:12px;margin:8px 0;color:white;font-weight:900}
.stTabs [data-baseweb="tab-list"]{background:#061A45;border:2px solid #FF6A00;border-radius:12px;padding:4px;gap:4px;overflow-x:auto}.stTabs [data-baseweb="tab"]{color:white!important;font-weight:900;min-width:max-content}.stTabs [aria-selected="true"]{background:#E51B23!important;color:white!important;border-radius:9px;border:2px solid #FFE600}
[data-testid="stMetric"]{background:#061A45!important;border:2px solid #FF6A00;border-radius:13px;padding:12px}[data-testid="stMetricLabel"]{color:white!important;font-weight:900!important}[data-testid="stMetricValue"]{color:#FFE600!important;font-weight:1000!important}
[data-testid="stPlotlyChart"]{border:2px solid #FF6A00;border-radius:14px;overflow:hidden;background:#061A45}
label,p,span,div{color:inherit} [data-testid="stMarkdownContainer"] p{color:white}
[data-baseweb="select"]>div,[data-baseweb="input"]>div,input{color:#061A45!important;background:white!important} input{font-size:16px!important}
.stSlider label,.stSelectbox label,.stNumberInput label,.stDateInput label,.stRadio label{color:white!important;font-weight:900!important}
.stAlert p{color:#061A45!important}.stAlert{border:2px solid #FFE600!important}
@media(max-width:700px){
 .block-container{padding:.2rem .38rem 2rem}.brand{font-size:2.25rem}.hero{border-width:3px;box-shadow:0 5px 0 #E51B23}.banner{font-size:.92rem}.section-title{font-size:1.08rem}
 [data-testid="column"]{min-width:100%!important;width:100%!important;flex:1 1 100%!important}
 .stButton button{min-height:70px;font-size:.95rem;margin-bottom:.25rem}
 .stTabs [data-baseweb="tab-list"]{flex-wrap:nowrap}.stTabs [data-baseweb="tab"]{font-size:.82rem;padding:8px 9px}
 [data-testid="stPlotlyChart"]{min-height:300px}.action-panel{font-size:.94rem}.big{font-size:3rem}
}
</style>
""", unsafe_allow_html=True)

if "focus" not in st.session_state:
    st.session_state.focus = "none"
if "selected_plan" not in st.session_state:
    st.session_state.selected_plan = None

def set_focus(name: str):
    st.session_state.focus = name

st.markdown(f"<div class='brand'>HIGH-YIELD <span>SAVINGS</span> PROJECT <small style='font-size:.28em'>v{APP_VERSION}</small></div>", unsafe_allow_html=True)
st.markdown("<div class='hero'><img src='https://raw.githubusercontent.com/Grzesiak33/High-Yield-Savings-Project/main/assets/savings_hero.png'></div>", unsafe_allow_html=True)
st.markdown("<div class='banner'>⚡ BLUE + RED + ORANGE MODE: tap a card to DO something. If a section cannot help you make a decision, it does not live on the dashboard.</div>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown("<div class='section-title'>🎮 CONTROL YOUR PLAN</div>", unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    with c1:
        amount = st.slider("Automatic savings each paycheck", 5, 250, int(DEFAULT_DEPOSIT), 5)
    with c2:
        balance = st.number_input("Current savings balance", min_value=0.0, value=DEFAULT_BALANCE, step=5.0, format="%.2f")
    with c3:
        next_dep = st.date_input("Next automatic deposit", value=DEFAULT_NEXT)
    with c4:
        freq = st.selectbox("Deposit schedule", [7,14,15,30], index=1, format_func=lambda x:{7:"Weekly",14:"Every 2 weeks",15:"Every 15 days",30:"Monthly"}[x])

cfg = Cfg(START, float(balance), next_dep, int(freq))
frame = project(cfg, float(amount), START + timedelta(days=3650))
goal = goal_date(frame)
thru = frame[frame["date"] <= goal] if goal else frame
earned = float(thru["interest"].sum())
months = (goal - START).days / 30.4375 if goal else 0
remaining = max(1000 - balance, 0)
progress = min(balance / 1000, 1)
div, detail = dividend_forecast(cfg, float(amount))
pre = balance + float(detail["deposit"].sum())
dates = ", ".join(d.strftime("%b %d") for d in detail[detail["deposit"] > 0]["date"].tolist()) or "None"

st.markdown(f"<div class='goalbar'><div class='goalfill' style='width:{progress*100:.2f}%'></div></div><div class='goalcopy'>{progress*100:.1f}% FILLED • {money(remaining)} LEFT • 10% APY ZONE</div>", unsafe_allow_html=True)

st.markdown("<div class='section-title'>🔥 TAP A CARD</div>", unsafe_allow_html=True)
a,b,c,d = st.columns(4)
with a:
    if st.button(f"💰 SAVED NOW\n{money(balance)}", key="saved_card"):
        set_focus("balance")
with b:
    if st.button(f"🎯 CLOSE THE GAP\n{money(remaining)} LEFT", key="gap_card"):
        set_focus("gap")
with c:
    if st.button(f"💵 NEXT DIVIDEND\n≈ {money(div)}", key="div_card"):
        set_focus("dividend")
with d:
    if st.button(f"🏁 $1,000 DATE\n{goal.strftime('%b %d, %Y') if goal else 'Beyond model'}", key="goal_card"):
        set_focus("goal")

if st.session_state.focus == "balance":
    st.markdown(f"<div class='action-panel'><b>BALANCE ACTION</b><div class='big'>{money(balance)}</div>Use the Current savings balance field above whenever ORSA changes. At a simple 10%/12 monthly approximation, {money(balance)} represents about {money(balance*.10/12)} of monthly interest before new deposits.</div>", unsafe_allow_html=True)
elif st.session_state.focus == "gap":
    st.markdown("<div class='action-panel'><b>CLOSE-THE-GAP CALCULATOR</b><br>Choose how quickly you want to fill the first $1,000.</div>", unsafe_allow_html=True)
    target_months = st.slider("Target months to $1,000", 3, 48, 12, 1)
    target_date = START + timedelta(days=round(target_months * 30.4375))
    candidates = scenarios(cfg, range(5, 501, 5))
    possible = candidates[candidates["Goal Date"] <= target_date]
    need = None if possible.empty else int(possible.iloc[0]["Deposit"])
    if need is not None:
        delta = max(need - amount, 0)
        st.success(f"About ${need}/paycheck targets roughly {target_months} months. That's ${delta}/check above your current setting." if delta else f"Your current ${amount}/check plan already meets this challenge.")
    else:
        st.warning("That timeline needs more than $500/paycheck in this calculator. Give yourself more time.")
elif st.session_state.focus == "dividend":
    st.markdown(f"<div class='action-panel'><b>NEXT DIVIDEND BREAKDOWN</b><div class='big'>≈ {money(div)}</div>Automatic deposits before payout: {money(detail['deposit'].sum())} on {dates}. Estimated balance before dividend: {money(pre)}.</div>", unsafe_allow_html=True)
    x = detail.copy(); x["cumulative"] = x["accrual"].cumsum()
    fig = go.Figure(go.Scatter(x=x["date"], y=x["cumulative"], mode="lines+markers", line=dict(color=ORANGE,width=5), marker=dict(color=YELLOW,size=6), fill="tozeroy", fillcolor="rgba(255,106,0,.16)"))
    style_chart(fig, 320); fig.update_yaxes(tickprefix="$", tickformat=".2f")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
elif st.session_state.focus == "goal":
    st.markdown(f"<div class='action-panel'><b>$1,000 FINISH LINE</b><div class='big'>{goal.strftime('%b %d, %Y') if goal else '—'}</div>About {months:.1f} months on the current plan, with approximately {money(earned)} in modeled interest along the way.</div>", unsafe_allow_html=True)

st.markdown("<div class='section-title'>🚀 TAP A PLAN TO TEST IT</div>", unsafe_allow_html=True)
plan_values = [10,20,30,50,75,100]
cols = st.columns(6)
for col, val in zip(cols, plan_values):
    temp = project(cfg, val, START + timedelta(days=3650))
    temp_hit = goal_date(temp)
    label = temp_hit.strftime("%b %Y") if temp_hit else "—"
    with col:
        if st.button(f"${val}/CHECK\n{label}", key=f"plan_{val}"):
            st.session_state.selected_plan = val
if st.session_state.selected_plan:
    val = st.session_state.selected_plan
    temp = project(cfg, val, START + timedelta(days=3650))
    temp_hit = goal_date(temp)
    temp_div, _ = dividend_forecast(cfg, val)
    st.markdown(f"<div class='insight'>⚡ TESTING <b>${val}/check</b>: $1,000 around <b>{temp_hit.strftime('%B %d, %Y') if temp_hit else 'beyond model'}</b> • next dividend ≈ <b>{money(temp_div)}</b>. Set the main paycheck slider to ${val} if you want to make it your active plan.</div>", unsafe_allow_html=True)

st.markdown("<div class='section-title'>🧭 CHOOSE WHAT YOU WANT TO DO</div>", unsafe_allow_html=True)
view = st.radio("", ["Growth","Compare plans","After $1K","Real history"], horizontal=True, label_visibility="collapsed")

if view == "Growth":
    horizon = st.radio("Chart range", ["To $1,000","1 year","2 years","5 years"], horizontal=True)
    ends = {"1 year":START+timedelta(days=365),"2 years":START+timedelta(days=730),"5 years":START+timedelta(days=1825)}
    end = goal + timedelta(days=30) if horizon == "To $1,000" and goal else ends.get(horizon, START+timedelta(days=365))
    p = frame[frame["date"] <= end]
    deps = p[p["deposit"] > 0]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=p["date"], y=p["balance"], mode="lines", name="Balance", line=dict(color=YELLOW,width=5), fill="tozeroy", fillcolor="rgba(255,230,0,.10)"))
    fig.add_trace(go.Scatter(x=deps["date"], y=deps["balance"], mode="markers", name="Deposits", marker=dict(color=ORANGE,size=8)))
    fig.add_hline(y=1000, line_dash="dash", line_color=RED, annotation_text="$1,000")
    style_chart(fig); fig.update_yaxes(tickprefix="$", title="Savings")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

elif view == "Compare plans":
    max_compare = st.slider("Compare plans up to $/paycheck", 25, 250, max(100,int(amount)), 5)
    vals = [v for v in [5,10,15,20,25,30,40,50,75,100,125,150,200,250,int(amount)] if v <= max_compare]
    sc = scenarios(cfg, sorted(set(vals)))
    fig = go.Figure(go.Bar(x=sc["Deposit"], y=sc["Months"], marker=dict(color=[BLUE if a<=30 else YELLOW if a<=75 else ORANGE if a<=150 else RED for a in sc["Deposit"]]), text=sc["Months"].map(lambda v:f"{v:.1f} mo"), textposition="outside"))
    style_chart(fig); fig.update_xaxes(title="$/paycheck"); fig.update_yaxes(title="Months to $1,000")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

elif view == "After $1K":
    next_apy = st.slider("Next account APY", 0.0, 10.0, 4.5, .1, format="%.1f%%")
    big_goal = st.number_input("Next total savings goal", 1000.0, 50000.0, 5000.0, 500.0)
    s = two_bucket(cfg, float(amount), next_apy/100, START+timedelta(days=365*12))
    orsa_rows = s[s["ORSA"] >= 1000]
    goal_rows = s[s["Total"] >= big_goal]
    od = None if orsa_rows.empty else orsa_rows.iloc[0]["date"]
    gd = None if goal_rows.empty else goal_rows.iloc[0]["date"]
    st.markdown(f"<div class='action-panel'><b>NEXT MOVE</b><br>1️⃣ Fill ORSA: <b>{od.strftime('%b %d, %Y') if od else '—'}</b><br>2️⃣ Redirect new deposits to a {next_apy:.1f}% account.<br>3️⃣ Reach {money(big_goal)} total: <b>{gd.strftime('%b %d, %Y') if gd else '—'}</b></div>", unsafe_allow_html=True)

else:
    p = Path("data/savings_transactions.csv")
    if p.exists():
        h = pd.read_csv(p); h["date"] = pd.to_datetime(h["date"])
        st.dataframe(h.sort_values("date", ascending=False), hide_index=True, use_container_width=True)
    else:
        st.info("Savings history file not found.")

st.markdown(f"<div class='goalcopy' style='text-align:center;margin-top:18px'>HIGH-YIELD SAVINGS PROJECT v{APP_VERSION} • BLUE • RED • ORANGE • EVERY TAP HAS A JOB</div>", unsafe_allow_html=True)
