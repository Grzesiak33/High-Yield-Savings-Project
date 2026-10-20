from datetime import date, timedelta
from math import ceil
from calendar import monthrange
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Our $5,000 Family Savings Goal",page_icon="💰",layout="wide")
GOAL=5000.0
DEADLINE=date(2027,3,1)
FIRST=date(2026,10,23)
st.markdown("""<style>.stApp{background:linear-gradient(160deg,#087CF2,#053B98 38%,#061A45 95%);color:white}.block-container{max-width:980px;padding:1rem .7rem 3rem}h1,h2,h3,p,label{color:white!important}div[data-testid="stMetric"]{background:#061A45;border:2px solid #FFE600;border-radius:16px;padding:12px}div[data-testid="stMetricLabel"] p{color:#FFE600!important;font-weight:800}div[data-testid="stMetricValue"]{color:white!important}[data-testid="stNumberInput"] input{color:#061A45!important;background:white!important;font-size:22px!important;font-weight:800!important}.stButton button{background:#E51B23!important;color:white!important;border:2px solid #FFE600!important;border-radius:14px!important;min-height:50px}.hero{background:linear-gradient(110deg,#E51B23,#FF6A00);border:3px solid #FFE600;border-radius:18px;padding:16px;margin:14px 0;box-shadow:0 6px 0 #061A45}.hero .big{font-size:clamp(2.5rem,8vw,5rem);font-weight:1000;line-height:1.1}.hero .small{font-weight:900}.info{background:#061A45;border:2px solid #FFE600;border-radius:14px;padding:14px;margin:12px 0}</style>""",unsafe_allow_html=True)
def money(x):return f"${x:,.2f}"
def paydays(today):
    days=[];d=FIRST
    while d<=DEADLINE:
        if d>=today:days.append(d)
        d+=timedelta(days=14)
    return days
def daily(b):
    return min(b,1000)*((1.10)**(1/365)-1)+max(b-1000,0)*((1.001)**(1/365)-1)
def simulate(balance,deposit,today,dual=False):
    a=float(balance);b=0.;pending_a=pending_b=0.;credited=0.;rows=[]
    dates=set(paydays(today));d=today
    while d<=DEADLINE:
        dep=float(deposit) if d in dates else 0.
        if dual:
            add_a=min(dep,max(1000-a,0));a+=add_a;b+=dep-add_a
        else:a+=dep
        pending_a+=daily(a)
        if dual:pending_b+=daily(b)
        if d.day==monthrange(d.year,d.month)[1]:
            a+=pending_a;b+=pending_b;credited+=pending_a+pending_b;pending_a=pending_b=0.
        rows.append({"Date":d,"Balance":a+b,"Deposit":dep,"Credited interest":credited})
        d+=timedelta(days=1)
    return pd.DataFrame(rows)
def required(balance,today,dual=False):
    if balance>=GOAL:return 0.
    if not paydays(today):return None
    lo,hi=0.,10000.
    for _ in range(27):
        mid=(lo+hi)/2
        if simulate(balance,mid,today,dual).iloc[-1]["Balance"]>=GOAL:hi=mid
        else:lo=mid
    ans=ceil(hi*100)/100
    while simulate(balance,ans,today,dual).iloc[-1]["Balance"]<GOAL:ans=round(ans+.01,2)
    return ans

today=date.today()
st.title("💰 OUR FAMILY SAVINGS MISSION")
st.caption("Mobile-friendly savings planner • Goal: March 1, 2027")
if "family_balance" not in st.session_state:st.session_state.family_balance=70.
balance=st.number_input("💵 Actual savings balance — update anytime",min_value=0.,step=5.,format="%.2f",key="family_balance")
remaining=paydays(today);days=max(0,(DEADLINE-today).days)
need=required(balance,today)
if need is None:
    st.error("No biweekly paydays remain before March 1. Update the goal or funding strategy.")
    st.stop()
st.markdown(f'<div class="hero"><div class="small">REQUIRED AUTOMATIC DEPOSIT — EVERY 2 WEEKS</div><div class="big">{money(need)}</div><div class="small">To grow {money(balance)} into $5,000 by March 1, 2027 • estimated interest included</div></div>',unsafe_allow_html=True)
a,b,c=st.columns(3)
a.metric("⏳ Days left",days)
b.metric("📆 Paychecks left",len(remaining))
c.metric("🎯 Still needed",money(max(0,GOAL-balance)))
st.progress(min(1.,balance/GOAL))
st.caption(f"{balance/GOAL*100:.1f}% of goal saved • Next payday: {remaining[0].strftime('%A, %B %d') if remaining else 'none'}")
st.subheader("⚡ Test your biweekly savings amount")
options=sorted(set([25.,50.,100.,150.,200.,250.,300.,350.,400.,450.,475.,500.,525.,550.,600.,700.,800.,float(need)]))
choice=st.selectbox("Choose an automatic deposit",options,index=options.index(float(need)),format_func=lambda x:f"{money(x)} / paycheck")
amount=st.number_input("Or type an exact deposit",min_value=0.,max_value=10000.,value=float(choice),step=5.,format="%.2f",key=f"deposit_{choice}")
df=simulate(balance,amount,today)
final=float(df.iloc[-1]["Balance"]);interest=float(df.iloc[-1]["Credited interest"])
x,y=st.columns(2)
x.metric("March 1 projected balance",money(final))
y.metric("Interest credited by deadline",money(interest))
if final>=GOAL:st.success(f"🎉 Goal reached! Projected cushion: {money(final-GOAL)}")
else:st.warning(f"Projected shortfall: {money(GOAL-final)}. Increase your deposit or add extra income.")
fig=go.Figure()
fig.add_trace(go.Scatter(x=df["Date"],y=df["Balance"],name="Savings",line=dict(color="#FFE600",width=5),fill="tozeroy",fillcolor="rgba(255,230,0,.14)"))
fig.add_hline(y=GOAL,line_color="#E51B23",line_dash="dash",annotation_text="$5,000")
fig.update_layout(height=340,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="#061A45",font_color="white",margin=dict(l=10,r=10,t=20,b=10),xaxis=dict(gridcolor="#22549B"),yaxis=dict(gridcolor="#22549B",tickprefix="$"))
st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
with st.expander("📅 Every payday and projected balance",expanded=True):
    rows=df[df["Date"].isin(remaining)][["Date","Deposit","Balance"]].copy()
    rows["Date"]=rows["Date"].map(lambda d:d.strftime("%a %b %d, %Y"))
    for col in ["Deposit","Balance"]:rows[col]=rows[col].map(money)
    st.dataframe(rows,hide_index=True,use_container_width=True)
with st.expander("💍 Optional: a second eligible 10% account in my wife's name"):
    st.write("This is a comparison scenario, not an existing account. It assumes your wife independently qualifies for the same savings rate and account terms.")
    dual=simulate(balance,amount,today,True)
    st.metric("Two-account projected balance",money(float(dual.iloc[-1]["Balance"])))
    st.metric("Two-account required biweekly deposit",money(required(balance,today,True)))
    st.caption("Model routes deposits to the first account until it reaches $1,000, then to the second. Both earn 10% APY on the first $1,000 and 0.10% above.")
st.markdown('<div class="info">📱 Share this website link with your wife. Each phone can view and edit its own scenario. Balances are not yet synchronized between devices, and this site does not connect to your bank.</div>',unsafe_allow_html=True)
st.caption("Estimates use 10% APY on the first $1,000, 0.10% above, daily interest calculations, and modeled month-end dividend posting. Actual rates, dates, and dividends may differ.")
st.caption("High-Yield Savings Project v2.2.0")
