from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP_VERSION="1.9.0"
START=date(2026,9,1); DEFAULT_BALANCE=20.71; DEFAULT_DEPOSIT=10.0; DEFAULT_NEXT=date(2026,9,11); BASELINE_DEPOSIT=10.0
BLUE="#087CF2"; DEEP_BLUE="#053B98"; NAVY="#061A45"; RED="#E51B23"; ORANGE="#FF6A00"; YELLOW="#FFE600"; WHITE="#FFFFFF"

@dataclass(frozen=True)
class Cfg:
    start:date; balance:float; next_dep:date; freq:int; apy:float=.10; cap:float=1000.; excess_apy:float=.001

def daily_rate(apy): return (1+apy)**(1/365)-1

def daily_interest(balance,cfg):
    return min(balance,cfg.cap)*daily_rate(cfg.apy)+max(balance-cfg.cap,0)*daily_rate(cfg.excess_apy)

def project(cfg,amount,end):
    d,bal,nxt=cfg.start,cfg.balance,cfg.next_dep; rows=[]
    while d<=end:
        dep=0.
        if d==nxt: dep=float(amount); bal+=dep; nxt+=timedelta(days=cfg.freq)
        intr=daily_interest(bal,cfg); bal+=intr
        rows.append({"date":d,"balance":bal,"deposit":dep,"interest":intr})
        d+=timedelta(days=1)
    return pd.DataFrame(rows)

def goal_date(df,goal=1000.):
    x=df[df.balance>=goal]; return None if x.empty else x.iloc[0].date

def dividend_forecast(cfg,amount,payout=date(2026,9,30)):
    d,bal,nxt=cfg.start,cfg.balance,cfg.next_dep; rows=[]; total=0.
    while d<=payout:
        dep=0.
        if d==nxt: dep=float(amount); bal+=dep; nxt+=timedelta(days=cfg.freq)
        intr=daily_interest(bal,cfg); total+=intr
        rows.append({"date":d,"balance":bal,"deposit":dep,"accrual":intr}); d+=timedelta(days=1)
    return total,pd.DataFrame(rows)

def monthly_dividends(cfg,amount,months=12):
    df=project(cfg,amount,cfg.start+timedelta(days=370)).copy(); df["month"]=pd.to_datetime(df.date).dt.to_period("M")
    out=df.groupby("month",as_index=False).interest.sum().head(months); out["label"]=out.month.astype(str).map(lambda x:pd.Period(x).strftime("%b %Y")); return out[["label","interest"]]

def scenarios(cfg,values):
    rows=[]
    for amt in values:
        df=project(cfg,amt,cfg.start+timedelta(days=3650)); hit=goal_date(df)
        if hit:
            thru=df[df.date<=hit]; rows.append({"Deposit":float(amt),"Goal Date":hit,"Months":round((hit-cfg.start).days/30.4375,1),"Interest":float(thru.interest.sum())})
    return pd.DataFrame(rows)

def required_deposit(cfg,target_date):
    if cfg.balance>=cfg.cap: return 0.
    lo,hi=0.,5000.
    for _ in range(24):
        mid=(lo+hi)/2; df=project(cfg,mid,target_date)
        if float(df.iloc[-1].balance)>=cfg.cap: hi=mid
        else: lo=mid
    return round(hi,2)

def milestone_dates(df,levels=(100,250,500,750,1000)):
    out=[]
    for level in levels:
        x=df[df.balance>=level]
        out.append((level,None if x.empty else x.iloc[0].date))
    return out

def money(v): return f"${v:,.2f}"

def style_chart(fig,height=410):
    fig.update_layout(height=height,margin=dict(l=8,r=8,t=42,b=8),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor=NAVY,font_color=WHITE,xaxis=dict(gridcolor="#2B5AA0",tickfont=dict(color=WHITE)),yaxis=dict(gridcolor="#2B5AA0",tickfont=dict(color=WHITE)),legend=dict(orientation="h",y=1.10),hovermode="x unified")

def activate_plan(x):
    st.session_state.active_deposit=float(x); st.session_state.deposit_draft=float(x); st.session_state.dash_focus="impact"

st.set_page_config(page_title="High-Yield Savings Project",page_icon="💰",layout="wide",initial_sidebar_state="collapsed")
st.markdown("""<style>
:root{--blue:#087CF2;--deep:#053B98;--navy:#061A45;--red:#E51B23;--orange:#FF6A00;--yellow:#FFE600}.stApp{background:linear-gradient(180deg,#087CF2 0%,#075dcc 22%,#061A45 72%,#04102d 100%);color:white}.block-container{max-width:1380px;padding:.35rem .7rem 3rem}header,footer{visibility:hidden}.brand{font-family:Impact,Arial Black,sans-serif;font-size:clamp(2rem,5vw,4.1rem);line-height:.9;font-style:italic;color:white;text-shadow:3px 3px 0 #E51B23;margin:.15rem 0 .55rem}.brand span{color:#FFE600}.hero{border:4px solid #FFE600;border-radius:20px;padding:5px;background:#061A45;box-shadow:0 8px 0 #E51B23}.hero img{width:100%;display:block;border-radius:13px}.live-panel{background:linear-gradient(155deg,#053B98,#087CF2 48%,#061A45 49%,#061A45 100%);border:4px solid #FFE600;border-radius:20px;padding:15px;box-shadow:0 8px 0 #E51B23}.live-title{font-family:Impact,Arial Black;font-size:1.65rem;color:white}.live-kicker{color:#FFE600;font-weight:1000;font-size:.8rem}.live-copy{color:white;font-weight:800;font-size:.9rem;margin:5px 0 10px}.banner{background:linear-gradient(90deg,#E51B23,#FF6A00);border:3px solid #FFE600;border-radius:14px;padding:12px 14px;margin:12px 0;color:white;font-weight:1000}.section-title{font-size:1.3rem;font-weight:1000;color:white;margin:.9rem 0 .35rem}[data-testid="stVerticalBlockBorderWrapper"]{background:rgba(6,26,69,.94);border:2px solid #FF6A00!important;border-radius:16px!important}[data-testid="stNumberInput"] input{font-size:22px!important;font-weight:1000!important;color:#061A45!important;background:white!important}.stNumberInput label,.stDateInput label,.stSelectbox label,.stRadio label{color:white!important;font-weight:900!important}.stButton button,.stFormSubmitButton button{width:100%;min-height:58px;background:linear-gradient(145deg,#E51B23,#FF6A00)!important;color:white!important;border:3px solid #FFE600!important;border-radius:15px!important;font-weight:1000!important;font-size:1.02rem!important;box-shadow:0 5px 0 #053B98!important}.stButton button:hover,.stFormSubmitButton button:hover{background:linear-gradient(145deg,#087CF2,#053B98)!important;border-color:white!important}.goalbar{height:22px;background:#061A45;border:2px solid white;border-radius:999px;overflow:hidden}.goalfill{height:100%;background:linear-gradient(90deg,#FFE600,#FF6A00,#E51B23)}.goalcopy{font-weight:900;color:white;margin-top:5px}.dashboard-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;margin:10px 0}.dash-card{background:#061A45;border:3px solid #087CF2;border-bottom:6px solid #FF6A00;border-radius:15px;padding:13px;color:white}.dash-card .label{font-size:.72rem;font-weight:1000;color:#FFE600}.dash-card .value{font-family:Impact,Arial Black;font-size:clamp(1.65rem,4vw,2.65rem);line-height:1;color:white;margin-top:4px}.dash-card .sub{font-size:.75rem;font-weight:800;color:#dcecff;margin-top:5px}.drill{background:#061A45;border:3px solid #FF6A00;border-left:8px solid #FFE600;border-radius:15px;padding:15px;margin:10px 0;color:white}.drill b{color:#FFE600}.drill-big{font-family:Impact,Arial Black;font-size:clamp(2.4rem,6vw,4rem);color:white;text-shadow:3px 3px 0 #E51B23;line-height:1}.milestones{display:grid;grid-template-columns:repeat(5,1fr);gap:7px}.mile{background:#061A45;border:2px solid #FFE600;border-radius:12px;padding:10px;text-align:center}.mile b{display:block;color:#FFE600;font-size:1.15rem}.mile span{font-size:.72rem;font-weight:800}[data-testid="stPlotlyChart"]{border:3px solid #FF6A00;border-radius:16px;overflow:hidden;background:#061A45;box-shadow:0 5px 0 #053B98}@media(max-width:700px){.block-container{padding:.2rem .38rem 2rem}.brand{font-size:2.25rem}.hero,.live-panel{box-shadow:0 5px 0 #E51B23}.live-title{font-size:1.35rem}[data-testid="column"]{min-width:100%!important;width:100%!important;flex:1 1 100%!important}.dashboard-grid{grid-template-columns:1fr 1fr}.dash-card .value{font-size:1.8rem}.milestones{grid-template-columns:1fr 1fr}.mile:last-child{grid-column:1/-1}}
</style>""",unsafe_allow_html=True)

for k,v in {"active_deposit":DEFAULT_DEPOSIT,"deposit_draft":DEFAULT_DEPOSIT,"dash_focus":"impact"}.items():
    if k not in st.session_state: st.session_state[k]=v

st.markdown(f"<div class='brand'>HIGH-YIELD <span>SAVINGS</span> PROJECT <small style='font-size:.28em'>v{APP_VERSION}</small></div>",unsafe_allow_html=True)
hero_col,control_col=st.columns([1.18,.82],gap="medium")
with hero_col: st.markdown("<div class='hero'><img src='https://raw.githubusercontent.com/Grzesiak33/High-Yield-Savings-Project/main/assets/savings_hero.png'></div>",unsafe_allow_html=True)
with control_col:
    st.markdown("<div class='live-panel'><div class='live-kicker'>⚡ LIVE MISSION CONTROL</div><div class='live-title'>CONTROL YOUR SAVINGS PLAN</div><div class='live-copy'>Change the plan here. Everything below recalculates from these numbers.</div></div>",unsafe_allow_html=True)
    with st.form("top_dashboard_form"):
        draft=st.number_input("💵 Deposit every paycheck ($)",0.,5000.,step=1.,format="%.2f",key="deposit_draft")
        balance=st.number_input("💰 Current balance ($)",0.,value=DEFAULT_BALANCE,step=1.,format="%.2f")
        next_dep=st.date_input("📅 Next deposit",value=DEFAULT_NEXT)
        freq=st.selectbox("🔁 Deposit schedule",[7,14,15,30],index=1,format_func=lambda x:{7:"Weekly",14:"Every 2 weeks",15:"Every 15 days",30:"Monthly"}[x])
        run=st.form_submit_button("🚀 UPDATE MY DASHBOARD",use_container_width=True)
    if run: st.session_state.active_deposit=float(draft)

amount=float(st.session_state.active_deposit); cfg=Cfg(START,float(balance),next_dep,int(freq))
active=project(cfg,amount,START+timedelta(days=3650)); baseline=project(cfg,BASELINE_DEPOSIT,START+timedelta(days=3650))
active_hit=goal_date(active); base_hit=goal_date(baseline); active_thru=active[active.date<=active_hit] if active_hit else active
active_interest=float(active_thru.interest.sum()); months_to_goal=(active_hit-START).days/30.4375 if active_hit else 0; base_months=(base_hit-START).days/30.4375 if base_hit else 0
days_faster=(base_hit-active_hit).days if active_hit and base_hit else 0; active_div,active_detail=dividend_forecast(cfg,amount); base_div,_=dividend_forecast(cfg,BASELINE_DEPOSIT); div_gain=active_div-base_div
remaining=max(1000-balance,0); progress=min(balance/1000,1); extra_per_check=amount-BASELINE_DEPOSIT; annual_extra=extra_per_check*(365/freq)
year_frame=active[active.date<=START+timedelta(days=365)]; year_balance=float(year_frame.iloc[-1].balance) if not year_frame.empty else balance

st.markdown(f"<div class='goalbar'><div class='goalfill' style='width:{progress*100:.2f}%'></div></div><div class='goalcopy'>{progress*100:.1f}% FILLED • {money(remaining)} LEFT • ACTIVE PLAN: {money(amount)}/PAYCHECK</div>",unsafe_allow_html=True)
st.markdown(f"""<div class='dashboard-grid'><div class='dash-card'><div class='label'>ACTIVE DEPOSIT</div><div class='value'>{money(amount)}</div><div class='sub'>{money(extra_per_check)} vs $10 baseline</div></div><div class='dash-card'><div class='label'>NEXT DIVIDEND</div><div class='value'>≈ {money(active_div)}</div><div class='sub'>{'+' if div_gain>=0 else ''}{money(div_gain)} vs baseline</div></div><div class='dash-card'><div class='label'>$1,000 FINISH</div><div class='value'>{active_hit.strftime('%b %Y') if active_hit else '—'}</div><div class='sub'>{abs(days_faster)} days {'faster' if days_faster>0 else 'later' if days_faster<0 else 'same'}</div></div><div class='dash-card'><div class='label'>12-MONTH BALANCE</div><div class='value'>{money(year_balance)}</div><div class='sub'>projected after one year</div></div></div>""",unsafe_allow_html=True)

st.markdown("<div class='section-title'>⚡ ONE-TAP PAYCHECK POWER-UPS</div>",unsafe_allow_html=True)
cols=st.columns(6)
for col,val in zip(cols,[10,11,13,18,25,50]):
    with col: st.button(f"${val}/CHECK",key=f"preset_{val}",on_click=activate_plan,args=(val,))

st.markdown("<div class='section-title'>👇 TAP A DASHBOARD ACTION</div>",unsafe_allow_html=True)
cols=st.columns(4)
for col,key,label in zip(cols,["dividend","goal","impact","year"],["💵 DIVIDEND\nBREAKDOWN","🏁 $1,000\nFINISH LINE","⚡ DEPOSIT\nPOWER-UP","📈 12-MONTH\nOUTLOOK"]):
    with col:
        if st.button(label,key=f"focus_{key}"): st.session_state.dash_focus=key
focus=st.session_state.dash_focus
if focus=="dividend":
    x=active_detail.copy(); x["cumulative"]=x.accrual.cumsum(); st.markdown(f"<div class='drill'><b>NEXT DIVIDEND</b><div class='drill-big'>≈ {money(active_div)}</div>{'+' if div_gain>=0 else ''}{money(div_gain)} versus the $10/check plan.</div>",unsafe_allow_html=True)
    fig=go.Figure(go.Scatter(x=x.date,y=x.cumulative,mode="lines+markers",line=dict(color=ORANGE,width=5),marker=dict(color=YELLOW,size=7),fill="tozeroy",fillcolor="rgba(255,106,0,.16)")); style_chart(fig,320); fig.update_yaxes(tickprefix="$",tickformat=".2f"); st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
elif focus=="goal": st.markdown(f"<div class='drill'><b>$1,000 FINISH LINE</b><div class='drill-big'>{active_hit.strftime('%b %d, %Y') if active_hit else '—'}</div>{months_to_goal:.1f} months • {abs(days_faster)} days {'faster' if days_faster>0 else 'later' if days_faster<0 else 'same as baseline'} • modeled interest {money(active_interest)}.</div>",unsafe_allow_html=True)
elif focus=="impact": st.markdown(f"<div class='drill'><b>DEPOSIT POWER-UP</b><div class='drill-big'>{money(amount)}</div>{'About '+money(annual_extra)+' more deposited per year than the $10 plan.' if extra_per_check>0 else 'Your $10/check baseline.' if extra_per_check==0 else money(abs(annual_extra))+' less deposited per year than baseline.'}</div>",unsafe_allow_html=True)
else: st.markdown(f"<div class='drill'><b>12-MONTH OUTLOOK</b><div class='drill-big'>{money(year_balance)}</div>Projected balance after one year at {money(amount)} per paycheck.</div>",unsafe_allow_html=True)

st.markdown("<div class='section-title'>🎯 GOAL DATE OPTIMIZER</div>",unsafe_allow_html=True)
with st.container(border=True):
    target=st.date_input("I want to reach $1,000 by",value=date(2028,1,1),min_value=START+timedelta(days=30),key="target_goal_date")
    need=required_deposit(cfg,target)
    delta=need-amount
    st.markdown(f"<div class='drill'><b>REQUIRED PAYCHECK DEPOSIT</b><div class='drill-big'>{money(need)}</div>{'Increase your current plan by '+money(delta)+' per paycheck.' if delta>0 else 'Your current plan already meets or beats this target.'}</div>",unsafe_allow_html=True)
    if st.button(f"⚡ ACTIVATE {money(need)}/CHECK PLAN",key="activate_optimizer",on_click=activate_plan,args=(need,)): pass

st.markdown("<div class='section-title'>🏅 YOUR SAVINGS MILESTONES</div>",unsafe_allow_html=True)
miles=milestone_dates(active)
st.markdown("<div class='milestones'>"+"".join(f"<div class='mile'><b>{money(level)}</b><span>{hit.strftime('%b %d, %Y') if hit else 'Beyond model'}</span></div>" for level,hit in miles)+"</div>",unsafe_allow_html=True)

st.markdown("<div class='section-title'>🚀 GROWTH VS. YOUR $10 BASELINE</div>",unsafe_allow_html=True)
horizon=st.radio("Chart view",["12 months","Until $1,000"],horizontal=True,label_visibility="collapsed")
chart_end=START+timedelta(days=365) if horizon=="12 months" else max([x for x in [active_hit,base_hit] if x is not None])+timedelta(days=30)
a=active[active.date<=chart_end]; b=baseline[baseline.date<=chart_end]
fig=go.Figure(); fig.add_trace(go.Scatter(x=b.date,y=b.balance,mode="lines",name="$10 baseline",line=dict(color=WHITE,width=3,dash="dot"))); fig.add_trace(go.Scatter(x=a.date,y=a.balance,mode="lines",name=f"${amount:g}/check",line=dict(color=YELLOW,width=6),fill="tozeroy",fillcolor="rgba(255,230,0,.12)")); fig.add_hline(y=1000,line_dash="dash",line_color=RED,line_width=4,annotation_text="🏁 $1,000"); style_chart(fig,450); fig.update_yaxes(tickprefix="$",title="Savings balance"); st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

st.markdown("<div class='section-title'>💵 MONTHLY DIVIDEND POWER</div>",unsafe_allow_html=True)
bm=monthly_dividends(cfg,10,12).rename(columns={"interest":"baseline"}); am=monthly_dividends(cfg,amount,12).rename(columns={"interest":"active"}); monthly=pd.merge(bm,am,on="label")
fig2=go.Figure(); fig2.add_trace(go.Bar(x=monthly.label,y=monthly.baseline,name="$10 baseline",marker_color=BLUE)); fig2.add_trace(go.Bar(x=monthly.label,y=monthly.active,name=f"${amount:g}/check",marker_color=ORANGE)); fig2.update_layout(barmode="group"); style_chart(fig2,420); fig2.update_yaxes(tickprefix="$",tickformat=".2f",title="Estimated monthly dividend"); st.plotly_chart(fig2,use_container_width=True,config={"displayModeBar":False})

st.markdown("<div class='section-title'>🎯 EXACT-AMOUNT COMPARISON</div>",unsafe_allow_html=True)
examples=scenarios(cfg,sorted(set([10,11,13,15,18,20,25,30,50,int(round(amount))])))
if not examples.empty:
    fig3=go.Figure(go.Bar(x=examples.Deposit,y=examples.Months,marker=dict(color=[BLUE if x==10 else YELLOW if x<15 else ORANGE if x<20 else RED for x in examples.Deposit]),text=examples.Months.map(lambda x:f"{x:.1f} mo"),textposition="outside")); style_chart(fig3,410); fig3.update_xaxes(title="Deposit each paycheck ($)"); fig3.update_yaxes(title="Months to $1,000"); st.plotly_chart(fig3,use_container_width=True,config={"displayModeBar":False})

with st.expander("◷ REAL ORSA HISTORY"):
    p=Path("data/savings_transactions.csv")
    if p.exists():
        hist=pd.read_csv(p); hist["date"]=pd.to_datetime(hist.date); st.dataframe(hist.sort_values("date",ascending=False),hide_index=True,use_container_width=True)
    else: st.info("Savings history file not found.")
st.markdown(f"<div class='goalcopy' style='text-align:center;margin-top:18px'>HIGH-YIELD SAVINGS PROJECT v{APP_VERSION} • HERO + COLORS UNCHANGED • MORE CONTROLS, MORE DECISIONS, MORE FEEDBACK</div>",unsafe_allow_html=True)
