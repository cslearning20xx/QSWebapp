import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title( "Financial Modeling & Projections Dashboard" )

with st.sidebar.form(key='BaselineInputs'):
    st.title("Input Parameters")
    riskmodel = st.selectbox('Choose Risk Model', ('GLM', 'CatBoost', 'TPOT'), index = 1)
    lossreservingmodel = st.selectbox('Choose Loss Reserving Model', ('Chain Ladder', 'Mack Chain Ladder', 'Bornhuetter Ferguson' ), index = 0)	
    lossreservingdevelopment = st.selectbox('Choose Loss Reserving Development Method', ('simple', 'volume' ), index = 0)	
    premium = st.number_input("Premium Amount", min_value=0, max_value=10000, value=1000, step = 10)
    avgclaimsize = st.number_input("Average Claim Severity", min_value=0, max_value=50000, value=21000, step = 100)
    marketsize = st.number_input("Enter Market Size of policyholders", value=1000000, step = 1000)
    marketshare = st.slider('Company Market Share', min_value = 0.0, max_value = 100.0, value = 10.0, step = 0.01 )
    operatingexpenses = st.slider('Operating Expenses', min_value = 0.0, max_value = 100.0, value = 35.0, step = 0.01 )
    investmentreturn = st.slider('Investment Expected Return', min_value = -20.0, max_value = 20.0, value = 5.0, step = 0.01 )
    marketgrowth = st.slider('Market Growth (CAGR)', min_value = -20.0, max_value = 20.0, value = 2.0, step = 0.01 )
    marketsharegrowth = st.slider('Market Share Growth (CAGR)', min_value = -50.0, max_value = 50.0, value = 5.0, step = 0.01 )
    premiumchangerange = st.slider('Premium high low scenario', min_value = -5.0, max_value = 5.0, value = (-3.0, 3.0))
    higherpremiumgearingrange = st.slider('Gearing Range for higher premium', min_value = 1.0, max_value = 5.0, value = (2.0, 2.5))
    lowerpremiumgearingrange = st.slider('Gearing Range for lower premium', min_value = 1.0, max_value = 5.0, value = (1.5, 1.0) )
    predictiontimeline = st.number_input("Prediction Timeline(years)", value=5)
    #not used currently in calculation
    Fraudloss = st.slider('Fraud loss', min_value = 0.0, max_value = 5.0, value = 0.0, step = 0.01 )
    #not used currently in calculation
    Competitivepricing = st.slider('Competitive Pricing', min_value = 0.0, max_value = 5.0, value = 0.0, step = 0.01 )
    resinsuranceretentionratio = st.number_input("Reinsurance Retention Ratio", min_value = 0, max_value = 1, value=0 )
    submitted = st.form_submit_button("Submit")

def getChainLadderOutput(model, development_average ):
	origin_col = "Accident Year"
	development_col = "Development Year"
	value_col = "Claim"
	iscumulative = False
	
	import chainladder as cl
	import numpy as np
	import pandas as pd
	df_raw = pd.read_csv('/home/ec2-user/qs/data/QSDataset/Claims CLDataset.csv')
	traingle_data = cl.Triangle(data=df_raw,origin=origin_col,development=development_col,columns=value_col,cumulative=iscumulative)
	traingle_data = traingle_data.incr_to_cum()
	
	dev = cl.Development(average=development_average)
	transformed_triangle = dev.fit_transform(data)	
    	if model == 'Standard Chain Ladder' :
		model = cl.Chainladder().fit(transformed_triangle)
        	ibnr = model.ibnr_.to_frame()
        	ultimate = model.ultimate_.to_frame()
        	latest = model.latest_diagonal.to_frame()
        	summary = pd.concat([ latest, ibnr, ultimate ], axis=1)
        	summary.columns = ['Latest', 'IBNR', 'Ultimate']            
    	elif model == "Mack Chain Ladder":
        	model = cl.MackChainladder().fit(transformed_triangle)
        	summary = model.summary_.to_frame()        
    	elif model == "Bornhuetter Ferguson":
        	cl_ult = cl.Chainladder().fit(transformed_triangle).ultimate_
        	sample_weight = cl_ult * 0 + (cl_ult.sum() / cl_ult.shape[2])  # Mean Chainladder Ultimate
        	model = cl.BornhuetterFerguson(apriori=1).fit( X= transformed_triangle, sample_weight=sample_weight )
        	ibnr = model.ibnr_.to_frame()
        	ultimate = model.ultimate_.to_frame()
        	latest = ultimate - ibnr
		summary = pd.concat([ latest, ibnr, ultimate ], axis=1)
        	summary.columns = ['Latest','IBNR', 'Ultimate']        
    	else:
        	print("This model choice is not yet supported")
        
    	LDF = model.ldf_.to_frame()
    	IDF = transformed_triangle.link_ratio

    	result = { "LDF": LDF, "Summary": summary, "IDF": IDF }
	
def PnLEstimateforScenario(Scenario):    
    MarketSize = Scenario["MarketSize"] * np.power((1+ Scenario["MarketGrowth"]), Scenario["TimeHorizon"])        
    NumPolicyHolders = MarketSize * Scenario["MarketShare"]
    NewPremium = Scenario['Premium'] * ( 1 + Scenario['PremiumChangePercentage']/100 )        
    DemandChange = Scenario['PremiumChangePercentage'] * Scenario['Gearing']
    NewNumPolicyHolders = ( 1- DemandChange/100) * NumPolicyHolders
    
    TotalPremium = NewPremium * NewNumPolicyHolders
    NumClaims = round(NewNumPolicyHolders * Scenario["ClaimProbability"])
    TotalClaimAmount = NumClaims * Scenario['AvgClaimSize']
	
    CLOutput = getChainLadderOutput(lossreservingmodel, lossreservingdevelopment)
    CL = CLOutput['LDF'].iloc[0].values
    CumulativeClaimRatios = [1]
    for i in range(1, len(CL)):
        CumulativeClaimRatios.append(CumulativeClaimRatios[i-1]*CL[i])
	
    # this is really reverse engineering, probably there is a better way to do
    ClaimInitial = round(TotalClaimAmount/CumulativeClaimRatios[-1],0)
    ClaimReserve = round(TotalClaimAmount - ClaimInitial, 0)
    
    Expenses = Scenario["OperatingExpenses"] * TotalPremium
    InvestmentAmount = np.maximum(TotalPremium - TotalClaimAmount - Expenses, 0)    
    InvestmentIncome = InvestmentAmount * np.exp(Scenario["ReturnRate"]) - InvestmentAmount
    PnL = TotalPremium + InvestmentIncome - ClaimInitial - Expenses
    
    return { "MarketSize" : MarketSize, "NumPolicyHolders" : NewNumPolicyHolders, "Premium":NewPremium, "GWP": round(TotalPremium/1e6,2), "NumClaims": NumClaims, 
	     "TotalClaimAmount":round(TotalClaimAmount/1e6,2),"ClaimInitial": round(ClaimInitial/1e6,2), "ClaimReserve": round(ClaimReserve/1e6,2), "Expenses": round(Expenses/1e6,2),
	     "InvestmentAmount": round(InvestmentAmount/1e6), "InvestmentIncome": round(InvestmentIncome/1e6,2),
	     "PnL": round(PnL/1e6,2) }

def getClaimProbability(RiskModel):
	if RiskModel == 'Catboost':
		claimprobability = 1.6/100.0
	if RiskModel == 'GLM':
		claimprobability = 1.6/100.0
	else:
		claimprobability = 1.6/100.0
	return claimprobability

PnLScenarios = {}
results = {}
if submitted:
	Baseline = {"Premium": premium, 'AvgClaimSize': avgclaimsize, "MarketSize": marketsize, "MarketShare": marketshare/100, 
            "ReturnRate": investmentreturn/100,             
            "ClaimProbability": getClaimProbability( riskmodel ),
            "PremiumChangePercentage": 0.0, "MarketGrowth": marketgrowth/100, "OperatingExpenses": operatingexpenses/100,
	    "lossreservingmodel", lossreservingmodel, "lossreservingdevelopment", lossreservingdevelopment
            }

	Scenarios = { 
	      "Baseline": {"PremiumChangePercentage": 0, "Gearing": 0 }, 
	      "Premium Higher Gearing High": {"PremiumChangePercentage": premiumchangerange[1], "Gearing": higherpremiumgearingrange[0] }, 
	      "Premium Higher Gearing Low": {"PremiumChangePercentage": premiumchangerange[1], "Gearing": higherpremiumgearingrange[1] }, 
	      "Premium Lower Gearing High": {"PremiumChangePercentage": premiumchangerange[0], "Gearing": lowerpremiumgearingrange[0] }, 
	      "Premium Lower Gearing Low": {"PremiumChangePercentage": premiumchangerange[0], "Gearing": lowerpremiumgearingrange[1] }, 
	    }
	
	for key in Scenarios:			
		PnLYearly = []
		ScenarioResult = []
		for i in range(predictiontimeline):
			Scenario = Scenarios[key]		
			Scenario = {**Baseline, **Scenario}
			Scenario.update({"TimeHorizon" : i })
			result = PnLEstimateforScenario( Scenario)
			ScenarioResult.append(result)
			PnLYearly.append(result["PnL"])
			#st.write( key + " Year " + str(i+1) + " : " +'${:,.0f}'.format(PnL))
		PnLScenarios.update({key:PnLYearly})
		results.update({key:ScenarioResult})
	#st.write(results)
	PnLScenarios.update({"Year": range(1, predictiontimeline +1 ) })
	df = pd.DataFrame.from_dict(PnLScenarios)
	df.set_index('Year', inplace=True)  
	
	kpi1, kpi2, kpi3, kpi4, kpi5, kpi6, kpi7 = st.columns(7)

	# fill in those three columns with respective metrics or KPIs
	kpi1.metric(
    		label="Claim Frequency",
    		value= round(getClaimProbability( riskmodel ) * 100)
		)
	kpi2.metric(
    		label="Claim Severity",
    		value= avgclaimsize
		)
	
	kpi3.metric(
    		label="GWP",
    		value=str(round(results["Baseline"][0]["GWP"])) + " $mn",    		
		)
	
	kpi4.metric(
    		label="Policy Holders('000)",
    		value=round(results["Baseline"][0]["NumPolicyHolders"]/1000),    		
		)
	
	kpi5.metric(
    		label="Loss Ratio",
    		value= str(round(results["Baseline"][0]["TotalClaimAmount"]* 100/results["Baseline"][0]["GWP"], 0)) + " %",    		
		)
	
	kpi6.metric(
    		label="Expense Ratio",
    		value= str(round(results["Baseline"][0]["TotalClaimAmount"] * 100/results["Baseline"][0]["GWP"], 0)) + " %",    		
		)
	
	kpi7.metric(
    		label="Underwriting Profit Ratio",
    		value= str(round(results["Baseline"][0]["TotalClaimAmount"]* 100/results["Baseline"][0]["GWP"], 0)) + " %",    		
		)
	
	fig, axs = plt.subplots(figsize=(30, 15))
	df.plot.line( ax = axs, xlabel = "Year", ylabel = "Profit ($mn)", title ="Development of Mean Overall Profit", marker='o', xticks = range(1, predictiontimeline + 1) )

	st.pyplot(fig)
