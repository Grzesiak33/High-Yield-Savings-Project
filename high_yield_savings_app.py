from __future__ import annotations
from dataclasses import dataclass
from datetime import date,timedelta
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP_VERSION="1.2.0"; MODEL_START=date(2026,9,1); DEFAULT_BALANCE=20.71; DEFAULT_DEPOSIT=10.; DEFAULT_NEXT_PAYCHECK=date(2026,9,11)
CYAN="#00c8f0"; YELLOW="#ffc400"; GREEN="#55d319"; ORANGE="#ff6a00"; RED="#ef2a14"; PANEL="#07111e"
@dataclass(frozen=True)
class AccountConfig:
    start_date:date; current_balance:float; next_paycheck_date:date; frequency_days:int; high_apy:float=.10; high_limit:float=1000.; excess_apy:float=.001

def rate(a): return (1+a)**(1/365)-1
def interest(b,c): return min(b,c.high_limit)*rate(c.high_apy)+max(b-c.high_limit,0)*rate(c.excess_apy)
def project(c,a,end):
    d=c.start_date;b=c.current_balance;n=c.next_paycheck_date;r=[]
    while d<=end:
        dep=0.
        if d==n: dep=float(a);b+=dep;n+=timedelta(days=c.frequency_days)
        i=interest(b,c);b+=i;r.append({"date":d,"balance":b,"deposit":dep,"interest":i});d+=timedelta(days=1)
    return pd.DataFrame(r)
def goal_date(f,g=1000.):
    x=f[f.balance>=g];return None if x.empty else x.iloc[0].date
def dividend(c,a,payout=date(2026,9,30)):
    d=c.start_date;b=c.current_balance;n=c.next_paycheck_date;r=[];total=0.
    while d<=payout:
        dep=0.
        if d==n:dep=float(a);b+=dep;n+=timedelta(days=c.frequency_days)
        i=interest(b,c);total+=i;r.append({"date":d,"balance":b,"deposit":dep,"accrual":i});d+=timedelta(days=1)
    return total,pd.DataFrame(r)
def scenarios(c,amounts):
    out=[]
    for a in amounts:
        f=project(c,a,c.start_date+timedelta(days=3650));h=goal_date(f)
        if h:
            x=f[f.date<=h];out.append({"Deposit":a,"Goal Date":h.strftime("%b %d, %Y"),"Months":round((h-c.start_date).days/30.4375,1),"Interest":x.interest.sum()})
    return pd.DataFrame(out)
def two_bucket(c,a,apy,end):
    d=c.start_date;o=c.current_balance;b2=0.;n=c.next_paycheck_date;r=[]
    while d<=end:
        if d==n:
            room=max(1000-o,0);x=min(a,room);o+=x;b2+=max(a-x,0);n+=timedelta(days=c.frequency_days)
        o+=interest(o,c);b2+=b2*rate(apy)
        if o>1000:b2+=o-1000;o=1000
        r.append({"date":d,"ORSA":o,"Bucket #2":b2,"Total":o+b2});d+=timedelta(days=1)
    return pd.DataFrame(r)
def style(f,h=420):
    f.update_layout(height=h,margin=dict(l=10,r=10,t=35,b=10),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="#07111e",font_color="white",xaxis=dict(gridcolor="#23415d"),yaxis=dict(gridcolor="#23415d"),legend=dict(orientation="h",y=1.08),hovermode="x unified")

st.set_page_config(page_title="High-Yield Savings Project",page_icon="💰",layout="wide",initial_sidebar_state="collapsed")
st.markdown('''<style>
.stApp{background:#030914;color:#fff}.block-container{max-width:1500px;padding:.3rem .8rem 3rem}header,footer{visibility:hidden}.top{font-family:Impact,Arial Black,sans-serif;font-size:clamp(1.7rem,4vw,3.2rem);font-style:italic}.top b{color:#00c8f0}.hero{border:2px solid #263b51;border-radius:18px;padding:5px;background:#07111e;box-shadow:0 10px 28px #000}.hero img{width:100%;display:block;border-radius:13px}.mission{margin:12px 0;background:linear-gradient(90deg,#07111e,#10233a);border:1px solid #00c8f0;border-left:6px solid #ffc400;border-radius:12px;padding:13px 16px;font-weight:900}.goalbar{height:18px;background:#2d3035;border-radius:99px;overflow:hidden}.goalfill{height:100%;background:linear-gradient(90deg,#00c8f0,#00b5d9)}.caption{font-size:.8rem;font-weight:900;color:#dce6ef}.divCard{background:#07111e;border:1px solid #29455e;border-radius:16px;padding:17px;margin:12px 0}.divBig{font-family:Impact,Arial Black;font-size:3.6rem;color:#55d319;line-height:1}.stTabs [data-baseweb="tab-list"]{background:#050b14;border-bottom:2px solid #23384c;gap:5px}.stTabs [data-baseweb="tab"]{font-weight:900;color:#fff}.stTabs [aria-selected="true"]{color:#ffc400!important;border-bottom:4px solid #ffc400}[data-testid="stMetric"]{background:#07111e;border:1px solid #29455e;border-radius:14px;padding:13px}[data-testid="stMetricLabel"]{color:#d9e4ee!important;font-weight:900}[data-testid="stMetricValue"]{color:#00c8f0!important;font-weight:1000}[data-testid="stPlotlyChart"]{border:1px solid #29455e;border-radius:15px;overflow:hidden}.step{background:#07111e;border:1px solid #29455e;border-left:5px solid #00c8f0;border-radius:10px;padding:11px;margin:7px 0;font-weight:850}.stButton button{background:#ef2a14;color:#fff;border:1px solid #ff6a00}
</style>''',unsafe_allow_html=True)
st.markdown(f"<div class='top'>🐷 HIGH-YIELD <b>SAVINGS PROJECT</b> <span style='font-size:.35em;color:#7d93a8'>v{APP_VERSION}</span></div>",unsafe_allow_html=True)
st.markdown("<div class='hero'><img src='https://raw.githubusercontent.com/Grzesiak33/High-Yield-Savings-Project/main/assets/savings_hero.png'></div>",unsafe_allow_html=True)
st.markdown("<div class='mission'>⚡ SAVE TODAY. BUILD FREEDOM. &nbsp; Every automatic deposit moves the $1,000 high-yield target closer.</div>",unsafe_allow_html=True)

c1,c2,c3,c4=st.columns([1.2,1,1,1])
with c1: amount=st.slider("Automatic savings / paycheck",5,150,int(DEFAULT_DEPOSIT),5)
with c2: balance=st.number_input("Current balance",min_value=0.,value=DEFAULT_BALANCE,step=5.,format="%.2f")
with c3: nxt=st.date_input("Next deposit",value=DEFAULT_NEXT_PAYCHECK)
with c4: freq=st.selectbox("Deposit frequency",[7,14,15,30],index=1,format_func=lambda x:{7:"Weekly",14:"Every 2 weeks",15:"Twice monthly",30:"Monthly"}[x])
cfg=AccountConfig(MODEL_START,float(balance),nxt,int(freq));frame=project(cfg,float(amount),MODEL_START+timedelta(days=3650));hit=goal_date(frame);thru=frame[frame.date<=hit] if hit else frame;earned=float(thru.interest.sum());months=(hit-MODEL_START).days/30.4375 if hit else 0;progress=min(balance/1000,1);div,detail=dividend(cfg,float(amount));pre=balance+detail.deposit.sum();dates=", ".join(x.strftime("%b %d") for x in detail[detail.deposit>0].date.tolist()) or "None"
st.markdown(f"<div class='goalbar'><div class='goalfill' style='width:{progress*100:.2f}%'></div></div><div class='caption'>{progress*100:.1f}% FILLED • ${max(1000-balance,0):,.2f} TO GO • 10% APY TARGET ZONE</div>",unsafe_allow_html=True)
m1,m2,m3,m4,m5=st.columns(5);m1.metric("CURRENT",f"${balance:,.2f}");m2.metric("PER CHECK",f"${amount}");m3.metric("NEXT DIVIDEND",f"≈ ${div:.2f}");m4.metric("PROJECTED $1K",hit.strftime("%b %d, %Y") if hit else "—");m5.metric("INTEREST TO $1K",f"${earned:,.2f}")
st.markdown(f"<div class='divCard'><b style='color:#ffc400'>NEXT MONTHLY DIVIDEND (EST.)</b><div class='divBig'>≈ ${div:.2f}</div><b>September deposits: ${detail.deposit.sum():,.0f} ({dates}) • projected pre-dividend balance: ${pre:,.2f}</b></div>",unsafe_allow_html=True)

plan,divtab,race,after,hist=st.tabs(["🏠 DASHBOARD","💲 DIVIDENDS","📈 PROJECTIONS","🛡 STRATEGY","◷ HISTORY"])
with plan:
    end=min(MODEL_START+timedelta(days=365*5),hit+timedelta(days=180) if hit else MODEL_START+timedelta(days=365*5));p=frame[frame.date<=end];d=p[p.deposit>0];f=go.Figure();f.add_trace(go.Scatter(x=p.date,y=p.balance,mode="lines",name="Balance (10% APY)",line=dict(color=CYAN,width=5)));f.add_trace(go.Scatter(x=d.date,y=d.balance,mode="markers",name="Automatic deposits",marker=dict(color=ORANGE,size=8)));f.add_hline(y=1000,line_dash="dash",line_color=YELLOW,annotation_text="$1,000 GOAL");style(f);f.update_yaxes(tickprefix="$",title="Savings");st.plotly_chart(f,use_container_width=True,config={"displayModeBar":False});st.markdown(f"<div class='mission'>On this plan: <b>${amount} every {freq} days</b> → $1,000 around <b>{hit.strftime('%B %d, %Y') if hit else 'beyond model'}</b>{f' • {months:.1f} months' if hit else ''}.</div>",unsafe_allow_html=True)
with divtab:
    x=detail.copy();x["cumulative"]=x.accrual.cumsum();f=go.Figure(go.Scatter(x=x.date,y=x.cumulative,mode="lines",name="Dividend accrued",line=dict(color=GREEN,width=5),fill="tozeroy",fillcolor="rgba(85,211,25,.15)"));style(f,390);f.update_yaxes(tickprefix="$",tickformat=".2f");st.plotly_chart(f,use_container_width=True,config={"displayModeBar":False});a,b,c=st.columns(3);a.metric("EXPECTED PAYOUT",f"≈ ${div:.2f}");b.metric("DEPOSITS BEFORE PAYOUT",f"${detail.deposit.sum():,.0f}");c.metric("EST. AFTER PAYOUT",f"${pre+div:,.2f}");st.caption("Planning estimate using a 10% APY effective daily rate. Actual posting and rounding can differ slightly.")
with race:
    sc=scenarios(cfg,sorted(set([5,10,15,20,25,30,40,50,75,100,125,150,int(amount)])));f=go.Figure(go.Bar(x=sc.Deposit,y=sc.Months,marker=dict(color=[GREEN if a<25 else CYAN if a<50 else ORANGE if a<100 else RED for a in sc.Deposit]),text=sc.Months.map(lambda v:f"{v:.1f} mo"),textposition="outside"));style(f);f.update_xaxes(title="Saved each paycheck ($)");f.update_yaxes(title="Months to $1,000");st.plotly_chart(f,use_container_width=True,config={"displayModeBar":False});show=sc.copy();show.Deposit=show.Deposit.map(lambda v:f"${v}");show.Interest=show.Interest.map(lambda v:f"${v:,.2f}");st.dataframe(show,hide_index=True,use_container_width=True)
with after:
    a,b=st.columns(2)
    with a: nextapy=st.number_input("Next savings account APY (%)",0.,20.,4.5,.1)
    with b: totalgoal=st.number_input("Total cash savings goal",1000.,50000.,5000.,500.)
    s=two_bucket(cfg,float(amount),nextapy/100,MODEL_START+timedelta(days=365*12));oh=s[s.ORSA>=1000];gh=s[s.Total>=totalgoal];od=None if oh.empty else oh.iloc[0].date;gd=None if gh.empty else gh.iloc[0].date;q1,q2,q3=st.columns(3);q1.metric("ORSA TARGET","$1,000");q2.metric("REDIRECT START",od.strftime("%b %d, %Y") if od else "—");q3.metric("TOTAL GOAL DATE",gd.strftime("%b %d, %Y") if gd else "—");st.markdown("<div class='step'>1. Fill the ORSA 10% APY zone.</div><div class='step'>2. Redirect future paycheck savings to Bucket #2.</div><div class='step'>3. Keep the automatic saving behavior running.</div>",unsafe_allow_html=True)
with hist:
    p=Path("data/savings_transactions.csv")
    if p.exists():
        h=pd.read_csv(p);h["date"]=pd.to_datetime(h.date);st.dataframe(h.sort_values("date",ascending=False),hide_index=True,use_container_width=True)
    else:st.info("Savings history file not found.")
st.markdown(f"<div class='caption' style='text-align:center;margin-top:20px'>HIGH-YIELD SAVINGS PROJECT v{APP_VERSION} • DISCIPLINE TODAY. FREEDOM TOMORROW.</div>",unsafe_allow_html=True)