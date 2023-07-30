import streamlit as st
import pandas as pd 
import numpy as np
import streamlit as st
import smtplib
from email.message import EmailMessage

st.set_page_config(page_title="Buy vs Rent",
                   page_icon="🏠")

st.title('Buy vs Rent 🏠')

st.write("""
This app is a tool to analyse the difference between buying and renting a property. 
It is done in a pure financial approach, it does not consider any personal prefferences or other non-financial factors that might affect this decision.

The difference from other buy vs rent comparisons is that here, both options use the same amount of cash outflows. 
This means that you will use the same amount of money in both scenarios, only in a different way (e.g. invetments instead of the initial down payment)""")

st.subheader('1. Mutual Inputs ⚖️')
st.write('Here you can change the main assumptions')

#mutual assumptions
with st.expander('Main Inputs'):
    property_value = st.number_input('Home Value', min_value=25000, max_value=1000000, value=250000,step=1000)
    stay_years = st.number_input('Staying Years', min_value=1, max_value=30, value=10,step=1)

st.subheader('2. Specific Inputs 💰')

#buying assumptions
with st.expander('Buy Inputs'):
    down_payment_percentage = st.number_input('Down Payment %', min_value=0.00, max_value=100.00, value=10.00,step=1.0)
    mortgage_rate = st.number_input('Mortgage Rate %', min_value=-1.00, max_value=20.00, value=6.00,step=1.0)
    mortgage_years = st.number_input('Mortgage Years', min_value=5, max_value=30, value=20,step=1)
    property_value_increase = st.number_input('Porperty Price Increase per year %', min_value=0.00, max_value=50.00, value=2.00,step=1.0)
    legal_fees = st.number_input('Legal Fees %', min_value=0.00, max_value=10.00,value=1.00,step=0.5)
    maintenance_rate = st.number_input('Maintenance Annual Rate %',min_value=0.00,max_value=20.00,value=0.50,step=0.50)

#rent assumptions
with st.expander('Rent Inputs'):
    rental_yield = st.number_input('Rental Yield %',min_value=0.00,max_value=20.00,value=5.00,step=1.0)
    investment_interest_rate = st.number_input('Return on Investment %',min_value=0.00,max_value=50.00, value=8.00,step=1.0)
    rental_increase = st.number_input('Rental Increase per Year %',min_value=0.00,max_value=50.00, value=2.00,step=1.0)
    rent_deposit = st.number_input('Rent deposit (Months)', min_value=0, max_value=12, value=2,step=1)

#buying calculations
down_payment = property_value * down_payment_percentage/100
mortgage_amount = property_value - down_payment
future_home_value = property_value * (1+property_value_increase/100)**(stay_years-1)
if mortgage_rate == 0:
    monthly_mortgage = mortgage_amount / (mortgage_years * 12)
    property_value_payer = future_home_value - mortgage_amount * (1- stay_years / max(mortgage_years,stay_years))
else:
    monthly_mortgage = mortgage_amount * (mortgage_rate/100/12) * (1 + mortgage_rate/100/12)**(mortgage_years*12) / ((1 + mortgage_rate/100/12)**(mortgage_years*12) - 1)
    property_value_payer = future_home_value - mortgage_amount*((1+mortgage_rate/100/12)**(mortgage_years*12)-(1+mortgage_rate/100/12)**(stay_years*12))/((1+mortgage_rate/100/12)**(mortgage_years*12)-1)

total_mortgage = monthly_mortgage * 12 * min(stay_years,mortgage_years)

buying_cost = property_value * legal_fees/100
selling_cost = future_home_value * legal_fees/100

#renting calculation
monthly_rent = property_value * rental_yield / 100 / 12
if rental_increase == 0:
    total_rent = monthly_rent * 12 * stay_years
else:
    total_rent = monthly_rent * 12 * (1-(1+rental_increase/100)**stay_years)/(1-(1+rental_increase/100))
rent_deposit = monthly_rent * rent_deposit
#pending: Investment; ROI

#df for house value (year)
base_df = pd.DataFrame({'Year': range(1,1 + stay_years,1)})
base_df['Property_Value'] = property_value
base_df['Rent'] = monthly_rent*12
for i in range(1, len(base_df)):
    prev = base_df.loc[i-1, 'Property_Value']
    base_df.loc[i, 'Property_Value'] = prev * (1 + property_value_increase/100)
    prev = base_df.loc[i-1, 'Rent']
    base_df.loc[i, 'Rent'] = prev * (1 + rental_increase/100)
base_df['Maintenance'] = round(base_df['Property_Value'] * maintenance_rate/100,2)

#buy - cash flow table
buy_cf = pd.DataFrame({'Month': range(1,1 + stay_years*12,1)})
buy_cf['Year'] = buy_cf['Month'].apply(lambda x: np.ceil(x/12))
buy_cf.loc[buy_cf['Month'] == 1,'Down_Payment'] = round(-down_payment,0)
buy_cf.loc[buy_cf['Month'] == 1,'Legal_Fees'] = round(-buying_cost,0)
buy_cf.loc[buy_cf['Month'] == stay_years*12,'Legal_Fees'] = round(-selling_cost,0)
buy_cf['Mortgage'] = np.where(buy_cf['Year'] <= mortgage_years,round(-monthly_mortgage,0),0)
buy_cf.loc[buy_cf['Month'] == stay_years*12,'Sale'] = round(property_value_payer)
buy_cf['Maintenance'] = round(buy_cf['Year'].map(-base_df.set_index('Year')['Maintenance'])/12,0)
buy_cf['Total'] = buy_cf.iloc[:,2:].sum(axis=1)

#rent - cash flow table
rent_cf = pd.DataFrame({'Month': range(1,1 + stay_years*12,1)})
rent_cf['Year'] = rent_cf['Month'].apply(lambda x: np.ceil(x/12))
rent_cf.loc[rent_cf['Month'] == 1,'Deposit'] = round(-rent_deposit,0)
rent_cf.loc[rent_cf['Month'] == stay_years*12,'Deposit'] = round(rent_deposit,0)
rent_cf['Rent'] = round(rent_cf['Year'].map(-base_df.set_index('Year')['Rent'])/12,0)
rent_cf['Sub-Total'] = rent_cf.iloc[:,2:].sum(axis=1)

#investments
buy_cf_outflows = buy_cf.drop(columns=['Sale','Total'])
buy_cf_outflows['Total'] = buy_cf_outflows.iloc[:,2:].sum(axis=1)
inv_df = pd.merge(rent_cf, buy_cf_outflows[['Total','Month']], on='Month')
inv_df.rename(columns={'Total':'Buy_Total','Sub-Total':'Rent_Total'},inplace=True)
invest = inv_df['Buy_Total'] - inv_df['Rent_Total']

#rent investments
inv_df['Rent_Investment'] = np.where(invest<0,invest,0)
inv_df.loc[rent_cf['Month'] == stay_years*12,'Rent_Investment'] = 0 #remove final investment
inv_df['Rent_Interest'] = 0
inv_df['Rent_Capital'] = -inv_df['Rent_Investment']
for i in range(1, len(inv_df)):
    prev = inv_df.loc[i-1, 'Rent_Capital']
    interest = round(prev * ((1+investment_interest_rate/100)**(1/12)-1),2)
    investment = inv_df.loc[i, 'Rent_Capital']
    inv_df.loc[i, 'Rent_Interest'] = interest
    inv_df.loc[i, 'Rent_Capital'] = prev + interest + investment

#buy investments
inv_df['Buy_Investment'] = np.where(invest>0,-invest,0)
inv_df.loc[rent_cf['Month'] == stay_years*12,'Buy_Investment'] = 0 #remove final investment
inv_df['Buy_Interest'] = 0
inv_df['Buy_Capital'] = -inv_df['Buy_Investment']
for i in range(1, len(inv_df)):
    prev = inv_df.loc[i-1, 'Buy_Capital']
    interest = round(prev * ((1+investment_interest_rate/100)**(1/12)-1),2)
    investment = inv_df.loc[i, 'Buy_Capital']
    inv_df.loc[i, 'Buy_Interest'] = interest
    inv_df.loc[i, 'Buy_Capital'] = prev + interest + investment


#rent - cash flow table
rent_cf.drop(columns='Sub-Total', inplace=True)
rent_cf.loc[rent_cf['Month'] == stay_years*12,'Investment_Capital'] = round(inv_df.loc[inv_df['Month'] == stay_years*12, 'Rent_Capital'],0)
rent_cf['Investment'] = round(inv_df['Rent_Investment'],0)
rent_cf['Total'] = round(rent_cf.iloc[:,2:].sum(axis=1),0)

#buy - add investments
buy_cf.drop(columns='Total', inplace=True)
buy_cf.loc[buy_cf['Month'] == stay_years*12,'Investment_Capital'] = round(inv_df.loc[inv_df['Month'] == stay_years*12, 'Buy_Capital'],0)
buy_cf['Investment'] = round(inv_df['Buy_Investment'],0)
buy_cf['Total'] = round(buy_cf.iloc[:,2:].sum(axis=1),0)

buy_sums = buy_cf.iloc[:,2:].sum(axis=0)
rent_sums = rent_cf.iloc[:,2:].sum()

buy_sums.name = 'Buy'
rent_sums.name = 'Rent'

rent_sums.drop(labels='Deposit', inplace=True)

st.divider()

st.subheader('3. Analysis 📊')

col1,col2 = st.columns(2)

col1.dataframe(buy_sums)
col2.dataframe(rent_sums)

with st.expander('Cash Flow'):
    st.subheader('Buy')
    st.dataframe(buy_cf,use_container_width=True)
    st.subheader('Rent')
    st.dataframe(rent_cf,use_container_width=True)
    st.dataframe(inv_df)

st.write(f"""
**Analysis:**
Based on the inputs provided, the total value of the buying option at 
the end of {stay_years} years was {int(buy_cf['Total'].sum()):,}. 
Compared to the total rent value of {int(rent_cf['Total'].sum()):,}.
""")

st.divider()

st.subheader("Feedback 📨")

mail = st.secrets['MAIL']
mail_pass = st.secrets['MAIL_PASS']

with st.form("feedback_form"):
    user_feedback = st.text_area("Please share your feedback")
    submitted = st.form_submit_button("Submit")
    if submitted:
        # Construct an email message
        msg = EmailMessage()
        msg['Subject'] = "Streamlit App Feedback" 
        msg['From'] = 'thisisfrom@mail.com'
        msg['To'] = mail
        
        # Add feedback as message body
        msg.set_content(user_feedback)
        
        # Send the message
        with smtplib.SMTP("smtp.gmail.com", port=587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(mail, mail_pass)
            smtp.send_message(msg)
            
        st.success("Feedback submitted!")

st.write('Disclaimer: this is not a financial advice!')

st.write("""
This analysis uses the following assumptions:
1. You have the option of either buy or rent the same or similar property
2. Have enough money to pay the outflows
3. Can access a mortgage
4. Can invest your disposable income
5. Cash outflows for both options are the same 
6. All investment returns are reinvested for the period of the stay
7. You will move out at some point in the future""")


#things to try:
# - Add an optional email from the sender?
# - inputs at 0%
# - add sensitivity analysis (graphs, high sensitivity inptus)
# - all investments are made at the end of the period (?) 
#things to fix:
# - buy option investment: check initial investment
# - rent increase rate = 0 gives an error (same with property increase%)
# - when stay is higher than mortgage year (property value)
