import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.title( "Financial Modeling & Projections Dashboard" )

with st.sidebar.form(key='BaselineInputs'):
    st.title("Baseline Inputs")
    premium = st.number_input("Enter Premium amount", min_value=0, max_value=10000, value=1000, step = 10)
    avgclaimsize = st.number_input("Enter Average Claim Amount", min_value=0, max_value=50000, value=21000, step = 100)
    marketsize = st.number_input("Enter Market Size of policyholders", value=1000000, step = 1000)
    marketshare = st.slider('market share', min_value = 0.0, max_value = 100.0, value = 10.0, step = 0.01 )
    operatingexpenses = st.slider('Operating expenses', min_value = 0.0, max_value = 100.0, value = 20.0, step = 0.01 )
    investmentreturn = st.slider('investment return', min_value = -20.0, max_value = 20.0, value = 5.0, step = 0.01 )
    marketgrowth = st.slider('Market Growth (CAGR)', min_value = -10.0, max_value = 10.0, value = 5.0, step = 0.01 )
    marketsharegrowth = st.slider('Market Share Growth (CAGR)', min_value = -10.0, max_value = 10.0, value = 5.0, step = 0.01 )
    higherpremiumgearingrange = st.slider('Gearing Range for higher premium', min_value = 1.0, max_value = 5.0, value = (2.0, 2.5))
    lowerpremiumgearingrange = st.slider('Gearing Range for lower premium', min_value = 1.0, max_value = 5.0, value = (1.5, 1.0) )
    predictiontimeline = st.number_input("Prediction Timeline(years)", value=5)
    #not used currently in calculation
    Fraudloss = st.slider('Fraud loss', min_value = 0.0, max_value = 5.0, value = 0.0, step = 0.01 )
    #not used currently in calculation
    Competitivepricing = st.slider('Competitive Pricing', min_value = 0.0, max_value = 5.0, value = 0.0, step = 0.01 )
    submitted = st.form_submit_button("Submit")
	
def PnLEstimateforScenario(Scenario):    
    MarketSize = Scenario["MarketSize"] * np.power((1+ Scenario["MarketGrowth"]), Scenario["TimeHorizon"])        
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
    
    Expenses = Scenario["OperatingExpenses"] * TotalPremium
    InvestmentAmount = np.maximum(TotalPremium - ClaimReserve - Expenses, 0)    
    InvestmentIncome = InvestmentAmount * np.exp(Scenario["ReturnRate"]) - InvestmentAmount
    PnL = InvestmentAmount + InvestmentIncome - ClaimInitial - Expenses
    
    return { "MarketSize" : MarketSize, "NumPolicyHolders" : NewNumPolicyHolders, "Premium": TotalPremium, "NumClaims": NumClaims, "TotalClaimAmount":TotalClaimAmount,
	     "ClaimInitial": ClaimInitial, "ClaimReserve": ClaimReserve, "Expenses": Expenses, "InvestmentAmount": InvestmentAmount, "InvestmentIncome": InvestmentIncome,
	    "PnL": PnL }

Baseline = {"Premium": premium, 'AvgClaimSize': avgclaimsize, "MarketSize": marketsize, "MarketShare": marketshare/100, 
            "ReturnRate": investmentreturn/100,             
            "ClaimProbability": 1.6/100.0,
            "PremiumChangePercentage": 0.0, "MarketGrowth": marketgrowth/100, "OperatingExpenses": operatingexpenses/100
            }

Scenarios = { 
	      "Baseline": {"PremiumChangePercentage": 0, "Gearing": 0 }, 
	      "Premium Higher Gearing High": {"PremiumChangePercentage": 3, "Gearing": higherpremiumgearingrange[0] }, 
	      "Premium Higher Gearing Low": {"PremiumChangePercentage": 3, "Gearing": higherpremiumgearingrange[1] }, 
	      "Premium Lower Gearing High": {"PremiumChangePercentage": -3, "Gearing": lowerpremiumgearingrange[0] }, 
	      "Premium Lower Gearing Low": {"PremiumChangePercentage": -3, "Gearing": lowerpremiumgearingrange[1] }, 
	    }

PnLScenarios = {}
results = {}
if submitted:
	for key in Scenarios:			
		PnLYearly = []
		for i in range(predictiontimeline):
			Scenario = Scenarios[key]		
			Scenario = {**Baseline, **Scenario}
			Scenario.update({"TimeHorizon" : i })
			result = PnLEstimateforScenario( Scenario)
			PnLYearly.append(result["PnL"]/1e6)
			#st.write( key + " Year " + str(i+1) + " : " +'${:,.0f}'.format(PnL))
		PnLScenarios.update({key:PnLYearly})
		results.update({key:result})
	
	PnLScenarios.update({"Year": range(1, predictiontimeline +1 ) })
	df = pd.DataFrame.from_dict(PnLScenarios)
	df.set_index('Year', inplace=True)  

	fig, axs = plt.subplots(figsize=(20, 8))
	df.plot.line( ax = axs, xlabel = "Year", ylabel = "Profit ($mn)", title ="Development of Mean Overall Profit", marker='o', xticks = range(1, predictiontimeline + 1) )

	st.pyplot(fig)
