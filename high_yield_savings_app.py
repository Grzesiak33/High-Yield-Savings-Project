from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP_VERSION="1.6.1"; START=date(2026,9,1); DEFAULT_BALANCE=20.71; DEFAULT_DEPOSIT=10.0; DEFAULT_NEXT=date(2026,9,11)
BLUE="#087CF2"; DEEP_BLUE="#053B98"; NAVY="#061A45"; RED="#E51B23"; ORANGE="#FF6A00"; YELLOW="#FFE600"; WHITE="#FFFFFF"
@dataclass(frozen=True)
class Cfg:
    start:date; balance:float; next_dep:date; freq:int; apy:float=.10; cap:float=1000.; excess_apy:float=.001

def daily_rate(a):return (1+a)**(1/365)-1
def daily_interest(b,c):return min(b,c.cap)*daily_rate(c.apy)+max(b-c.cap,0)*daily_rate(c.excess_apy)
def project(c,a,end):
    d,b,n=c.start,c.balance,c.next_dep;r=[]
    while d<=end:
        dep=0.
        if d==n:dep=float(a);b+=dep;n+=timedelta(days=c.freq)
        i=daily_interest(b,c);b+=i;r.append({"date":d,"balance":b,"deposit":dep,"interest":i});d+=timedelta(days=1)
    return pd.DataFrame(r)
def goal_date(df,g=1000.):
    x=df[df.balance>=g];return None if x.empty else x.iloc[0]["date"]
def dividend_forecast(c,a,payout=date(2026,9,30)):
    d,b,n=c.start,c.balance,c.next_dep;r=[];total=0.
    while d<=payout:
        dep=0.
        if d==n:dep=float(a);b+=dep;n+=timedelta(days=c.freq)
        i=daily_interest(b,c);total+=i;r.append({"date":d,"balance":b,"deposit":dep,"accrual":i});d+=timedelta(days=1)
    return total,pd.DataFrame(r)
def scenarios(c,values):
    rows=[]
    for a in values:
        df=project(c,a,c.start+timedelta(days=3650));h=goal_date(df)
        if h:
            x=df[df.date<=h];rows.append({"Deposit":a,"Goal Date":h,"Months":round((h-c.start).days/30.4375,1),"Interest":float(x.interest.sum())})
    return pd.DataFrame(rows)
def two_bucket(c,a,next_apy,end):
    d,o,b2,n=c.start,c.balance,0.,c.next_dep;r=[]
    while d<=end:
        if d==n:
            room=max(c.cap-o,0);x=min(a,room);o+=x;b2+=max(a-x,0);n+=timedelta(days=c.freq)
        o+=daily_interest(o,c);b2+=b2*daily_rate(next_apy)
        if o>c.cap:b2+=o-c.cap;o=c.cap
        r.append({"date":d,"ORSA":o,"Bucket #2":b2,"Total":o+b2});d+=timedelta(days=1)
    return pd.DataFrame(r)
def money(v):return f"${v:,.2f}"
def style_chart(fig,h=390):fig.update_layout(height=h,margin=dict(l=8,r=8,t=32,b=8),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor=NAVY,font_color=WHITE,xaxis=dict(gridcolor="#2B5AA0",tickfont=dict(color=WHITE)),yaxis=dict(gridcolor="#2B5AA0",tickfont=dict(color=WHITE)),legend=dict(orientation="h",y=1.07),hovermode="x unified")

st.set_page_config(page_title="High-Yield Savings Project",page_icon="💰",layout="wide",initial_sidebar_state="collapsed")
st.markdown('''<style>:root{--blue:#087CF2;--deep:#053B98;--navy:#061A45;--red:#E51B23;--orange:#FF6A00;--yellow:#FFE600}.stApp{background:linear-gradient(180deg,#087CF2 0%,#075dcc 20%,#061A45 72%,#04102d 100%);color:white}.block-container{max-width:1380px;padding:.35rem .7rem 3rem}header,footer{visibility:hidden}.brand{font-family:Impact,Arial Black,sans-serif;font-size:clamp(2rem,5vw,4.1rem);line-height:.9;font-style:italic;color:white;text-shadow:3px 3px 0 #E51B23;margin:.15rem 0 .55rem}.brand span{color:#FFE600}.hero{border:4px solid #FFE600;border-radius:20px;padding:5px;background:#061A45;box-shadow:0 8px 0 #E51B23}.hero img{width:100%;display:block;border-radius:13px}.banner{background:linear-gradient(90deg,#E51B23,#FF6A00);color:white;border:3px solid #FFE600;border-radius:14px;padding:12px 14px;margin:12px 0;font-weight:1000}.section-title{font-size:1.25rem;font-weight:1000;color:white;margin:.8rem 0 .35rem}.goalbar{height:20px;background:#061A45;border:2px solid white;border-radius:999px;overflow:hidden}.goalfill{height:100%;background:linear-gradient(90deg,#FFE600,#FF6A00,#E51B23)}.goalcopy{font-weight:900;color:white;margin-top:5px}[data-testid="stVerticalBlockBorderWrapper"]{background:rgba(6,26,69,.93);border:2px solid #FF6A00!important;border-radius:16px!important}.stButton button{width:100%;min-height:72px;background:linear-gradient(145deg,#087CF2,#053B98)!important;color:white!important;border:3px solid #FFE600!important;border-radius:15px!important;font-weight:1000!important;font-size:1rem!important;white-space:pre-line!important;box-shadow:0 5px 0 #E51B23!important}.stButton button:hover,.stButton button:focus{background:linear-gradient(145deg,#E51B23,#FF6A00)!important;color:white!important;border-color:white!important}.stButton button p{color:white!important}.action-panel{background:#061A45;border:3px solid #FF6A00;border-left:8px solid #FFE600;border-radius:15px;padding:15px;margin:10px 0;color:white}.action-panel b{color:#FFE600}.big{font-family:Impact,Arial Black;font-size:clamp(2.5rem,7vw,4.5rem);color:white;text-shadow:3px 3px 0 #E51B23}.insight{background:linear-gradient(90deg,#053B98,#087CF2);border:2px solid #FFE600;border-radius:13px;padding:12px;margin:8px 0;color:white;font-weight:900}[data-testid="stPlotlyChart"]{border:2px solid #FF6A00;border-radius:14px;overflow:hidden;background:#061A45}[data-baseweb="select"]>div,[data-baseweb="input"]>div,input{color:#061A45!important;background:white!important}input{font-size:18px!important;font-weight:900!important}.stNumberInput label,.stDateInput label,.stSelectbox label,.stRadio label{color:white!important;font-weight:900!important}.deposit-wrap{background:linear-gradient(135deg,#E51B23,#FF6A00);border:3px solid #FFE600;border-radius:18px;padding:12px 14px 5px;margin-bottom:8px;box-shadow:0 6px 0 #053B98}.deposit-title{font-family:Impact,Arial Black;font-size:1.35rem;color:white}.deposit-help{font-size:.86rem;font-weight:800;color:white}.stAlert p{color:#061A45!important}.stAlert{border:2px solid #FFE600!important}@media(max-width:700px){.block-container{padding:.2rem .38rem 2rem}.brand{font-size:2.25rem}.hero{border-width:3px;box-shadow:0 5px 0 #E51B23}.banner{font-size:.92rem}.section-title{font-size:1.08rem}[data-testid="column"]{min-width:100%!important;width:100%!important;flex:1 1 100%!important}.stButton button{min-height:66px;font-size:.95rem;margin-bottom:.25rem}.action-panel{font-size:.94rem}.big{font-size:3rem}.deposit-wrap{padding:10px 11px 3px}.deposit-title{font-size:1.2rem}}</style>''',unsafe_allow_html=True)
if "focus" not in st.session_state:st.session_state.focus="none"
if "selected_plan" not in st.session_state:st.session_state.selected_plan=None
if "deposit_amount" not in st.session_state:st.session_state.deposit_amount=DEFAULT_DEPOSIT

def set_focus(x):st.session_state.focus=x
def set_deposit(x):st.session_state.deposit_amount=float(x)

st.markdown(f"<div class='brand'>HIGH-YIELD <span>SAVINGS</span> PROJECT <small style='font-size:.28em'>v{APP_VERSION}</small></div>",unsafe_allow_html=True)
st.markdown("<div class='hero'><img src='https://raw.githubusercontent.com/Grzesiak33/High-Yield-Savings-Project/main/assets/savings_hero.png'></div>",unsafe_allow_html=True)
st.markdown("<div class='banner'>⚡ TYPE YOUR SAVINGS NUMBER. Enter exactly what you want, or use a quick amount button.</div>",unsafe_allow_html=True)
with st.container(border=True):
    st.markdown("<div class='section-title'>🎮 CONTROL YOUR PLAN</div>",unsafe_allow_html=True);c1,c2=st.columns(2)
    with c1:
        st.markdown("<div class='deposit-wrap'><div class='deposit-title'>💵 YOUR PAYCHECK DEPOSIT</div><div class='deposit-help'>Type the exact amount, or tap a quick choice.</div></div>",unsafe_allow_html=True)
        amount=st.number_input("Deposit amount ($)",min_value=0.0,max_value=5000.0,step=1.0,format="%.2f",key="deposit_amount")
        q1,q2,q3,q4=st.columns(4)
        with q1:st.button("$10",key="q10",on_click=set_deposit,args=(10.0,))
        with q2:st.button("$25",key="q25",on_click=set_deposit,args=(25.0,))
        with q3:st.button("$50",key="q50",on_click=set_deposit,args=(50.0,))
        with q4:st.button("$100",key="q100",on_click=set_deposit,args=(100.0,))
    with c2:
        balance=st.number_input("💰 Current savings balance",min_value=0.0,value=DEFAULT_BALANCE,step=5.0,format="%.2f");next_dep=st.date_input("📅 Next automatic deposit",value=DEFAULT_NEXT);freq=st.selectbox("🔁 Deposit schedule",[7,14,15,30],index=1,format_func=lambda x:{7:"Weekly",14:"Every 2 weeks",15:"Every 15 days",30:"Monthly"}[x])
cfg=Cfg(START,float(balance),next_dep,int(freq));frame=project(cfg,float(amount),START+timedelta(days=3650));goal=goal_date(frame);thru=frame[frame.date<=goal] if goal else frame;earned=float(thru.interest.sum());months=(goal-START).days/30.4375 if goal else 0;remaining=max(1000-balance,0);progress=min(balance/1000,1);div,detail=dividend_forecast(cfg,float(amount));pre=balance+float(detail.deposit.sum());dates=", ".join(d.strftime("%b %d") for d in detail[detail.deposit>0].date.tolist()) or "None"
st.markdown(f"<div class='goalbar'><div class='goalfill' style='width:{progress*100:.2f}%'></div></div><div class='goalcopy'>{progress*100:.1f}% FILLED • {money(remaining)} LEFT • CURRENT PLAN: {money(amount)}/PAYCHECK</div>",unsafe_allow_html=True)
st.markdown("<div class='section-title'>🔥 TAP A CARD</div>",unsafe_allow_html=True);a,b,c,d=st.columns(4)
with a:
    if st.button(f"💰 SAVED NOW\n{money(balance)}",key="saved_card"):set_focus("balance")
with b:
    if st.button(f"🎯 CLOSE THE GAP\n{money(remaining)} LEFT",key="gap_card"):set_focus("gap")
with c:
    if st.button(f"💵 NEXT DIVIDEND\n≈ {money(div)}",key="div_card"):set_focus("dividend")
with d:
    if st.button(f"🏁 $1,000 DATE\n{goal.strftime('%b %d, %Y') if goal else 'Beyond model'}",key="goal_card"):set_focus("goal")
if st.session_state.focus=="balance":st.markdown(f"<div class='action-panel'><b>BALANCE ACTION</b><div class='big'>{money(balance)}</div>Edit the balance above whenever the real account changes.</div>",unsafe_allow_html=True)
elif st.session_state.focus=="gap":
    st.markdown("<div class='action-panel'><b>CLOSE-THE-GAP CALCULATOR</b><br>Type the number of months you want to give yourself.</div>",unsafe_allow_html=True);target_months=st.number_input("Months to reach $1,000",min_value=1,max_value=120,value=12,step=1);target_date=START+timedelta(days=round(target_months*30.4375));candidates=scenarios(cfg,range(5,1001,5));possible=candidates[candidates["Goal Date"]<=target_date];need=None if possible.empty else int(possible.iloc[0]["Deposit"])
    if need is not None:st.success(f"About ${need}/paycheck targets roughly {target_months} months. Current plan: {money(amount)}/paycheck.")
    else:st.warning("That timeline needs more than $1,000 per paycheck in this calculator.")
elif st.session_state.focus=="dividend":
    st.markdown(f"<div class='action-panel'><b>NEXT DIVIDEND BREAKDOWN</b><div class='big'>≈ {money(div)}</div>Deposits before payout: {money(detail.deposit.sum())} on {dates}. Estimated pre-dividend balance: {money(pre)}.</div>",unsafe_allow_html=True);x=detail.copy();x["cumulative"]=x.accrual.cumsum();fig=go.Figure(go.Scatter(x=x.date,y=x.cumulative,mode="lines+markers",line=dict(color=ORANGE,width=5),marker=dict(color=YELLOW,size=6)));style_chart(fig,320);fig.update_yaxes(tickprefix="$",tickformat=".2f");st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
elif st.session_state.focus=="goal":st.markdown(f"<div class='action-panel'><b>$1,000 FINISH LINE</b><div class='big'>{goal.strftime('%b %d, %Y') if goal else '—'}</div>About {months:.1f} months on the current {money(amount)}/paycheck plan, with approximately {money(earned)} in modeled interest.</div>",unsafe_allow_html=True)
st.markdown("<div class='section-title'>🚀 QUICK WHAT-IF BUTTONS</div>",unsafe_allow_html=True);cols=st.columns(6)
for col,val in zip(cols,[10,20,30,50,75,100]):
    temp=project(cfg,val,START+timedelta(days=3650));h=goal_date(temp);label=h.strftime("%b %Y") if h else "—"
    with col:
        if st.button(f"${val}/CHECK\n{label}",key=f"plan_{val}"):st.session_state.selected_plan=val
if st.session_state.selected_plan:
    val=st.session_state.selected_plan;temp=project(cfg,val,START+timedelta(days=3650));h=goal_date(temp);dv,_=dividend_forecast(cfg,val);st.markdown(f"<div class='insight'>⚡ TESTING <b>${val}/check</b>: $1,000 around <b>{h.strftime('%B %d, %Y') if h else 'beyond model'}</b> • next dividend ≈ <b>{money(dv)}</b>. Type ${val} above to make it active.</div>",unsafe_allow_html=True)
st.markdown("<div class='section-title'>🧭 CHOOSE WHAT YOU WANT TO DO</div>",unsafe_allow_html=True);view=st.radio("",["Growth","Compare plans","After $1K","Real history"],horizontal=True,label_visibility="collapsed")
if view=="Growth":
    horizon=st.radio("Chart range",["To $1,000","1 year","2 years","5 years"],horizontal=True);ends={"1 year":START+timedelta(days=365),"2 years":START+timedelta(days=730),"5 years":START+timedelta(days=1825)};end=goal+timedelta(days=30) if horizon=="To $1,000" and goal else ends.get(horizon,START+timedelta(days=365));p=frame[frame.date<=end];deps=p[p.deposit>0];fig=go.Figure();fig.add_trace(go.Scatter(x=p.date,y=p.balance,mode="lines",name="Balance",line=dict(color=YELLOW,width=5)));fig.add_trace(go.Scatter(x=deps.date,y=deps.balance,mode="markers",name="Deposits",marker=dict(color=ORANGE,size=8)));fig.add_hline(y=1000,line_dash="dash",line_color=RED);style_chart(fig);fig.update_yaxes(tickprefix="$",title="Savings");st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
elif view=="Compare plans":
    max_compare=st.number_input("Highest paycheck deposit to compare ($)",min_value=25,max_value=1000,value=max(100,int(amount)),step=25);vals=[v for v in [5,10,15,20,25,30,40,50,75,100,125,150,200,250,300,400,500,int(amount)] if v<=max_compare];sc=scenarios(cfg,sorted(set(vals)));fig=go.Figure(go.Bar(x=sc.Deposit,y=sc.Months,marker=dict(color=[BLUE if a<=30 else YELLOW if a<=75 else ORANGE if a<=150 else RED for a in sc.Deposit])));style_chart(fig);fig.update_xaxes(title="$/paycheck");fig.update_yaxes(title="Months to $1,000");st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
elif view=="After $1K":
    next_apy=st.number_input("Next account APY (%)",min_value=0.0,max_value=20.0,value=4.5,step=.1,format="%.1f");big_goal=st.number_input("Next total savings goal ($)",min_value=1000.0,max_value=100000.0,value=5000.0,step=500.0);s=two_bucket(cfg,float(amount),next_apy/100,START+timedelta(days=365*12));o=s[s.ORSA>=1000];g=s[s.Total>=big_goal];od=None if o.empty else o.iloc[0].date;gd=None if g.empty else g.iloc[0].date;st.markdown(f"<div class='action-panel'><b>NEXT MOVE</b><br>1️⃣ Fill ORSA: <b>{od.strftime('%b %d, %Y') if od else '—'}</b><br>2️⃣ Redirect deposits to a {next_apy:.1f}% account.<br>3️⃣ Reach {money(big_goal)} total: <b>{gd.strftime('%b %d, %Y') if gd else '—'}</b></div>",unsafe_allow_html=True)
else:
    p=Path("data/savings_transactions.csv")
    if p.exists():h=pd.read_csv(p);h["date"]=pd.to_datetime(h.date);st.dataframe(h.sort_values("date",ascending=False),hide_index=True,use_container_width=True)
    else:st.info("Savings history file not found.")
st.markdown(f"<div class='goalcopy' style='text-align:center;margin-top:18px'>HIGH-YIELD SAVINGS PROJECT v{APP_VERSION} • TYPE IT • TAP IT • GROW IT</div>",unsafe_allow_html=True)