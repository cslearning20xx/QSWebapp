import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import chainladder as cl
import json
import os
import s3fs

# Create connection object.
# `anon=False` means not anonymous, i.e. it uses access keys to pull data.
fs = s3fs.S3FileSystem(anon=False)

# Retrieve file contents.
# Uses st.experimental_memo to only rerun when the query changes or after 10 min.
@st.experimental_memo(ttl=600)
def read_file(filename):
    with fs.open(filename) as f:
        return f.read().decode("utf-8")


#files = fs.ls('qs-streamlit')
#for file in files:
	#fs.delete(file)
	#st.write('deleted file')
		  
#with fs.open('qs-streamlit/abc.txt', 'rb') as f:
	#data = json.load(f)
	#st.write(data)
    
st.title( "Financial Modeling & Projections Dashboard" )

with st.sidebar.form(key='LoadScenarios'):
	files = fs.ls('qs-streamlit')
	files = [ x.split("/")[1].split(".")[0] for x in files ]
	scenariooptions = st.multiselect('Scenario Choices(s)', files, [] )
	showscenarios = st.form_submit_button("Show Scenarios")

	
with st.sidebar.form(key='RefreshScenarios'):
	refreshscenarios = st.form_submit_button("Refresh Scenario List")

with st.sidebar.form(key='TriggerDeleteScenarios'):
	deletescenarios = st.form_submit_button("Delete Existing Scenarios")
	
if deletescenarios:
	files = fs.ls('qs-streamlit')
	for file in files:
		fs.delete(file)	
		
with st.sidebar.form(key='BaselineInputs'):
    st.title("Input Parameters")
    riskmodel = st.selectbox('Choose Risk Model', ('GLM', 'CatBoost', 'TPOT'), index = 1)
    fraudmodel = st.selectbox('Choose Fraud Model', ('None','Support Vector Classifier', 'CatBoost', 'KNN'), index = 1)
    fraudloss = st.slider('Fraud loss probability adjustment', min_value = 0.0, max_value = 5.0, value = 0.0, step = 0.01, help = "Manual adjutment to model produced fraud probability" )
    lossreservingmodel = st.selectbox('Choose Loss Reserving Model', ('Standard Chain Ladder', 'Mack Chain Ladder', 'Bornhuetter Ferguson' ), index = 0)	
    lossreservingdevelopment = st.selectbox('Choose Loss Reserving Development Method', ('simple', 'volume' ), index = 0)	
    baselinepremium = st.number_input("Premium Amount", min_value=0, max_value=10000, value=1000, step = 10)
    avgclaimsize = st.number_input("Average Claim Severity", min_value=0, max_value=50000, value=21000, step = 100)
    marketsize = st.number_input("Enter Market Size of policyholders", value=1000000, step = 1000)
    marketshare = st.slider('Company Market Share', min_value = 0.0, max_value = 100.0, value = 10.0, step = 0.01 )
    operatingexpenses = st.slider('Operating Expenses', min_value = 0.0, max_value = 100.0, value = 30.0, step = 0.01 )
    investmentreturn = st.slider('Investment Expected Return', min_value = -20.0, max_value = 20.0, value = 6.0, step = 0.01 )
    marketgrowth = st.slider('Market Growth (CAGR)', min_value = -100.0, max_value = 100.0, value = 10.0, step = 0.01 )
    marketsharegrowth = st.slider('Market Share Growth (CAGR)', min_value = -100.0, max_value = 100.0, value = 15.0, step = 0.01 )
    premiumchange = st.slider("Premium Change %", min_value = -0.0, max_value = 100.0, value=0.0, step = 0.01)
    gearing = st.number_input("Gearing", value=1.0, step = 0.1)
    predictiontimeline = st.number_input("Prediction Timeline(years)", value=5)
    #not used currently in calculation
    Competitivepricing = st.slider('Competitive Pricing', min_value = -100.0, max_value = 100.0, value = 0.0, step = 0.01 )
    resinsuranceretentionratio = st.number_input("Reinsurance Retention Ratio", min_value = 0, max_value = 100, value=100 )
    scenarioname = st.text_input("Write Scenario name", help= "Ex: Scenario_Baseline, Scenario_BestCase, Scenario_WorstCase, Scenario_Pandemic",
				placeholder = "Scenario_Baseline")
    submitted = st.form_submit_button("Save Scenario")

def getChainLadderOutput(model, development_average ):
	origin_col = "Accident Year"
	development_col = "Development Year"
	value_col = "Claim"
	iscumulative = False	
	df_raw = pd.read_csv('Claims CLDataset.csv')
	traingle_data = cl.Triangle(data=df_raw,origin=origin_col,development=development_col,columns=value_col,cumulative=iscumulative)
	traingle_data = traingle_data.incr_to_cum()
	
	dev = cl.Development(average=development_average)
	transformed_triangle = dev.fit_transform(traingle_data)
	if model == 'Standard Chain Ladder':
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
		st.write("This model choice is not yet supported")
	LDF = model.ldf_.to_frame()
	IDF = transformed_triangle.link_ratio
	result = { "LDF": LDF, "Summary": summary, "IDF": IDF }
	return result
	
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
	     "PnL": round(PnL/1e6,2), "LDF": CLOutput['LDF'] }

def getClaimProbability(RiskModel):
	if RiskModel == 'Catboost':
		claimprobability = 1.6/100.0
	if RiskModel == 'GLM':
		claimprobability = 1.6/100.0
	else:
		claimprobability = 1.6/100.0
	return claimprobability

def getFraudProbability(FraudModel, fraudloss):
	if FraudModel == 'None':
		fraudprobability = 0
	else:
		fraudprobability = 0.005
	fraudprobability = fraudprobability + fraudloss/100
	return fraudprobability
	
PnLScenarios = {}
results = {}
if submitted:

	claimprobability = getClaimProbability( riskmodel )
	fraudprobability = getFraudProbability( fraudmodel, fraudloss )
	claimcount = claimprobability * marketsize
	claimcountwithfraud = round( claimcount * ( 1 + fraudprobability))
	
	lossratio = (claimprobability * avgclaimsize) / baselinepremium
	premium = round((claimcountwithfraud * avgclaimsize)/(lossratio * marketsize))
	
	Scenario = {"Premium": premium, 'AvgClaimSize': avgclaimsize, "MarketSize": marketsize, "MarketShare": marketshare/100, 
            "ReturnRate": investmentreturn/100,             
            "ClaimProbability": claimprobability, "FraudProbability": fraudprobability, 
            "PremiumChangePercentage": 0.0, "MarketGrowth": marketgrowth/100, "OperatingExpenses": operatingexpenses/100,
	    "lossreservingmodel": lossreservingmodel, "lossreservingdevelopment": lossreservingdevelopment,
	    "PremiumChangePercentage":premiumchange, "Gearing": gearing,	   
            }
	
	filename = "qs-streamlit/" + scenarioname + ".txt"
	json.dump(Scenario, fs.open( filename,'w'))

def readscenario(scenario):
	with fs.open('qs-streamlit/' + scenario + '.txt', 'rb') as f:
		data = json.load(f)
	return data
	
if showscenarios:
	for key in scenariooptions:
		PnLYearly = []
		ScenarioResult = []
		Scenario = readscenario(key)
		for i in range(predictiontimeline):
			Scenario.update({"TimeHorizon" : i })
			result = PnLEstimateforScenario( Scenario)
			ScenarioResult.append(result)
			PnLYearly.append(result["PnL"])
			
		PnLScenarios.update({key:PnLYearly})
		results.update({key:ScenarioResult})
	
	PnLScenarios.update({"Year": range(1, predictiontimeline +1 ) })
	df = pd.DataFrame.from_dict(PnLScenarios)
	df.set_index('Year', inplace=True)  
	
	st.write(df)
	
	#st.header( "Loss Reserving") 
	#cl1, cl2 = st.columns(2)
	#ldf = results["Baseline"][0]["LDF"]
	#fig1, axs1 = plt.subplots(figsize=(30, 10))
	#ldf.T.plot.line(ax = axs1, marker= 'o', xlabel ="Year", ylabel = "Loss Development Factor", title ="Loss Development Factors" )
	#cl1.pyplot(fig1)
	#cl2.write(ldf)
	
	#st.header( "Projected PnL") 
	#fig, axs = plt.subplots(figsize=(30, 15))
	#df.plot.line( ax = axs, xlabel = "Year", ylabel = "Profit ($mn)", title ="Development of Mean Overall Profit", marker='o', xticks = range(1, predictiontimeline + 1) )

	#st.pyplot(fig)
	
