import streamlit as st
import pandas as pd 
import numpy as np

st.title('Buy vs Rent Analysis')

col1, col2 = st.columns(2)

#mutual assumptions
property_value = col2.number_input('Home Value', min_value=100000, max_value=1000000, value=250000)
stay_years = col2.number_input('Stay in Years', min_value=5, max_value=30, value=10)

#buying assumptions
down_payment_percentage = col1.number_input('Down Payment %', min_value=5.00, max_value=20.00, value=10.00)
mortgage_rate = col1.number_input('Mortgage Rate %', min_value=-1.00, max_value=20.00, value=6.00)
mortgage_years = col1.number_input('Mortgage Years', min_value=5, max_value=30, value=20)
property_value_increase = col1.number_input('Porperty Price Increase per year %', min_value=0.00, max_value=50.00, value=6.00)
legal_fees = col1.number_input('Legal Fees', min_value=0.00, max_value=5.00,value=1.00)
maintenance_rate = col1.number_input('Maintenance Annual Rate',min_value=0.00,max_value=10.00,value=1.00)

#rent assumptions
rental_yield = col2.number_input('Rental Yield %',min_value=0.00,max_value=20.00,value=5.00)
investment_interest_rate = col2.number_input('Return on Investment %',min_value=0.00,max_value=50.00, value=8.00)
rental_increase = col2.number_input('Rental Increase per year %',min_value=0.00,max_value=50.00, value=2.00)
rent_deposit = col2.number_input('Rent deposit (Months)', min_value=0, max_value=12, value=2)

#buying calculations
down_payment = property_value * down_payment_percentage/100
mortgage_amount = property_value - down_payment
monthly_mortgage = mortgage_amount * (mortgage_rate/100/12) * (1 + mortgage_rate/100/12)**(mortgage_years*12) / ((1 + mortgage_rate/100/12)**(mortgage_years*12) - 1)
total_mortgage = monthly_mortgage * 12 * stay_years
future_home_value = property_value * (1+property_value_increase/100)**(stay_years-1)
property_value_payer = future_home_value - mortgage_amount*((1+mortgage_rate/100/12)**(mortgage_years*12)-(1+mortgage_rate/100/12)**(stay_years*12))/((1+mortgage_rate/100/12)**(mortgage_years*12)-1)
buying_cost = property_value * legal_fees/100
selling_cost = future_home_value * legal_fees/100
maintenance = property_value *  maintenance_rate/100 * (1-(1+property_value_increase/100)**stay_years)/(1-(1+property_value_increase/100))

#renting calculation
monthly_rent = property_value * rental_yield / 100 / 12
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
buy_cf['Mortgage'] = round(-monthly_mortgage,0)
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
inv_df = pd.merge(rent_cf, buy_cf[['Total','Month']], on='Month')
inv_df['Rent_Investment'] = np.where(inv_df['Total'] - inv_df['Sub-Total']<0,inv_df['Total'] - inv_df['Sub-Total'],0)
inv_df['Interest'] = 0
inv_df['Capital'] = -inv_df['Rent_Investment']
for i in range(1, len(inv_df)):
    prev = inv_df.loc[i-1, 'Capital']
    interest = round(prev * ((1+investment_interest_rate/100)**(1/12)-1),2)
    investment = inv_df.loc[i, 'Capital']
    inv_df.loc[i, 'Interest'] = interest
    inv_df.loc[i, 'Capital'] = prev + interest + investment

#rent - cash flow table
rent_cf.drop(columns='Sub-Total', inplace=True)
rent_cf.loc[rent_cf['Month'] == stay_years*12,'Investment_Capital'] = round(inv_df.loc[inv_df['Month'] == stay_years*12, 'Capital'],0)
rent_cf['Investment'] = round(inv_df['Rent_Investment'],0)
rent_cf['Total'] = round(rent_cf.iloc[:,2:].sum(axis=1),0)

buy_sums = buy_cf.iloc[:,2:].sum(axis=0)
rent_sums = rent_cf.iloc[:,2:].sum()

buy_sums.name = 'Buy'
rent_sums.name = 'Rent'

col1, col2 = st.columns(2)
col1.title('Buy')
col1.dataframe(buy_sums)
col2.title('Rent')
col2.dataframe(rent_sums)

with st.expander('Cash Flow'):
    st.title('Buy')
    st.dataframe(buy_cf)
    st.title('Rent')
    st.dataframe(rent_cf)

st.write(f"""
**Analysis:**
Based on the inputs provided, the total value of the buying option at 
the end of {stay_years} years was {int(buy_cf['Total'].sum()):,}. 
Compared to the total rent value of {int(rent_cf['Total'].sum()):,}.
""")