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
    investmentreturn = st.slider('investment return', min_value = -20.0, max_value = 20.0, value = 5.0, step = 0.01 )    
    submitted = st.form_submit_button("Submit")
	
def PnLEstimateforScenario(Scenario):     
    MarketSize = Scenario["MarketSize"] * (1+ Scenario["MarketGrowth"])    
    NumPolicyHolders = MarketSize * Scenario["MarketShare"] 
    NewPremium = Scenario['Premium'] * ( 1 + Scenario['PremiumChangePercentage']/100 )    
    DemandChange = Scenario['PremiumChangePercentage'] * Scenario['Gearing']
    NewNumPolicyHolders = ( 1- DemandChange/100) * NumPolicyHolders
    
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

Baseline = {"Premium": premium, 'AvgClaimSize': avgclaimsize, "MarketSize": marketsize, "MarketShare": marketshare/100, 
            "ReturnRate": investmentreturn/100,             
            "ClaimProbability": 1.6/100.0,
            "PremiumChangePercentage": 0.0, "MarketGrowth": 0.0
            }

Scenarios = { "PremiumHigh_GearingHigh": {"PremiumChangePercentage": 3, "Gearing": 2.5 }, 
	      "PremiumHigh_GearingLow": {"PremiumChangePercentage": 3, "Gearing": 2.0 }, 
	    }
if submitted:
	for key in Scenarios:
		Scenario = Scenarios[key]
		Scenario = {**Baseline, **Scenario}
		PnL = PnLEstimateforScenario( Scenario)
		st.write( key + ":" +'${:,.0f}'.format(PnL))
	
	
