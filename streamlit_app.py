import streamlit as st
import pandas as pd
 
st.write( "Welcome to QS!" )

with st.sidebar.form(key='BaselineInputs'):
    st.title("Baseline Inputs")
    premium = st.number_input("Enter Premium amount", min_value=0, max_value=10000, value=1000, step = 10)
    avgclaimsize = st.number_input("Enter Average Claim Amount", min_value=0, max_value=50000, value=21000, step = 100)
    marketsize = st.number_input("Enter Market Size of policyholders", value=1000000, step = 1000)
    marketshare = st.slider('market share', min_value = 0.0, max_value = 100.0, value = 10.0, step = 0.01 )
    claimprobability = st.slider('market share', min_value = 0.0, max_value = 10.0, value = 1.6, step = 0.01 )
    investmentreturn = st.slider('investment return', min_value = -20.0, max_value = 20.0, value = 5.0, step = 0.01 )
    priceelasticity = st.number_input("Price Elasticity", value = -0.6 )
    submitted = st.form_submit_button("Submit")
	
col1, col2 = st.sidebar.columns(2)

with col1:
    with st.form('Form1'):
        marketgrowth1 = st.slider('market growth', min_value = 0.0, max_value = 20.0, value = 2.0, step = 0.01 )
        premiumchange1 = st.slider('change in premium', min_value = 0.0, max_value = 10.0, value = -1.0, step = 0.01 )
        investmentreturn1 = st.slider('investment return', min_value = -20.0, max_value = 20.0, value = 5.0, step = 0.01 )
        submitted1 = st.form_submit_button('Submit Scenario1')

with col2:
    with st.form('Form2'):
        marketgrowth2 = st.slider('market growth', min_value = 0.0, max_value = 20.0, value = 2.0, step = 0.01 )
        premiumchange2 = st.slider('change in premium', min_value = 0.0, max_value = 10.0, value = 1.0, step = 0.01 )
        investmentreturn2 = st.slider('investment return', min_value = -20.0, max_value = 20.0, value = 2.0, step = 0.01 )
        submitted2 = st.form_submit_button("Submit Scenario2")

def PnLEstimateforScenario(Scenario):
     
    MarketSize = Scenario["MarketSize"] * (1+ Scenario["MarketGrowth"])    
    NumPolicyHolders = MarketSize * Scenario["MarketShare"] 
    NewPremium = Scenario['Premium'] * ( 1 + Scenario['PremiumChangePercentage'] )    
    DemandChange = getDemandChangeForPremiumChange(Scenario['PremiumChangePercentage'])
    NewNumPolicyHolders = ( 1- DemandChange) * NumPolicyHolders
    
    TotalPremium = NewPremium * NewNumPolicyHolders
    NumClaims = NewNumPolicyHolders * Scenario["ClaimProbability"]
    TotalClaimAmount = NumClaims * Scenario['AvgClaimSize']
    
    # this is really reverse engineering, probably there is a better way to do
    ClaimInitial = round(TotalClaimAmount/CumulativeClaimRatios[-1],0)
    ClaimReserve = round(TotalClaimAmount - ClaimInitial, 0)
    
    Expenses = 0.25 * TotalPremium
    InvestmentAmount = TotalPremium - ClaimReserve - Expenses    
    InvestmentIncome = InvestmentAmount * math.exp(Scenario["ReturnRate"]) - InvestmentAmount
    PnL = InvestmentAmount + InvestmentIncome - ClaimInitial - Expenses
    
    return PnL
	
if submitted1:
	st.write("you filled scenario 1")
if submitted2:
	st.write("you filled scenario 2")
	
