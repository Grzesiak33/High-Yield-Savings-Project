from __future__ import annotations
from dataclasses import dataclass
from datetime import date,timedelta
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP_VERSION="1.3.0"; MODEL_START=date(2026,9,1); DEFAULT_BALANCE=20.71; DEFAULT_DEPOSIT=10.; DEFAULT_NEXT_PAYCHECK=date(2026,9,11)
CYAN="#00e5ff"; YELLOW="#ffe600"; GREEN="#65ff36"; ORANGE="#ff7a00"; RED="#ff304f"; PURPLE="#b32cff"; PINK="#ff3fd2"; BLUE="#168cff"; PANEL="#07111e"
@dataclass(frozen=True)
class AccountConfig:
    start_date:date; current_balance:float; next_paycheck_date:date; frequency_days:int; high_apy:float=.10; high_limit:float=1000.; excess_apy:float=.001

def rate(a): return (1+a)**(1/365)-1
def interest(b,c): return min(b,c.high_limit)*rate(c.high_apy)+max(b-c.high_limit,0)*rate(c.excess_apy)
def project(c,a,end):
    d=c.start_date;b=c.current_balance;n=c.next_paycheck_date;r=[]
    while d<=end:
        dep=0.
        if d==n:dep=float(a);b+=dep;n+=timedelta(days=c.frequency_days)
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
            x=f[f.date<=h];out.append({"Deposit":a,"Goal Date":h,"Months":round((h-c.start_date).days/30.4375,1),"Interest":x.interest.sum()})
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

def money(v):return f"${v:,.2f}"

st.set_page_config(page_title="High-Yield Savings Project",page_icon="💰",layout="wide",initial_sidebar_state="collapsed")
st.markdown('''<style>
.stApp{background:radial-gradient(circle at 45% -15%,#102c62 0,#050b18 38%,#02050c 78%);color:#fff}.block-container{max-width:1500px;padding:.3rem .8rem 3rem}header,footer{visibility:hidden}.top{font-family:Impact,Arial Black,sans-serif;font-size:clamp(1.7rem,4vw,3.2rem);font-style:italic}.top b{background:linear-gradient(90deg,#00e5ff,#65ff36,#ffe600,#ff7a00,#ff3fd2);-webkit-background-clip:text;color:transparent}.hero{border:2px solid #304d69;border-radius:18px;padding:5px;background:#07111e;box-shadow:0 10px 28px #000}.hero img{width:100%;display:block;border-radius:13px}.mission{margin:12px 0;background:linear-gradient(90deg,#09213d,#132b4b,#27143c);border:1px solid #00e5ff;border-left:7px solid #ffe600;border-radius:12px;padding:13px 16px;font-weight:900}.goalbar{height:21px;background:#292d34;border:2px solid #46576a;border-radius:99px;overflow:hidden}.goalfill{height:100%;background:linear-gradient(90deg,#00e5ff,#65ff36,#ffe600,#ff7a00,#ff304f)}.caption{font-size:.82rem;font-weight:900;color:#dce6ef}.bigCard{background:linear-gradient(135deg,#08182a,#102540 58%,#281238);border:2px solid #294f72;border-radius:18px;padding:17px;margin:12px 0}.bigNumber{font-family:Impact,Arial Black;font-size:clamp(2.5rem,6vw,4.7rem);color:#65ff36;line-height:1;text-shadow:2px 2px 0 #0b4320}.stTabs [data-baseweb="tab-list"]{background:#050b14;border-bottom:2px solid #23384c;gap:5px}.stTabs [data-baseweb="tab"]{font-weight:900;color:#fff}.stTabs [aria-selected="true"]{color:#ffe600!important;border-bottom:4px solid #ffe600}[data-testid="stMetric"]{background:linear-gradient(145deg,#081522,#0b2036);border:1px solid #315473;border-radius:14px;padding:13px}[data-testid="stMetricLabel"]{color:#d9e4ee!important;font-weight:900}[data-testid="stMetricValue"]{color:#00e5ff!important;font-weight:1000}[data-testid="stPlotlyChart"]{border:1px solid #29455e;border-radius:15px;overflow:hidden}.step{background:#07111e;border:1px solid #29455e;border-left:5px solid #00e5ff;border-radius:10px;padding:11px;margin:7px 0;font-weight:850}.insight{background:linear-gradient(90deg,#10253e,#1d1641);border:1px solid #b32cff;border-radius:13px;padding:12px;margin:8px 0;font-weight:850}.stButton button{background:linear-gradient(90deg,#ff304f,#ff7a00);color:#fff;border:2px solid #ffe600;font-weight:900}.stSlider [data-baseweb="slider"]>div>div{background:#00e5ff}.stProgress>div>div>div>div{background:linear-gradient(90deg,#00e5ff,#65ff36,#ffe600,#ff7a00)}
</style>''',unsafe_allow_html=True)
st.markdown(f"<div class='top'>🐷 HIGH-YIELD <b>SAVINGS PROJECT</b> <span style='font-size:.35em;color:#7d93a8'>v{APP_VERSION}</span></div>",unsafe_allow_html=True)
st.markdown("<div class='hero'><img src='https://raw.githubusercontent.com/Grzesiak33/High-Yield-Savings-Project/main/assets/savings_hero.png'></div>",unsafe_allow_html=True)
st.markdown("<div class='mission'>⚡ YOUR MONEY CONTROL PANEL — change any setting below and every projection, goal date and insight recalculates instantly.</div>",unsafe_allow_html=True)

with st.container(border=True):
    st.markdown("### 🎮 CONTROL THE PLAN")
    c1,c2,c3,c4=st.columns([1.25,1,1,1])
    with c1: amount=st.slider("💵 Automatic savings each paycheck",5,250,int(DEFAULT_DEPOSIT),5,help="Drag this and watch the entire dashboard recalculate.")
    with c2: balance=st.number_input("💰 Current savings balance",min_value=0.,value=DEFAULT_BALANCE,step=5.,format="%.2f")
    with c3: nxt=st.date_input("📅 Next automatic deposit",value=DEFAULT_NEXT_PAYCHECK)
    with c4: freq=st.selectbox("🔁 Deposit schedule",[7,14,15,30],index=1,format_func=lambda x:{7:"Every week",14:"Every 2 weeks",15:"Every 15 days",30:"Every month"}[x])

cfg=AccountConfig(MODEL_START,float(balance),nxt,int(freq));frame=project(cfg,float(amount),MODEL_START+timedelta(days=3650));hit=goal_date(frame);thru=frame[frame.date<=hit] if hit else frame;earned=float(thru.interest.sum());months=(hit-MODEL_START).days/30.4375 if hit else 0;days=(hit-MODEL_START).days if hit else 0;progress=min(balance/1000,1);div,detail=dividend(cfg,float(amount));pre=balance+detail.deposit.sum();dates=", ".join(x.strftime("%b %d") for x in detail[detail.deposit>0].date.tolist()) or "None";remaining=max(1000-balance,0)
base_cfg=AccountConfig(MODEL_START,float(balance),nxt,int(freq));base10=project(base_cfg,10,MODEL_START+timedelta(days=3650));base_hit=goal_date(base10);days_saved=(base_hit-hit).days if hit and base_hit and amount>10 else 0

st.markdown(f"<div class='goalbar'><div class='goalfill' style='width:{progress*100:.2f}%'></div></div><div class='caption'>🏆 {progress*100:.1f}% OF THE $1,000 POWER ZONE • {money(remaining)} LEFT • FIRST $1,000 MODELED AT 10% APY</div>",unsafe_allow_html=True)

st.markdown("### 🔥 LIVE SCOREBOARD")
a,b,c,d=st.columns(4);a.metric("💰 SAVED NOW",money(balance),help="Your editable current balance.");b.metric("🎯 LEFT TO $1,000",money(remaining),help="How much remains before interest and future deposits.");c.metric("💵 NEXT DIVIDEND",f"≈ {money(div)}",help="Estimated September dividend using the current plan.");d.metric("🏁 $1,000 DATE",hit.strftime("%b %d, %Y") if hit else "Beyond model",help="Changes instantly with your deposit amount and schedule.")

st.markdown(f"<div class='bigCard'><b style='color:#ffe600'>💥 NEXT PAYOUT CHALLENGE</b><div class='bigNumber'>≈ {money(div)}</div><b>{money(detail.deposit.sum())} of automatic deposits are scheduled before payout ({dates}). Projected balance before dividend: {money(pre)}.</b></div>",unsafe_allow_html=True)

st.markdown("### 🚀 WHAT IF I SAVE MORE?")
quick=[10,20,30,50,75,100]
cols=st.columns(6)
for col,val in zip(cols,quick):
    f2=project(cfg,val,MODEL_START+timedelta(days=3650));h2=goal_date(f2);label=h2.strftime("%b %Y") if h2 else "—";col.metric(f"${val}/CHECK",label,help=f"Projected month you reach $1,000 saving ${val} each paycheck.")
if days_saved>0: st.markdown(f"<div class='insight'>⚡ Your current ${amount}/check plan reaches $1,000 about <b>{days_saved} days sooner</b> than staying at $10/check.</div>",unsafe_allow_html=True)
elif amount==10: st.markdown("<div class='insight'>💡 Try dragging the paycheck slider above $10. The goal date, dividend and projections update immediately.</div>",unsafe_allow_html=True)

st.markdown("### 🎯 PERSONAL CHALLENGE")
challenge=st.slider("Choose a target date: how fast do you WANT to reach $1,000?",3,48,12,1,format="%d months")
challenge_date=MODEL_START+timedelta(days=round(challenge*30.4375));candidates=scenarios(cfg,range(5,501,5));possible=candidates[candidates["Goal Date"]<=challenge_date];needed=None if possible.empty else int(possible.iloc[0].Deposit)
if needed: st.success(f"To target $1,000 in about {challenge} months, save roughly ${needed} per paycheck on this schedule. That's ${max(needed-amount,0)} more than your current ${amount} setting." if needed>amount else f"Your current ${amount}/check plan is already strong enough for the {challenge}-month challenge.")
else: st.warning("That target is outside the current calculator range. Increase the timeline or savings amount.")

plan,divtab,race,after,hist=st.tabs(["📈 GROWTH","💲 DIVIDEND","🏁 COMPARE PLANS","🛡 AFTER $1K","◷ REAL HISTORY"])
with plan:
    horizon=st.radio("Chart horizon",["To $1,000","1 year","2 years","5 years"],horizontal=True)
    ends={"1 year":MODEL_START+timedelta(days=365),"2 years":MODEL_START+timedelta(days=730),"5 years":MODEL_START+timedelta(days=1825)};end=hit+timedelta(days=30) if horizon=="To $1,000" and hit else ends.get(horizon,MODEL_START+timedelta(days=365));p=frame[frame.date<=end];dd=p[p.deposit>0];f=go.Figure();f.add_trace(go.Scatter(x=p.date,y=p.balance,mode="lines",name="Savings balance",line=dict(color=CYAN,width=5),fill="tozeroy",fillcolor="rgba(0,229,255,.10)"));f.add_trace(go.Scatter(x=dd.date,y=dd.balance,mode="markers",name="Deposits",marker=dict(color=ORANGE,size=8)));f.add_hline(y=1000,line_dash="dash",line_color=YELLOW,annotation_text="$1,000");style(f);f.update_yaxes(tickprefix="$",title="Savings");st.plotly_chart(f,use_container_width=True,config={"displayModeBar":False});x1,x2,x3=st.columns(3);x1.metric("TIME TO $1K",f"{months:.1f} months" if hit else "—");x2.metric("INTEREST TO $1K",money(earned));x3.metric("AUTOMATIC DEPOSITS",str(int(thru.deposit.gt(0).sum())))
with divtab:
    x=detail.copy();x["cumulative"]=x.accrual.cumsum();f=go.Figure();f.add_trace(go.Scatter(x=x.date,y=x.cumulative,mode="lines+markers",name="Dividend building",line=dict(color=GREEN,width=5),marker=dict(color=YELLOW,size=5),fill="tozeroy",fillcolor="rgba(101,255,54,.13)"));style(f,390);f.update_yaxes(tickprefix="$",tickformat=".2f");st.plotly_chart(f,use_container_width=True,config={"displayModeBar":False});a,b,c=st.columns(3);a.metric("EST. PAYOUT",money(div));b.metric("DEPOSITS INCLUDED",money(detail.deposit.sum()));c.metric("EST. AFTER PAYOUT",money(pre+div));st.caption("Planning estimate. Actual ORSA posting, daily-balance method, rate changes and rounding can change the result.")
with race:
    custom=st.slider("Compare up to this amount per paycheck",25,250,max(100,int(amount)),5);vals=sorted(set([5,10,15,20,25,30,40,50,75,100,125,150,200,250,int(amount)]));vals=[v for v in vals if v<=custom];sc=scenarios(cfg,vals);f=go.Figure(go.Bar(x=sc.Deposit,y=sc.Months,marker=dict(color=[GREEN if a<=20 else CYAN if a<=50 else YELLOW if a<=100 else ORANGE if a<=150 else PINK for a in sc.Deposit]),text=sc.Months.map(lambda v:f"{v:.1f} mo"),textposition="outside"));style(f);f.update_xaxes(title="Saved each paycheck ($)");f.update_yaxes(title="Months to $1,000");st.plotly_chart(f,use_container_width=True,config={"displayModeBar":False});show=sc.copy();show["Goal Date"]=show["Goal Date"].map(lambda v:v.strftime("%b %d, %Y"));show.Deposit=show.Deposit.map(lambda v:f"${v}");show.Interest=show.Interest.map(money);st.dataframe(show,hide_index=True,use_container_width=True)
with after:
    a,b=st.columns(2)
    with a:nextapy=st.slider("APY for your next savings bucket",0.,10.,4.5,.1,format="%.1f%%")
    with b:totalgoal=st.number_input("Next total savings goal",1000.,50000.,5000.,500.)
    s=two_bucket(cfg,float(amount),nextapy/100,MODEL_START+timedelta(days=365*12));oh=s[s.ORSA>=1000];gh=s[s.Total>=totalgoal];od=None if oh.empty else oh.iloc[0].date;gd=None if gh.empty else gh.iloc[0].date;q1,q2,q3=st.columns(3);q1.metric("ORSA TARGET","$1,000");q2.metric("REDIRECT DATE",od.strftime("%b %d, %Y") if od else "—");q3.metric("NEXT GOAL DATE",gd.strftime("%b %d, %Y") if gd else "—");st.markdown("<div class='step'>1️⃣ Fill the first $1,000 high-yield zone.</div><div class='step'>2️⃣ Redirect future automatic savings to the next competitive savings account.</div><div class='step'>3️⃣ Keep the habit automatic and let both buckets compound.</div>",unsafe_allow_html=True)
with hist:
    p=Path("data/savings_transactions.csv")
    if p.exists():
        h=pd.read_csv(p);h["date"]=pd.to_datetime(h.date);h=h.sort_values("date");divs=h[h.type.str.lower().eq("dividend")].copy();a,b,c=st.columns(3);a.metric("RECORDED BALANCE",money(float(h.iloc[-1].balance)));b.metric("DIVIDENDS RECORDED",money(float(divs.amount.sum())));c.metric("LAST REPORTED APY",f"{float(h.iloc[-1].reported_apy):.2f}%");st.dataframe(h.sort_values("date",ascending=False),hide_index=True,use_container_width=True)
    else:st.info("Savings history file not found.")
st.markdown(f"<div class='caption' style='text-align:center;margin-top:20px'>HIGH-YIELD SAVINGS PROJECT v{APP_VERSION} • EVERY CONTROL DOES SOMETHING • EVERY NUMBER HAS A PURPOSE</div>",unsafe_allow_html=True)