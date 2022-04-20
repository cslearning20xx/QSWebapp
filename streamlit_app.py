import streamlit as st
import pandas as pd
import numpy as np


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
        st.title("Hypothetical Up Scenario")
        marketgrowth1 = st.slider('market growth', min_value = 0.0, max_value = 20.0, value = 2.0, step = 0.01 )
        premiumchange1 = st.slider('change in premium', min_value = 0.0, max_value = 10.0, value = -1.0, step = 0.01 )
        investmentreturn1 = st.slider('investment return', min_value = -20.0, max_value = 20.0, value = 5.0, step = 0.01 )
        submitted1 = st.form_submit_button('Submit Up Scenario')

with col2:
    with st.form('Form2'):
        st.title("Hypothetical Down Scenario")
        marketgrowth2 = st.slider('market growth', min_value = 0.0, max_value = 20.0, value = 2.0, step = 0.01 )
        premiumchange2 = st.slider('change in premium', min_value = 0.0, max_value = 10.0, value = 1.0, step = 0.01 )
        investmentreturn2 = st.slider('investment return', min_value = -20.0, max_value = 20.0, value = 2.0, step = 0.01 )
        submitted2 = st.form_submit_button("Submit Down Scenario")

def PnLEstimateforScenario(Scenario):
     
    MarketSize = Scenario["MarketSize"] * (1+ Scenario["MarketGrowth"])    
    NumPolicyHolders = MarketSize * Scenario["MarketShare"] 
    NewPremium = Scenario['Premium'] * ( 1 + Scenario['PremiumChangePercentage'] )    
    DemandChange = Scenario['PremiumChangePercentage'] * Scenario['Elasticity']
    NewNumPolicyHolders = ( 1- DemandChange) * NumPolicyHolders
    
    TotalPremium = NewPremium * NewNumPolicyHolders
    NumClaims = NewNumPolicyHolders * Scenario["ClaimProbability"]
    TotalClaimAmount = NumClaims * Scenario['AvgClaimSize']
	
    CL = [1.4259, 1.0426, 1.0270, 1.0137, 1.0115, 1.0075]
    CumulativeClaimRatios = [1]
    for i in range(1, len(CL)):
        CumulativeClaimRatios.append(CumulativeClaimRatios[i-1]*CL[i])
	
    # this is really reverse engineering, probably there is a better way to do
    ClaimInitial = round(TotalClaimAmount/CumulativeClaimRatios[-1],0)
    ClaimReserve = round(TotalClaimAmount - ClaimInitial, 0)
    
    Expenses = 0.25 * TotalPremium
    InvestmentAmount = TotalPremium - ClaimReserve - Expenses    
    InvestmentIncome = InvestmentAmount * np.exp(Scenario["ReturnRate"]) - InvestmentAmount
    PnL = InvestmentAmount + InvestmentIncome - ClaimInitial - Expenses
    
    return PnL

Baseline = {"Premium": premium, 'AvgClaimSize': avgclaimsize, "MarketSize": marketsize, "MarketShare": marketshare/100, "MarketGrowth": 0.0,
            "ReturnRate": investmentreturn/100,             
            "Elasticity": priceelasticity,  "ClaimProbability": claimprobability/100,
            "PremiumChangePercentage": 0.0, "MarketGrowth": 0.0
            }

if submitted1:
	ScenarioUp = {"PremiumChangePercentage": premiumchange1/100.0, "MarketGrowth": marketgrowth1/100.0, "ReturnRate": investmentreturn1/100 }
	ScenarioUp = {**Baseline, **ScenarioUp}
	PnLScenarioUp = PnLEstimateforScenario( ScenarioUp)
	st.write(PnLScenarioUp)
if submitted2:
	ScenarioDown = {"PremiumChangePercentage": premiumchange2/100.0, "MarketGrowth": marketgrowth2/100.0, "ReturnRate": investmentreturn2/100 }
	ScenarioDown = {**Baseline, **ScenarioDown}
	PnLScenarioDown = PnLEstimateforScenario(ScenarioDown)	
	st.write(PnLScenarioDown)
	
