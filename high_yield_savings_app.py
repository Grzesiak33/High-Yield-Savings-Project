from __future__ import annotations
from dataclasses import dataclass
from datetime import date,timedelta
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP_VERSION="1.4.0"; START=date(2026,9,1); BAL=20.71; DEP=10.; NEXT=date(2026,9,11)
CYAN="#00e5ff";YELLOW="#ffe600";GREEN="#65ff36";ORANGE="#ff7a00";RED="#ff304f";PINK="#ff3fd2";PURPLE="#b32cff";BG="#07111e"

@dataclass(frozen=True)
class Cfg:
    start:date; balance:float; next_dep:date; freq:int; apy:float=.10; cap:float=1000.; excess:.001=.001

def dr(a): return (1+a)**(1/365)-1
def intr(b,c): return min(b,c.cap)*dr(c.apy)+max(b-c.cap,0)*dr(c.excess)
def proj(c,a,end):
    d=c.start;b=c.balance;n=c.next_dep;r=[]
    while d<=end:
        dep=0.
        if d==n: dep=float(a);b+=dep;n+=timedelta(days=c.freq)
        i=intr(b,c);b+=i;r.append({"date":d,"balance":b,"deposit":dep,"interest":i});d+=timedelta(days=1)
    return pd.DataFrame(r)
def hit(df,g=1000.):
    x=df[df.balance>=g];return None if x.empty else x.iloc[0].date
def div_forecast(c,a,payout=date(2026,9,30)):
    d=c.start;b=c.balance;n=c.next_dep;r=[];tot=0.
    while d<=payout:
        dep=0.
        if d==n:dep=float(a);b+=dep;n+=timedelta(days=c.freq)
        i=intr(b,c);tot+=i;r.append({"date":d,"balance":b,"deposit":dep,"accrual":i});d+=timedelta(days=1)
    return tot,pd.DataFrame(r)
def scenarios(c,vals):
    out=[]
    for a in vals:
        f=proj(c,a,c.start+timedelta(days=3650));h=hit(f)
        if h:
            x=f[f.date<=h];out.append({"Deposit":a,"Goal Date":h,"Months":round((h-c.start).days/30.4375,1),"Interest":x.interest.sum()})
    return pd.DataFrame(out)
def two_bucket(c,a,apy,end):
    d=c.start;o=c.balance;b2=0.;n=c.next_dep;r=[]
    while d<=end:
        if d==n:
            room=max(c.cap-o,0);x=min(a,room);o+=x;b2+=max(a-x,0);n+=timedelta(days=c.freq)
        o+=intr(o,c);b2+=b2*dr(apy)
        if o>c.cap:b2+=o-c.cap;o=c.cap
        r.append({"date":d,"ORSA":o,"Bucket #2":b2,"Total":o+b2});d+=timedelta(days=1)
    return pd.DataFrame(r)
def style(fig,h=420):
    fig.update_layout(height=h,margin=dict(l=10,r=10,t=35,b=10),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor=BG,font_color="white",xaxis=dict(gridcolor="#23415d"),yaxis=dict(gridcolor="#23415d"),legend=dict(orientation="h",y=1.08),hovermode="x unified")
def money(v):return f"${v:,.2f}"

st.set_page_config(page_title="High-Yield Savings Project",page_icon="💰",layout="wide",initial_sidebar_state="collapsed")
st.markdown('''<style>
.stApp{background:radial-gradient(circle at 45% -15%,#102c62 0,#050b18 38%,#02050c 78%);color:white}.block-container{max-width:1500px;padding:.3rem .8rem 3rem}header,footer{visibility:hidden}.top{font-family:Impact,Arial Black,sans-serif;font-size:clamp(1.8rem,4vw,3.2rem);font-style:italic}.top b{background:linear-gradient(90deg,#00e5ff,#65ff36,#ffe600,#ff7a00,#ff3fd2);-webkit-background-clip:text;color:transparent}.hero{border:2px solid #304d69;border-radius:18px;padding:5px;background:#07111e}.hero img{width:100%;display:block;border-radius:13px}.mission{margin:12px 0;background:linear-gradient(90deg,#09213d,#132b4b,#27143c);border:1px solid #00e5ff;border-left:7px solid #ffe600;border-radius:12px;padding:13px 16px;font-weight:900}.goalbar{height:21px;background:#292d34;border:2px solid #46576a;border-radius:99px;overflow:hidden}.goalfill{height:100%;background:linear-gradient(90deg,#00e5ff,#65ff36,#ffe600,#ff7a00,#ff304f)}.caption{font-size:.82rem;font-weight:900;color:#dce6ef}.panel{background:linear-gradient(135deg,#08182a,#102540 58%,#281238);border:2px solid #294f72;border-radius:18px;padding:16px;margin:10px 0}.big{font-family:Impact,Arial Black;font-size:3.5rem;color:#65ff36;line-height:1}.stButton button{width:100%;min-height:86px;background:linear-gradient(145deg,#0b2036,#102a47);color:#fff;border:2px solid #00e5ff;border-radius:16px;font-weight:1000;font-size:1rem}.stButton button:hover{border-color:#ffe600;color:#ffe600;box-shadow:0 0 0 2px #ff7a00 inset}.stTabs [data-baseweb="tab-list"]{background:#050b14;border-bottom:2px solid #23384c}.stTabs [aria-selected="true"]{color:#ffe600!important;border-bottom:4px solid #ffe600}[data-testid="stPlotlyChart"]{border:1px solid #29455e;border-radius:15px;overflow:hidden}.step{background:#07111e;border:1px solid #29455e;border-left:5px solid #00e5ff;border-radius:10px;padding:11px;margin:7px 0;font-weight:850}.insight{background:linear-gradient(90deg,#10253e,#1d1641);border:1px solid #b32cff;border-radius:13px;padding:12px;margin:8px 0;font-weight:850}
</style>''',unsafe_allow_html=True)

if "focus" not in st.session_state: st.session_state.focus="none"

def focus(name): st.session_state.focus=name

st.markdown(f"<div class='top'>🐷 HIGH-YIELD <b>SAVINGS PROJECT</b> <span style='font-size:.35em;color:#7d93a8'>v{APP_VERSION}</span></div>",unsafe_allow_html=True)
st.markdown("<div class='hero'><img src='https://raw.githubusercontent.com/Grzesiak33/High-Yield-Savings-Project/main/assets/savings_hero.png'></div>",unsafe_allow_html=True)
st.markdown("<div class='mission'>⚡ TAP THE DASHBOARD. Every major card below is now a real action — it opens useful detail or a calculator.</div>",unsafe_allow_html=True)

with st.container(border=True):
    st.markdown("### 🎮 CONTROL THE PLAN")
    c1,c2,c3,c4=st.columns([1.3,1,1,1])
    with c1: amount=st.slider("💵 Automatic savings / paycheck",5,250,int(DEP),5)
    with c2: balance=st.number_input("💰 Current balance",min_value=0.,value=BAL,step=5.,format="%.2f")
    with c3: nxt=st.date_input("📅 Next deposit",value=NEXT)
    with c4: freq=st.selectbox("🔁 Schedule",[7,14,15,30],index=1,format_func=lambda x:{7:"Weekly",14:"Every 2 weeks",15:"Every 15 days",30:"Monthly"}[x])

cfg=Cfg(START,float(balance),nxt,int(freq));frame=proj(cfg,float(amount),START+timedelta(days=3650));goal=hit(frame);thru=frame[frame.date<=goal] if goal else frame;earned=float(thru.interest.sum());months=(goal-START).days/30.4375 if goal else 0;remaining=max(1000-balance,0);progress=min(balance/1000,1);div,detail=div_forecast(cfg,float(amount));pre=balance+detail.deposit.sum();dates=", ".join(x.strftime("%b %d") for x in detail[detail.deposit>0].date.tolist()) or "None"

st.markdown(f"<div class='goalbar'><div class='goalfill' style='width:{progress*100:.2f}%'></div></div><div class='caption'>🏆 {progress*100:.1f}% FILLED • {money(remaining)} LEFT • 10% APY ZONE</div>",unsafe_allow_html=True)
st.markdown("### 🔥 TAP A CARD")
a,b,c,d=st.columns(4)
with a:
    if st.button(f"💰 SAVED NOW\n\n{money(balance)}",key="saved"): focus("balance")
with b:
    if st.button(f"🎯 LEFT TO $1,000\n\n{money(remaining)}",key="left"): focus("challenge")
with c:
    if st.button(f"💵 NEXT DIVIDEND\n\n≈ {money(div)}",key="div"): focus("dividend")
with d:
    if st.button(f"🏁 $1,000 DATE\n\n{goal.strftime('%b %d, %Y') if goal else 'Beyond model'}",key="date"): focus("goal")

if st.session_state.focus=="balance":
    st.markdown(f"<div class='panel'><b style='color:#00e5ff'>💰 BALANCE CONTROL</b><div class='big'>{money(balance)}</div><p>Edit Current Balance above whenever the real account changes. At 10% APY, this balance alone generates roughly {money(balance*0.10/12)} in a simple average month before new deposits.</p></div>",unsafe_allow_html=True)
elif st.session_state.focus=="challenge":
    st.markdown("<div class='panel'><b style='color:#ffe600'>🎯 CLOSE THE GAP</b></div>",unsafe_allow_html=True)
    target=st.slider("How many months do you want to give yourself to reach $1,000?",3,48,12,1)
    target_date=START+timedelta(days=round(target*30.4375));cand=scenarios(cfg,range(5,501,5));possible=cand[cand["Goal Date"]<=target_date];need=None if possible.empty else int(possible.iloc[0].Deposit)
    if need: st.success(f"Target: about {target} months → roughly ${need} per paycheck. Current setting: ${amount}.")
    else: st.warning("That goal needs more than $500/check in this calculator. Give yourself more time.")
elif st.session_state.focus=="dividend":
    st.markdown(f"<div class='panel'><b style='color:#65ff36'>💵 NEXT DIVIDEND BREAKDOWN</b><div class='big'>≈ {money(div)}</div><p>Scheduled deposits before payout: {money(detail.deposit.sum())} on {dates}. Estimated pre-dividend balance: {money(pre)}.</p></div>",unsafe_allow_html=True)
    x=detail.copy();x["cumulative"]=x.accrual.cumsum();f=go.Figure(go.Scatter(x=x.date,y=x.cumulative,mode="lines+markers",line=dict(color=GREEN,width=5),marker=dict(color=YELLOW,size=6),fill="tozeroy",fillcolor="rgba(101,255,54,.12)"));style(f,320);f.update_yaxes(tickprefix="$",tickformat=".2f");st.plotly_chart(f,use_container_width=True,config={"displayModeBar":False})
elif st.session_state.focus=="goal":
    st.markdown(f"<div class='panel'><b style='color:#ff7a00'>🏁 $1,000 FINISH LINE</b><div class='big'>{goal.strftime('%b %d, %Y') if goal else '—'}</div><p>About {months:.1f} months on the current plan, with approximately {money(earned)} in modeled interest along the way.</p></div>",unsafe_allow_html=True)
    f=go.Figure();p=frame[frame.date<=(goal+timedelta(days=30) if goal else START+timedelta(days=365))];f.add_trace(go.Scatter(x=p.date,y=p.balance,mode="lines",line=dict(color=CYAN,width=5),fill="tozeroy",fillcolor="rgba(0,229,255,.10)"));f.add_hline(y=1000,line_dash="dash",line_color=YELLOW);style(f,320);f.update_yaxes(tickprefix="$",title="Savings");st.plotly_chart(f,use_container_width=True,config={"displayModeBar":False})

st.markdown("### 🚀 TAP A SAVINGS PLAN")
vals=[10,20,30,50,75,100];cols=st.columns(6)
for col,val in zip(cols,vals):
    f2=proj(cfg,val,START+timedelta(days=3650));h2=hit(f2);label=h2.strftime("%b %Y") if h2 else "—"
    with col:
        if st.button(f"${val}/CHECK\n\n{label}",key=f"plan{val}"): st.session_state.compare_amount=val
if "compare_amount" in st.session_state:
    v=st.session_state.compare_amount;cf=proj(cfg,v,START+timedelta(days=3650));ch=hit(cf);cd,dd=div_forecast(cfg,v);st.markdown(f"<div class='insight'>⚡ <b>${v}/check selected:</b> projected $1,000 date {ch.strftime('%B %d, %Y') if ch else 'beyond model'} • next dividend ≈ {money(cd)}. Use the main slider above to make this your active plan.</div>",unsafe_allow_html=True)

plan,compare,after,hist=st.tabs(["📈 GROWTH","🏁 COMPARE","🛡 AFTER $1K","◷ REAL HISTORY"])
with plan:
    horizon=st.radio("Chart horizon",["To $1,000","1 year","2 years","5 years"],horizontal=True);ends={"1 year":START+timedelta(days=365),"2 years":START+timedelta(days=730),"5 years":START+timedelta(days=1825)};end=goal+timedelta(days=30) if horizon=="To $1,000" and goal else ends.get(horizon,START+timedelta(days=365));p=frame[frame.date<=end];dd=p[p.deposit>0];f=go.Figure();f.add_trace(go.Scatter(x=p.date,y=p.balance,mode="lines",name="Balance",line=dict(color=CYAN,width=5)));f.add_trace(go.Scatter(x=dd.date,y=dd.balance,mode="markers",name="Deposits",marker=dict(color=ORANGE,size=8)));f.add_hline(y=1000,line_dash="dash",line_color=YELLOW);style(f);f.update_yaxes(tickprefix="$",title="Savings");st.plotly_chart(f,use_container_width=True,config={"displayModeBar":False})
with compare:
    custom=st.slider("Compare plans up to",25,250,max(100,int(amount)),5);vals=[v for v in [5,10,15,20,25,30,40,50,75,100,125,150,200,250,int(amount)] if v<=custom];sc=scenarios(cfg,sorted(set(vals)));f=go.Figure(go.Bar(x=sc.Deposit,y=sc.Months,marker=dict(color=[GREEN if a<=20 else CYAN if a<=50 else YELLOW if a<=100 else ORANGE if a<=150 else PINK for a in sc.Deposit]),text=sc.Months.map(lambda v:f"{v:.1f} mo"),textposition="outside"));style(f);f.update_xaxes(title="$/paycheck");f.update_yaxes(title="Months to $1,000");st.plotly_chart(f,use_container_width=True,config={"displayModeBar":False})
with after:
    apy=st.slider("Next account APY",0.,10.,4.5,.1,format="%.1f%%");biggoal=st.number_input("Next total savings goal",1000.,50000.,5000.,500.);s=two_bucket(cfg,float(amount),apy/100,START+timedelta(days=365*12));oh=s[s.ORSA>=1000];gh=s[s.Total>=biggoal];od=None if oh.empty else oh.iloc[0].date;gd=None if gh.empty else gh.iloc[0].date;st.markdown(f"<div class='step'>1️⃣ ORSA reaches $1,000: <b>{od.strftime('%b %d, %Y') if od else '—'}</b></div><div class='step'>2️⃣ Redirect new deposits to the next account at your selected {apy:.1f}% APY.</div><div class='step'>3️⃣ Total savings reaches {money(biggoal)}: <b>{gd.strftime('%b %d, %Y') if gd else '—'}</b></div>",unsafe_allow_html=True)
with hist:
    p=Path("data/savings_transactions.csv")
    if p.exists():
        h=pd.read_csv(p);h["date"]=pd.to_datetime(h.date);st.dataframe(h.sort_values("date",ascending=False),hide_index=True,use_container_width=True)
    else:st.info("Savings history file not found.")
st.markdown(f"<div class='caption' style='text-align:center;margin-top:20px'>HIGH-YIELD SAVINGS PROJECT v{APP_VERSION} • TAP • LEARN • ADJUST • GROW</div>",unsafe_allow_html=True)