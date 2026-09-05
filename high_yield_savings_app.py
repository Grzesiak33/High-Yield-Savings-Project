from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP_VERSION="2.0.0"
START=date(2026,9,1); DEFAULT_BALANCE=20.71; DEFAULT_DEPOSIT=10.; DEFAULT_NEXT=date(2026,9,11); BASELINE_DEPOSIT=10.
BLUE="#087CF2"; DEEP_BLUE="#053B98"; NAVY="#061A45"; RED="#E51B23"; ORANGE="#FF6A00"; YELLOW="#FFE600"; WHITE="#FFFFFF"
@dataclass(frozen=True)
class Cfg: start:date; balance:float; next_dep:date; freq:int; apy:float=.10; cap:float=1000.; excess_apy:float=.001

def daily_rate(a): return (1+a)**(1/365)-1
def daily_interest(b,c): return min(b,c.cap)*daily_rate(c.apy)+max(b-c.cap,0)*daily_rate(c.excess_apy)
def project(c,a,end):
 d,b,n=c.start,c.balance,c.next_dep; r=[]
 while d<=end:
  dep=0.
  if d==n: dep=float(a); b+=dep; n+=timedelta(days=c.freq)
  i=daily_interest(b,c); b+=i; r.append({"date":d,"balance":b,"deposit":dep,"interest":i}); d+=timedelta(days=1)
 return pd.DataFrame(r)
def goal_date(df,g=1000.):
 x=df[df.balance>=g]; return None if x.empty else x.iloc[0].date
def dividend_forecast(c,a,payout=date(2026,9,30)):
 d,b,n=c.start,c.balance,c.next_dep; r=[]; total=0.
 while d<=payout:
  dep=0.
  if d==n: dep=float(a); b+=dep; n+=timedelta(days=c.freq)
  i=daily_interest(b,c); total+=i; r.append({"date":d,"balance":b,"deposit":dep,"accrual":i}); d+=timedelta(days=1)
 return total,pd.DataFrame(r)
def monthly_dividends(c,a,months=12):
 df=project(c,a,c.start+timedelta(days=370)); df["month"]=pd.to_datetime(df.date).dt.to_period("M"); o=df.groupby("month",as_index=False).interest.sum().head(months); o["label"]=o.month.astype(str).map(lambda x:pd.Period(x).strftime("%b %Y")); return o[["label","interest"]]
def required_deposit(c,target,goal=1000.):
 if c.balance>=goal:return 0.
 lo,hi=0.,5000.
 for _ in range(24):
  mid=(lo+hi)/2; df=project(c,mid,target)
  if float(df.iloc[-1].balance)>=goal:hi=mid
  else:lo=mid
 return round(hi,2)
def milestone_dates(df,levels):
 out=[]
 for level in levels:
  x=df[df.balance>=level]; out.append((level,None if x.empty else x.iloc[0].date))
 return out
def money(v):return f"${v:,.2f}"
def style_chart(fig,h=410): fig.update_layout(height=h,margin=dict(l=8,r=8,t=42,b=8),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor=NAVY,font_color=WHITE,xaxis=dict(gridcolor="#2B5AA0"),yaxis=dict(gridcolor="#2B5AA0"),legend=dict(orientation="h",y=1.10),hovermode="x unified")
def activate(x): st.session_state.active_deposit=float(x);st.session_state.deposit_draft=float(x);st.session_state.focus="impact"

st.set_page_config(page_title="High-Yield Savings Project",page_icon="💰",layout="wide",initial_sidebar_state="collapsed")
st.markdown("""<style>:root{--b:#087CF2;--n:#061A45;--r:#E51B23;--o:#FF6A00;--y:#FFE600}.stApp{background:linear-gradient(180deg,#087CF2,#075dcc 22%,#061A45 72%,#04102d);color:white}.block-container{max-width:1380px;padding:.35rem .7rem 3rem}header,footer{visibility:hidden}.brand{font-family:Impact,Arial Black;font-size:clamp(2rem,5vw,4.1rem);line-height:.9;font-style:italic;color:white;text-shadow:3px 3px 0 #E51B23}.brand span{color:#FFE600}.hero{border:4px solid #FFE600;border-radius:20px;padding:5px;background:#061A45;box-shadow:0 8px 0 #E51B23}.hero img{width:100%;display:block;border-radius:13px}.live{background:linear-gradient(155deg,#053B98,#087CF2 48%,#061A45 49%);border:4px solid #FFE600;border-radius:20px;padding:15px;box-shadow:0 8px 0 #E51B23}.title{font-family:Impact,Arial Black;font-size:1.65rem}.yellow{color:#FFE600;font-weight:1000}.section{font-size:1.3rem;font-weight:1000;margin:.9rem 0 .35rem}.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;margin:10px 0}.card{background:#061A45;border:3px solid #087CF2;border-bottom:6px solid #FF6A00;border-radius:15px;padding:13px}.label{font-size:.72rem;font-weight:1000;color:#FFE600}.value{font-family:Impact,Arial Black;font-size:clamp(1.65rem,4vw,2.65rem);line-height:1;margin-top:4px}.sub{font-size:.75rem;font-weight:800;color:#dcecff;margin-top:5px}.panel{background:#061A45;border:3px solid #FF6A00;border-left:8px solid #FFE600;border-radius:15px;padding:15px;margin:10px 0}.big{font-family:Impact,Arial Black;font-size:clamp(2.4rem,6vw,4rem);text-shadow:3px 3px 0 #E51B23;line-height:1}.goalbar{height:22px;background:#061A45;border:2px solid white;border-radius:999px;overflow:hidden}.fill{height:100%;background:linear-gradient(90deg,#FFE600,#FF6A00,#E51B23)}.copy{font-weight:900;margin-top:5px}.stButton button,.stFormSubmitButton button{width:100%;min-height:58px;background:linear-gradient(145deg,#E51B23,#FF6A00)!important;color:white!important;border:3px solid #FFE600!important;border-radius:15px!important;font-weight:1000!important;box-shadow:0 5px 0 #053B98!important}[data-testid="stNumberInput"] input{font-size:21px!important;font-weight:1000!important;color:#061A45!important;background:white!important}.stNumberInput label,.stDateInput label,.stSelectbox label,.stRadio label{color:white!important;font-weight:900!important}[data-testid="stPlotlyChart"]{border:3px solid #FF6A00;border-radius:16px;overflow:hidden;background:#061A45}.payday{background:linear-gradient(90deg,#053B98,#087CF2);border:3px solid #FFE600;border-radius:14px;padding:12px;margin:7px 0;font-weight:900}@media(max-width:700px){[data-testid="column"]{min-width:100%!important;width:100%!important;flex:1 1 100%!important}.cards{grid-template-columns:1fr 1fr}.brand{font-size:2.25rem}.value{font-size:1.8rem}}</style>""",unsafe_allow_html=True)
for k,v in {"active_deposit":10.,"deposit_draft":10.,"focus":"impact","custom_goal":1000.}.items():
 if k not in st.session_state:st.session_state[k]=v
st.markdown(f"<div class='brand'>HIGH-YIELD <span>SAVINGS</span> PROJECT <small style='font-size:.28em'>v{APP_VERSION}</small></div>",unsafe_allow_html=True)
a,b=st.columns([1.18,.82],gap="medium")
with a:st.markdown("<div class='hero'><img src='https://raw.githubusercontent.com/Grzesiak33/High-Yield-Savings-Project/main/assets/savings_hero.png'></div>",unsafe_allow_html=True)
with b:
 st.markdown("<div class='live'><div class='yellow'>⚡ LIVE MISSION CONTROL</div><div class='title'>CONTROL YOUR SAVINGS PLAN</div><div>Change the plan here. Every tool below recalculates.</div></div>",unsafe_allow_html=True)
 with st.form("mission"):
  draft=st.number_input("💵 Deposit every paycheck ($)",0.,5000.,step=1.,format="%.2f",key="deposit_draft");balance=st.number_input("💰 Current balance ($)",0.,value=DEFAULT_BALANCE,step=1.,format="%.2f");next_dep=st.date_input("📅 Next deposit",value=DEFAULT_NEXT);freq=st.selectbox("🔁 Deposit schedule",[7,14,15,30],index=1,format_func=lambda x:{7:"Weekly",14:"Every 2 weeks",15:"Every 15 days",30:"Monthly"}[x]);run=st.form_submit_button("🚀 UPDATE MY DASHBOARD",use_container_width=True)
 if run:st.session_state.active_deposit=float(draft)
amount=float(st.session_state.active_deposit);cfg=Cfg(START,float(balance),next_dep,int(freq));active=project(cfg,amount,START+timedelta(days=3650));base=project(cfg,10,START+timedelta(days=3650));hit=goal_date(active);basehit=goal_date(base);div,detail=dividend_forecast(cfg,amount);basediv,_=dividend_forecast(cfg,10);days=(basehit-hit).days if hit and basehit else 0;remain=max(1000-balance,0);progress=min(balance/1000,1);yr=active[active.date<=START+timedelta(days=365)];yrbal=float(yr.iloc[-1].balance);extra=(amount-10)*(365/freq)
st.markdown(f"<div class='goalbar'><div class='fill' style='width:{progress*100:.2f}%'></div></div><div class='copy'>{progress*100:.1f}% FILLED • {money(remain)} LEFT • {money(amount)}/PAYCHECK</div>",unsafe_allow_html=True)
st.markdown(f"<div class='cards'><div class='card'><div class='label'>ACTIVE DEPOSIT</div><div class='value'>{money(amount)}</div><div class='sub'>{money(amount-10)} vs baseline</div></div><div class='card'><div class='label'>NEXT DIVIDEND</div><div class='value'>≈ {money(div)}</div><div class='sub'>{'+' if div-basediv>=0 else ''}{money(div-basediv)} vs baseline</div></div><div class='card'><div class='label'>$1,000 FINISH</div><div class='value'>{hit.strftime('%b %Y') if hit else '—'}</div><div class='sub'>{abs(days)} days {'faster' if days>0 else 'later' if days<0 else 'same'}</div></div><div class='card'><div class='label'>12-MONTH BALANCE</div><div class='value'>{money(yrbal)}</div><div class='sub'>projected</div></div></div>",unsafe_allow_html=True)

st.markdown("<div class='section'>⚡ QUICK PLAN SWITCHER</div>",unsafe_allow_html=True)
cs=st.columns(6)
for c,v in zip(cs,[10,11,13,18,25,50]):
 with c:st.button(f"${v}/CHECK",key=f"p{v}",on_click=activate,args=(v,))

st.markdown("<div class='section'>💥 NEXT 4 PAYDAYS — SEE IT HAPPEN</div>",unsafe_allow_html=True)
paydays=active[active.deposit>0].head(4)
for _,r in paydays.iterrows():st.markdown(f"<div class='payday'>📅 {r.date.strftime('%b %d, %Y')} &nbsp; +{money(r.deposit)} &nbsp; → projected balance <span class='yellow'>{money(r.balance)}</span></div>",unsafe_allow_html=True)

st.markdown("<div class='section'>🎯 BUILD YOUR OWN SAVINGS GOAL</div>",unsafe_allow_html=True)
g1,g2=st.columns(2)
with g1:custom_goal=st.number_input("My savings goal ($)",min_value=50.,max_value=100000.,value=float(st.session_state.custom_goal),step=50.)
with g2:target=st.date_input("I want it by",value=date(2028,1,1),min_value=START+timedelta(days=30),key="custom_target")
st.session_state.custom_goal=custom_goal
need=required_deposit(cfg,target,custom_goal); custom_hit=goal_date(active,custom_goal); delta=need-amount
st.markdown(f"<div class='panel'><div class='yellow'>YOUR GOAL PLAN</div><div class='big'>{money(need)}/CHECK</div>Required to target {money(custom_goal)} by {target.strftime('%b %d, %Y')}. {'Add '+money(delta)+' to your current paycheck deposit.' if delta>0 else 'Your current plan already meets or beats this target.'}</div>",unsafe_allow_html=True)
st.button(f"🚀 ACTIVATE {money(need)}/CHECK",key="activate_goal",on_click=activate,args=(need,),use_container_width=True)

st.markdown("<div class='section'>🧠 SAVINGS COACH</div>",unsafe_allow_html=True)
if amount==10:coach="Try $13/check. It is only $3 more each payday, but the finish-date and dividend charts below will show what those small increases buy you."
elif amount<18:coach=f"You're already above baseline. Your current increase adds about {money(extra)} more deposits per year. Test $18/check next to see whether the faster finish feels worth it."
elif amount<50:coach=f"This is a meaningful power-up: roughly {money(extra)} more deposits per year than baseline. Watch the milestone dates — you're compressing the wait, not just growing a number."
else:coach=f"At {money(amount)}/check you're in acceleration mode. The next decision becomes what account receives new money after the 10% ORSA tier is filled."
st.markdown(f"<div class='panel'><div class='yellow'>⚡ WHAT THE NUMBERS ARE TELLING YOU</div>{coach}</div>",unsafe_allow_html=True)

st.markdown("<div class='section'>🏅 MILESTONE LADDER</div>",unsafe_allow_html=True)
levels=sorted(set([100.,250.,500.,750.,1000.,float(custom_goal)]));miles=milestone_dates(active,levels)
figm=go.Figure()
for level,mhit in miles:
 if mhit:figm.add_trace(go.Scatter(x=[mhit],y=[level],mode="markers+text",text=[money(level)],textposition="top center",marker=dict(size=18,color=YELLOW,line=dict(color=RED,width=3)),name=money(level),showlegend=False))
style_chart(figm,350);figm.update_yaxes(tickprefix="$",title="Savings milestone");figm.update_xaxes(title="Projected date");st.plotly_chart(figm,use_container_width=True,config={"displayModeBar":False})

st.markdown("<div class='section'>🚀 GROWTH LAB</div>",unsafe_allow_html=True)
horizon=st.radio("Growth view",["Next 6 months","12 months","Until $1,000"],horizontal=True,label_visibility="collapsed")
if horizon=="Next 6 months":end=START+timedelta(days=183)
elif horizon=="12 months":end=START+timedelta(days=365)
else:end=max([x for x in [hit,basehit] if x])+timedelta(days=30)
aa=active[active.date<=end];bb=base[base.date<=end];fig=go.Figure();fig.add_trace(go.Scatter(x=bb.date,y=bb.balance,name="$10 baseline",line=dict(color=WHITE,width=3,dash="dot")));fig.add_trace(go.Scatter(x=aa.date,y=aa.balance,name=f"${amount:g}/check",line=dict(color=YELLOW,width=6),fill="tozeroy",fillcolor="rgba(255,230,0,.12)"));fig.add_hline(y=1000,line_dash="dash",line_color=RED,line_width=4);style_chart(fig,450);fig.update_yaxes(tickprefix="$",title="Savings balance");st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

st.markdown("<div class='section'>💵 DIVIDEND ACCELERATOR</div>",unsafe_allow_html=True)
bm=monthly_dividends(cfg,10).rename(columns={"interest":"baseline"});am=monthly_dividends(cfg,amount).rename(columns={"interest":"active"});mm=pd.merge(bm,am,on="label");mm["gain"]=mm.active-mm.baseline
fig2=go.Figure();fig2.add_trace(go.Bar(x=mm.label,y=mm.baseline,name="$10 baseline",marker_color=BLUE));fig2.add_trace(go.Bar(x=mm.label,y=mm.active,name="Active plan",marker_color=ORANGE,text=mm.active.map(lambda x:f"${x:.2f}"),textposition="outside"));fig2.update_layout(barmode="group");style_chart(fig2,430);fig2.update_yaxes(tickprefix="$",tickformat=".2f");st.plotly_chart(fig2,use_container_width=True,config={"displayModeBar":False})
st.markdown(f"<div class='panel'><span class='yellow'>12-MONTH DIVIDEND DIFFERENCE:</span> {money(mm.gain.sum())} versus staying at $10/check.</div>",unsafe_allow_html=True)

with st.expander("◷ REAL ORSA HISTORY"):
 p=Path("data/savings_transactions.csv")
 if p.exists():
  hist=pd.read_csv(p);hist["date"]=pd.to_datetime(hist.date);st.dataframe(hist.sort_values("date",ascending=False),hide_index=True,use_container_width=True)
st.markdown(f"<div class='copy' style='text-align:center;margin-top:18px'>HIGH-YIELD SAVINGS PROJECT v{APP_VERSION} • HERO + COLORS UNCHANGED • PAYDAY SIMULATOR • CUSTOM GOALS • SAVINGS COACH</div>",unsafe_allow_html=True)
