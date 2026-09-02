from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP_VERSION = "1.1.0"
MODEL_START = date(2026, 9, 1)
DEFAULT_BALANCE = 20.71
DEFAULT_DEPOSIT = 10.0
DEFAULT_NEXT_PAYCHECK = date(2026, 9, 11)
BLUE="#087cf2"; DEEP="#0647aa"; CYAN="#55efff"; RED="#e51b23"; ORANGE="#ff6a00"; YELLOW="#ffe600"; GREEN="#24bd2d"; PURPLE="#7a28ce"

@dataclass(frozen=True)
class AccountConfig:
    start_date: date; current_balance: float; next_paycheck_date: date; frequency_days: int
    high_apy: float=.10; high_limit: float=1000.; excess_apy: float=.001

def daily_rate(apy): return (1+apy)**(1/365)-1

def daily_interest(balance,cfg):
    return min(balance,cfg.high_limit)*daily_rate(cfg.high_apy)+max(balance-cfg.high_limit,0)*daily_rate(cfg.excess_apy)

def project(cfg,amount,end_date):
    d=cfg.start_date; bal=cfg.current_balance; nxt=cfg.next_paycheck_date; rows=[]
    while d<=end_date:
        dep=0.
        if d==nxt: dep=float(amount); bal+=dep; nxt+=timedelta(days=cfg.frequency_days)
        intr=daily_interest(bal,cfg); bal+=intr
        rows.append({"date":d,"balance":bal,"deposit":dep,"interest":intr}); d+=timedelta(days=1)
    return pd.DataFrame(rows)

def first_goal_date(df,goal=1000.):
    h=df[df.balance>=goal]; return None if h.empty else h.iloc[0].date

def dividend_forecast(cfg,amount,payout=date(2026,9,30)):
    d=cfg.start_date; bal=cfg.current_balance; nxt=cfg.next_paycheck_date; rows=[]; accrued=0.
    while d<=payout:
        dep=0.
        if d==nxt: dep=float(amount); bal+=dep; nxt+=timedelta(days=cfg.frequency_days)
        intr=daily_interest(bal,cfg); accrued+=intr
        rows.append({"date":d,"balance":bal,"deposit":dep,"accrual":intr}); d+=timedelta(days=1)
    return accrued,pd.DataFrame(rows)

def scenarios(cfg,amounts):
    out=[]
    for a in amounts:
        f=project(cfg,a,cfg.start_date+timedelta(days=3650)); hit=first_goal_date(f)
        if hit:
            x=f[f.date<=hit]; out.append({"Deposit":a,"Goal Date":hit.strftime("%b %d, %Y"),"Months":round((hit-cfg.start_date).days/30.4375,1),"Interest":x.interest.sum()})
    return pd.DataFrame(out)

def two_bucket(cfg,amount,next_apy,end):
    d=cfg.start_date; orsa=cfg.current_balance; b2=0.; nxt=cfg.next_paycheck_date; r2=daily_rate(next_apy); rows=[]
    while d<=end:
        if d==nxt:
            room=max(1000-orsa,0); add=min(amount,room); orsa+=add; b2+=max(amount-add,0); nxt+=timedelta(days=cfg.frequency_days)
        orsa+=daily_interest(orsa,cfg); b2+=b2*r2
        if orsa>1000: b2+=orsa-1000; orsa=1000
        rows.append({"date":d,"ORSA":orsa,"Bucket #2":b2,"Total":orsa+b2}); d+=timedelta(days=1)
    return pd.DataFrame(rows)

def style(fig,h=430):
    fig.update_layout(height=h,margin=dict(l=8,r=8,t=28,b=8),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor=DEEP,font_color="white",xaxis=dict(gridcolor="#55efff44"),yaxis=dict(gridcolor="#55efff44"),legend=dict(orientation="h",y=1.08),hovermode="x unified")

st.set_page_config(page_title="High-Yield Savings Project",page_icon="💰",layout="wide",initial_sidebar_state="collapsed")
st.markdown('''<style>
.stApp{background:radial-gradient(circle at 50% 0,#168eff 0,#075dcc 38%,#032a72 100%);color:white}.block-container{max-width:1180px;padding:.4rem .55rem 3rem}header,footer{visibility:hidden}
.heroTitle{font-family:Impact,Arial Black,sans-serif;text-align:center;font-size:clamp(2.4rem,7vw,5.8rem);line-height:.85;color:#fff;text-shadow:4px 5px 0 #061a45,-3px -2px 0 #e51b23;margin:8px 0}.heroTitle span{color:#ffe600}.tag{text-align:center;font-weight:1000;letter-spacing:.12em;color:#55efff;margin-bottom:10px}.heroFrame{border:5px solid #ffe600;border-radius:24px;background:#0647aa;padding:6px;box-shadow:0 12px 0 #041b4b,0 20px 35px #001b4f}.heroFrame img{width:100%;border-radius:16px;display:block}.power{background:linear-gradient(110deg,#e51b23,#ff6a00);border:4px solid #ffe600;border-radius:18px;padding:13px;text-align:center;font-family:Arial Black;font-size:1.25rem;box-shadow:0 7px 0 #05235b;margin:14px 0}.controlbox{background:#0647aa;border:3px solid #55efff;border-radius:18px;padding:12px;box-shadow:0 7px 0 #032a72}[data-testid="stMetric"]{background:linear-gradient(145deg,#075fd7,#0647aa);border:3px solid #55efff;border-radius:17px;padding:13px;box-shadow:0 7px 0 #03265f}[data-testid="stMetricLabel"]{font-weight:1000;color:#fff!important}[data-testid="stMetricValue"]{font-weight:1000;color:#ffe600!important}.divCard{background:linear-gradient(120deg,#119a32,#087cf2 55%,#7a28ce);border:5px solid #ffe600;border-radius:22px;padding:18px;margin:14px 0;box-shadow:0 9px 0 #03265f}.divBig{font-family:Impact,Arial Black;font-size:4rem;line-height:1;color:#fff200;text-shadow:3px 3px 0 #07305e}.goalbar{height:25px;background:#03265f;border:3px solid #fff;border-radius:99px;overflow:hidden}.goalfill{height:100%;background:linear-gradient(90deg,#24bd2d,#ffe600,#ff6a00,#e51b23)}.caption{font-weight:900;font-size:.82rem}.stTabs [data-baseweb="tab-list"]{background:#0647aa;border:3px solid #55efff;border-radius:15px;padding:5px}.stTabs [data-baseweb="tab"]{font-weight:1000}.stTabs [aria-selected="true"]{background:#e51b23!important;border:2px solid #ffe600;border-radius:10px}[data-testid="stPlotlyChart"]{border:3px solid #55efff;border-radius:18px;overflow:hidden}.mission{background:linear-gradient(90deg,#e51b23,#ff6a00);border:3px solid #ffe600;border-radius:15px;padding:13px;font-weight:900;margin:10px 0}.step{background:#0647aa;border:2px solid #55efff;border-radius:14px;padding:12px;margin:7px 0;font-weight:900}
</style>''',unsafe_allow_html=True)

st.markdown(f"<div class='tag'>💰 PERSONAL SAVINGS CONTROL CENTER • v{APP_VERSION}</div><div class='heroTitle'>HIGH-YIELD <span>SAVINGS</span> PROJECT</div>",unsafe_allow_html=True)
st.markdown("<div class='heroFrame'><img src='https://raw.githubusercontent.com/Grzesiak33/High-Yield-Savings-Project/main/assets/savings_hero.svg'></div>",unsafe_allow_html=True)
st.markdown("<div class='power'>⚡ MISSION: FILL THE 10% APY $1,000 ZONE — THEN KEEP THE SAVINGS POWER MOVING ⚡</div>",unsafe_allow_html=True)

c1,c2,c3,c4=st.columns([1.2,1,1,1])
with c1: amount=st.slider("💵 Save every paycheck",5,150,int(DEFAULT_DEPOSIT),5)
with c2: balance=st.number_input("💰 Current balance",min_value=0.,value=DEFAULT_BALANCE,step=5.,format="%.2f")
with c3: nxt=st.date_input("📅 Next paycheck",value=DEFAULT_NEXT_PAYCHECK)
with c4: freq=st.selectbox("🔁 Frequency",[7,14,15,30],index=1,format_func=lambda x:{7:"Weekly",14:"Every 2 weeks",15:"Twice monthly",30:"Monthly"}[x])

cfg=AccountConfig(MODEL_START,float(balance),nxt,int(freq)); frame=project(cfg,float(amount),MODEL_START+timedelta(days=3650)); hit=first_goal_date(frame)
thru=frame[frame.date<=hit] if hit else frame; interest=float(thru.interest.sum()); months=(hit-MODEL_START).days/30.4375 if hit else 0; progress=min(balance/1000,1)
div,detail=dividend_forecast(cfg,float(amount)); deps=detail[detail.deposit>0]; dep_dates=", ".join(x.strftime("%b %d") for x in deps.date.tolist()) or "None"; pre=balance+detail.deposit.sum()

st.markdown(f"<div class='divCard'><div style='font-weight:1000;color:#fff200'>💵 NEXT MONTHLY DIVIDEND POWER-UP • SEP 30 / OCT 1</div><div class='divBig'>≈ ${div:.2f}</div><div style='font-weight:900'>Starting balance ${balance:,.2f} + ${detail.deposit.sum():,.0f} scheduled deposits = ≈ ${pre:,.2f} before dividend.<br>Paycheck hits included: {dep_dates}</div></div>",unsafe_allow_html=True)
st.markdown(f"<div class='goalbar'><div class='goalfill' style='width:{progress*100:.2f}%'></div></div><div class='caption'>🔥 {progress*100:.1f}% OF THE $1,000 10% APY POWER ZONE FILLED</div>",unsafe_allow_html=True)

m1,m2,m3,m4,m5=st.columns(5); m1.metric("CURRENT",f"${balance:,.2f}"); m2.metric("PER CHECK",f"${amount}"); m3.metric("LEFT TO $1K",f"${max(1000-balance,0):,.2f}"); m4.metric("$1K DATE",hit.strftime("%b %d, %Y") if hit else "—"); m5.metric("INTEREST",f"${interest:,.2f}")
if hit: st.markdown(f"<div class='mission'>💥 At ${amount} every {freq} days, you hit $1,000 around {hit.strftime('%B %d, %Y')} — {months:.1f} months — with about ${interest:,.2f} generated by interest.</div>",unsafe_allow_html=True)

plan,divtab,race,after,hist=st.tabs(["💰 SAVINGS MISSION","💵 DIVIDEND POWER","🏁 DEPOSIT RACE","🚀 NEXT LEVEL","🧾 HISTORY"])
with plan:
    end=min(MODEL_START+timedelta(days=365*5),hit+timedelta(days=180) if hit else MODEL_START+timedelta(days=365*5)); p=frame[frame.date<=end]; d=p[p.deposit>0]
    f=go.Figure(); f.add_trace(go.Scatter(x=p.date,y=p.balance,mode="lines",name="Savings balance",line=dict(color=CYAN,width=6),fill="tozeroy",fillcolor="rgba(85,239,255,.2)")); f.add_trace(go.Scatter(x=d.date,y=d.balance,mode="markers",name="Paycheck power-up",marker=dict(color=ORANGE,size=10,line=dict(color=YELLOW,width=2)))); f.add_hline(y=1000,line_dash="dash",line_color=RED,line_width=5,annotation_text="$1,000 ZONE"); style(f); f.update_yaxes(tickprefix="$",title="Savings balance"); st.plotly_chart(f,use_container_width=True,config={"displayModeBar":False})
with divtab:
    x=detail.copy(); x["cumulative"]=x.accrual.cumsum(); f=go.Figure(); f.add_trace(go.Scatter(x=x.date,y=x.cumulative,mode="lines",name="Dividend building",line=dict(color=YELLOW,width=6),fill="tozeroy",fillcolor="rgba(255,230,0,.2)")); dd=x[x.deposit>0]; f.add_trace(go.Scatter(x=dd.date,y=dd.cumulative,mode="markers+text",name="Deposits",marker=dict(color=ORANGE,size=14),text=dd.deposit.map(lambda v:f"+${v:.0f}"),textposition="top center")); style(f,400); f.update_yaxes(tickprefix="$",tickformat=".2f"); st.plotly_chart(f,use_container_width=True,config={"displayModeBar":False}); a,b,c=st.columns(3); a.metric("EXPECTED DIVIDEND",f"≈ ${div:.2f}"); b.metric("DEPOSITS",f"${detail.deposit.sum():,.0f}"); c.metric("AFTER PAYOUT",f"${pre+div:,.2f}"); st.caption("Planning estimate using a 10% APY effective daily rate. Actual ORSA posting and rounding may differ slightly.")
with race:
    sc=scenarios(cfg,sorted(set([5,10,15,20,25,30,40,50,75,100,125,150,int(amount)]))); colors=[GREEN if a<25 else CYAN if a<50 else ORANGE if a<100 else RED for a in sc.Deposit]; f=go.Figure(go.Bar(x=sc.Deposit,y=sc.Months,marker=dict(color=colors,line=dict(color=YELLOW,width=1)),text=sc.Months.map(lambda v:f"{v:.1f} mo"),textposition="outside")); style(f); f.update_xaxes(title="Dollars saved each paycheck"); f.update_yaxes(title="Months to $1,000"); st.plotly_chart(f,use_container_width=True,config={"displayModeBar":False}); show=sc.copy(); show.Deposit=show.Deposit.map(lambda v:f"${v}"); show.Interest=show.Interest.map(lambda v:f"${v:,.2f}"); st.dataframe(show,hide_index=True,use_container_width=True)
with after:
    a,b=st.columns(2)
    with a: nextapy=st.number_input("Next savings account APY (%)",0.,20.,4.5,.1)
    with b: goal=st.number_input("Total cash savings goal",1000.,50000.,5000.,500.)
    s=two_bucket(cfg,float(amount),nextapy/100,MODEL_START+timedelta(days=365*12)); oh=s[s.ORSA>=1000]; gh=s[s.Total>=goal]; od=None if oh.empty else oh.iloc[0].date; gd=None if gh.empty else gh.iloc[0].date
    q1,q2,q3,q4=st.columns(4); q1.metric("ORSA POWER ZONE","$1,000"); q2.metric("REDIRECT",od.strftime("%b %d, %Y") if od else "—"); q3.metric("TOTAL GOAL",f"${goal:,.0f}"); q4.metric("GOAL DATE",gd.strftime("%b %d, %Y") if gd else "—")
    st.markdown("<div class='step'>1️⃣ Fill ORSA's 10% APY zone.</div><div class='step'>2️⃣ Redirect new paycheck savings to Bucket #2.</div><div class='step'>3️⃣ Keep the automatic savings streak alive.</div>",unsafe_allow_html=True)
    z=s[s.date<=min(MODEL_START+timedelta(days=365*6),gd+timedelta(days=120) if gd else MODEL_START+timedelta(days=365*6))]; f=go.Figure(); f.add_trace(go.Scatter(x=z.date,y=z.ORSA,stackgroup="one",name="ORSA",line=dict(color=CYAN,width=3))); f.add_trace(go.Scatter(x=z.date,y=z["Bucket #2"],stackgroup="one",name="Bucket #2",line=dict(color=ORANGE,width=3))); f.add_hline(y=goal,line_dash="dot",line_color=YELLOW,line_width=4); style(f,470); f.update_yaxes(tickprefix="$",title="Total savings"); st.plotly_chart(f,use_container_width=True,config={"displayModeBar":False})
with hist:
    path=Path("data/savings_transactions.csv")
    if path.exists():
        h=pd.read_csv(path); h["date"]=pd.to_datetime(h.date); st.dataframe(h.sort_values("date",ascending=False),hide_index=True,use_container_width=True)
    else: st.info("Savings history file not found.")
st.markdown(f"<div class='caption' style='text-align:center;margin-top:20px'>HIGH-YIELD SAVINGS PROJECT v{APP_VERSION} • SAVE • GROW • LEVEL UP</div>",unsafe_allow_html=True)
