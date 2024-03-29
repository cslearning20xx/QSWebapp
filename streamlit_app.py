import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import chainladder as cl
import json
import os
import s3fs
import requests
from st_aggrid import AgGrid

pd.set_option('display.max_columns', None)
st. set_page_config(layout="wide")

# Create connection object.
# `anon=False` means not anonymous, i.e. it uses access keys to pull data.
fs = s3fs.S3FileSystem(anon=False)

# Retrieve file contents.
# Uses st.experimental_memo to only rerun when the query changes or after 10 min.
@st.experimental_memo(ttl=600)
def read_file(filename):
    with fs.open(filename) as f:
        return f.read().decode("utf-8")
  
ip = "ec2-43-204-34-187.ap-south-1.compute.amazonaws.com"

st.title( "Financial Modeling & Projections Dashboard" )

with st.sidebar.form(key='GenerateBaseScenario'):	
	st.title("Baseline Scenario")
	basescenario = st.form_submit_button("Generate Base Scenario")

with st.sidebar.form(key='ShowBaselineparams'):		
	basescenarioparams = st.form_submit_button("Show Baseline Parameters")

with st.sidebar.form(key='BaselineInputs'):
    st.title("Generate New Scenarios")
    riskmodel = st.selectbox('Choose Risk Model', ('GLM', 'Catboost', 'TPOT'), index = 1)
    riskprobadjustment = st.slider('Risk probability adjustment', min_value = -5.0, max_value = 5.0, value = 0.0, step = 0.01, help = "Manual adjutment to model produced risk probability" )
    fraudmodel = st.selectbox('Choose Fraud Model', ('None','Support Vector Classifier', 'CatBoost', 'KNN'), index = 1)
    fraudloss = st.slider('Fraud loss probability adjustment', min_value = -5.0, max_value = 5.0, value = 0.0, step = 0.01, help = "Manual adjutment to model produced fraud probability" )
    lossreservingmodel = st.selectbox('Choose Loss Reserving Model', ('Standard Chain Ladder', 'Mack Chain Ladder', 'Bornhuetter Ferguson' ), index = 0)	
    lossreservingdevelopment = st.selectbox('Choose Loss Reserving Development Method', ('simple', 'volume' ), index = 0)	
    baselinepremium = st.number_input("Premium Amount ($)", min_value=0, max_value=10000, value=1000, step = 10)
    avgclaimsize = st.number_input("Average Claim Severity ($)", min_value=0, max_value=50000, value=8500, step = 100)
    baselinemarketsize = st.number_input("Enter Market Size of policyholders", value=1000000, step = 1000)
    baselinemarketshare = st.slider('Company Market Share(%)', min_value = 0.0, max_value = 100.0, value = 10.0, step = 0.01 )
    operatingexpenses = st.slider('Operating Expenses(%)', min_value = 0.0, max_value = 100.0, value = 30.0, step = 0.01, help ="operating expenses as % of GWP" )
    investmentreturn = st.slider('Investment Expected Return (%)', min_value = -20.0, max_value = 20.0, value = 6.0, step = 0.01, help = "expected return on inbestments done in financial portfolio consisting of stocks, bonds etc." )
    marketgrowth = st.slider('Market Growth (CAGR)(%)', min_value = -100.0, max_value = 100.0, value = 10.0, step = 0.01, help = "expectation of overall industry/segment growth")
    marketsharegrowth = st.slider('Market Share Growth (CAGR)(%)', min_value = -100.0, max_value = 100.0, value = 15.0, step = 0.01, help = "expectation of company's growth in upcoming years" )
    premiumchange = st.slider("Premium Change %", min_value = -20.0, max_value = 20.0, value=0.0, step = 0.01, help = "% change in premium amount in upcoming years for scenario analysis")
    gearing = st.number_input("Gearing", value=1.0, step = 0.1, help="Gearing factor represents the ratio of the proportionate change in volume to the proportionate deviation of the company premium from the market level. They are opposite signs, i.e., the volume falls more if the premium charged is higher")
    predictiontimeline = st.number_input("Prediction Timeline(years)", value=5, help= "time horizon to project P&L" )
    #not used currently in calculation
    Competitivepricing = st.slider('Competitive Pricing', min_value = -100.0, max_value = 100.0, value = 0.0, step = 0.01 )
    resinsuranceretentionratio = st.number_input("Reinsurance Retention Ratio", min_value = 0, max_value = 100, value=100 )
    largeloss = st.slider('Large Loss(% policies)', min_value = 0.0, max_value = 20.0, value = 0.0, step = 0.01, help = "% of policies impacted by large/catastrophic evenets" )
    largelossseverity = st.number_input("Large Loss Severity($)", min_value=0, max_value=50000, value=50000, step = 100, help = "Severity for catastrophic events" )
    noclaimdiscounts = st.text_input( "Provide No Claim Discount Mix", '0%@0%', help = "%discount@%policies, 20%@5%;10%@2% implies 20% discount for 5% of policies and 10% discount for 2% of policies" )
    scenarioname = st.text_input("Write Scenario name", help= "Ex: Scenario_Baseline, Scenario_BestCase, Scenario_WorstCase, Scenario_Pandemic")
    submitted = st.form_submit_button("Save Scenario")

with st.sidebar.form(key='ChooseAction'):
	files = fs.ls('qs-streamlit')
	files = [ x.split("/")[1].split(".")[0] for x in files ]
	scenariooptions = st.multiselect('Scenario Choices(s)', files, [], help = 'Baseline Scenario is always included by default' )
	action = st.selectbox('Choose action for scenarios', ["Run", "Delete", "Refresh Scenario List","Show Parameters"], index = 0, help = 'You can perform Run, Delete, Refresh and Show Parameters' )
	scenarioaction = st.form_submit_button("Submit")
	
def readscenario(scenario):
	with fs.open('qs-streamlit/' + scenario + '.txt', 'rb') as f:
		data = json.load(f)
	return data	
def getChainLadderOutput(model, development_average ):
		
	model = model.replace(" ", "%20")
	api_url = "http://" + ip + "/chainLadder?modelName=" + model + "&developmentAverage=" + development_average
	
	response = requests.get(api_url)	
	response = response.json()
	LDF = pd.DataFrame.from_dict(response['LDF'])
	
	result = { "LDF": LDF }
	
	return result

def performRun(scenariooptions):
	Scenariolist =[]
	ScenarioResultY0 = []
	for key in scenariooptions:
		PnLYearly = []
		ScenarioResult = []			
		Scenario = readscenario(key)
		Scenariolist.append(Scenario)
		for i in range(predictiontimeline):
			Scenario.update({"TimeHorizon" : i })
			result = PnLEstimateforScenario( Scenario)
			ScenarioResult.append(result)
			if i == 0:
				ScenarioResultY0.append(result)
			PnLYearly.append(result["PnL"])
			
		PnLScenarios.update({key:PnLYearly})
		results.update({key:ScenarioResult})
	
	PnLScenarios.update({"Year": range(1, predictiontimeline +1 ) })
	df = pd.DataFrame.from_dict(PnLScenarios)
	df.set_index('Year', inplace=True)
	df.index.name = 'Year'
	
	st.header( "Key KPIs") 
	output = pd.DataFrame.from_dict(ScenarioResultY0)
	output.set_index('scenarioname', inplace=True)
	output.index.name = 'Scenario Name'
	output['FraudProbability'] = round(output['FraudProbability']*100,4)
	output['ClaimProbability'] = round(output['ClaimProbability']*100,4)
	output = output.apply(lambda x: x.astype(str), axis=1)
		
	oldcols = [ 'ClaimProbability', 'AverageClaimSize','TotalClaimAmount', 'GWP',  'Premium', 'Expenses', 'FraudProbability',  'ClaimReserve', 'PnL', 'LossRatio', 'CombinedRatio' ]
	newcols = [ 'Frequency', 'Avg Severity ($)', 'Total Claim Amount ($m)', 'GWP ($m)','Premium Per Policy ($)', 'Expenses ($m)', 'Fraud Probability (%)', 'Claim Reserve ($m)', 'PnL ($m)',
		  'Loss Ratio', 'Combined Ratio' ]
		
	output = output[oldcols]
	columnmap = dict(zip(oldcols, newcols))
	output = output.rename( columns = columnmap )
		
	st.write(output)
		
	st.header( "Projected PnL") 
		
	col1,col2 = st.columns(2)
		
	with col1:
		fig, axs = plt.subplots(figsize=(30, 20))
		axs.set_ylabel( "Profit ($mn)",fontdict={'fontsize':40})
		axs.set_xlabel( "Year",fontdict={'fontsize':40})
		axs.set_title( "Development of Overall Profit",pad=20, fontdict={'fontsize':40})
			
		df.plot.line(ax = axs,fontsize = 40, linewidth=5, marker='o', xticks = range(1, predictiontimeline + 1), markersize = 30 )				     
		plt.legend(loc='upper left',fontsize = 40)
		st.pyplot(fig)
			
	with col2:			
		st.write(df)

def PnLEstimateforScenario(Scenario):    
    MarketSize = Scenario["BaselineMarketSize"] * np.power((1+ Scenario["MarketGrowth"]), Scenario["TimeHorizon"])        
    NumPolicyHolders = MarketSize * Scenario["BaselineMarketShare"]
    NewPremium = Scenario['BaselinePremium'] * ( 1 + Scenario['PremiumChangePercentage']/100 )        
    DemandChange = Scenario['PremiumChangePercentage'] * Scenario['Gearing']
    NewNumPolicyHolders = ( 1- DemandChange/100) * NumPolicyHolders
    
    remainingpolicyholders = NewNumPolicyHolders 
    TotalPremium = 0
    
    ncdlist = Scenario['noclaimdiscounts'].split(',')
    for ncd in ncdlist:
        if ncd != 'None':
            ncd = ncd.replace('%', '')
            [noclaimpopulationpercentage, noclaimdiscount] = ncd.split('@')            
            ncd_policyholders = NewNumPolicyHolders * (float(noclaimpopulationpercentage)/100 )
            ncd_premium = NewPremium * ( 1 - float(noclaimdiscount)/100)
            TotalPremium = ncd_premium * ncd_policyholders
            remainingpolicyholders = remainingpolicyholders - ncd_policyholders
		
    TotalPremium = TotalPremium + NewPremium * remainingpolicyholders
    avgpremium = TotalPremium/NewNumPolicyHolders

    NumClaims = round(NewNumPolicyHolders * Scenario["ClaimProbability"])
    NumClaims = round(NumClaims * ( 1 + Scenario["FraudProbability"]))
    largelossclaim = NumClaims * (Scenario['largeloss']/100 ) * Scenario['largelossseverity']
    usualclaim = NumClaims * ( 1- Scenario['largeloss']/100) * Scenario['AvgClaimSize']
    TotalClaimAmount = usualclaim + largelossclaim
    AverageClaimSize = TotalClaimAmount/NumClaims
	
    LossRatio = TotalClaimAmount/TotalPremium
    Expenses = Scenario["OperatingExpenses"] * TotalPremium
    CombinedRatio = (TotalClaimAmount + Expenses)/TotalPremium

    CLOutput = getChainLadderOutput(lossreservingmodel, lossreservingdevelopment)
    CL = CLOutput['LDF'].iloc[0].values
    CumulativeClaimRatios = [1]
    for i in range(1, len(CL)):
        CumulativeClaimRatios.append(CumulativeClaimRatios[i-1]*CL[i])
	
    ClaimInitial = round(TotalClaimAmount/CumulativeClaimRatios[-1],0)
    ClaimReserve = round(TotalClaimAmount - ClaimInitial, 0)    
    
    InvestmentAmount = np.maximum(TotalPremium - TotalClaimAmount - Expenses, 0)    
    InvestmentIncome = InvestmentAmount * np.exp(Scenario["ReturnRate"]) - InvestmentAmount
    PnL = TotalPremium + InvestmentIncome - ClaimInitial - Expenses    
	 
    output = { "MarketSize" : MarketSize, "NumPolicyHolders" : NewNumPolicyHolders, "Premium":avgpremium, "GWP": round(TotalPremium/1e6,2), "NumClaims": NumClaims, 
	     "TotalClaimAmount":round(TotalClaimAmount/1e6,2),"ClaimInitial": round(ClaimInitial/1e6,2), "ClaimReserve": round(ClaimReserve/1e6,2), "Expenses": round(Expenses/1e6,2),
	     "InvestmentAmount": round(InvestmentAmount/1e6), "InvestmentIncome": round(InvestmentIncome/1e6,2),
	     "PnL": round(PnL/1e6,2), "LDF": CLOutput['LDF'], 	      
	      "LossRatio": round(LossRatio *100,2), "CombinedRatio": round(CombinedRatio *100,2), "AverageClaimSize": AverageClaimSize
	      }
    output.update(Scenario)
    return output

def getClaimProbability( RiskModel, riskprobadjustment):	
	
	api_url = "http://" + ip + "/modelMatrix?modelName=" + RiskModel
	
	response = requests.get(api_url)	
	response = response.json()
	
	matrix = response["confusion_matrix"]
	num = matrix[0][1] + matrix[1][1]
	den = matrix[0][0] + matrix[0][1] + matrix[1][0] + matrix[1][1]
	claimprobability = num/den
	claimprobability = claimprobability + riskprobadjustment
	return claimprobability

def getFraudProbability(FraudModel, fraudloss):
	if FraudModel == 'None':
		fraudprobability = 0
	else:		
		api_url = "http://" + ip + "/fraudModel"
	
		response = requests.get(api_url)	
		response = response.json()
	
		matrix = response["confusion_matrix"]
		num = matrix[0][1] + matrix[1][1]
		den = matrix[0][0] + matrix[0][1] + matrix[1][0] + matrix[1][1]
		fraudprobability = num/den
						
	fraudprobability = fraudprobability + fraudloss/100
	
	return fraudprobability
	
PnLScenarios = {}
results = {}
if submitted:

	claimprobability = getClaimProbability( riskmodel, riskprobadjustment )
	fraudprobability = getFraudProbability( fraudmodel, fraudloss )
			
	Scenario = { "RiskModel": riskmodel, "FraudModel": fraudmodel, "BaselinePremium": baselinepremium, 'AvgClaimSize': avgclaimsize, 
		    "BaselineMarketSize": baselinemarketsize, "BaselineMarketShare": baselinemarketshare/100, 
            "ReturnRate": investmentreturn/100,             
            "ClaimProbability": claimprobability, "FraudProbability": fraudprobability, 
            "MarketGrowth": marketgrowth/100, "OperatingExpenses": operatingexpenses/100,
	    "lossreservingmodel": lossreservingmodel, "lossreservingdevelopment": lossreservingdevelopment,
	    "PremiumChangePercentage":premiumchange, "Gearing": gearing, "largeloss": largeloss, "largelossseverity": largelossseverity,
	    "noclaimdiscounts": noclaimdiscounts, "scenarioname": scenarioname,	   
            }
	
	filename = "qs-streamlit/" + scenarioname + ".txt"
	json.dump(Scenario, fs.open( filename,'w'))

if basescenario:
	paramfilename = "qs-streamlit-params/params.txt"	
	with fs.open(paramfilename, 'rb') as f:
		data = json.load(f)
	claimprobability = getClaimProbability( data['riskmodel'], data['riskprobadjustment'] )
	fraudprobability = getFraudProbability( data['fraudmodel'], data['fraudloss'] )
	
	Scenario = { "RiskModel": riskmodel, "FraudModel": fraudmodel, "BaselinePremium": data['baselinepremium'], 'AvgClaimSize': data['avgclaimsize'], "BaselineMarketSize": data['baselinemarketsize'], 
		    "BaselineMarketShare": data['baselinemarketshare']/100, "ReturnRate": data['investmentreturn']/100,             
            		"ClaimProbability": claimprobability, "FraudProbability": fraudprobability,
            		"MarketGrowth": data['marketgrowth']/100, "OperatingExpenses": data['operatingexpenses']/100,
	    		"lossreservingmodel": data['lossreservingmodel'], "lossreservingdevelopment": data['lossreservingdevelopment'],
	    		"PremiumChangePercentage":data['premiumchange'], "Gearing": data['gearing'], "largeloss": data['largeloss'],
		    	"largelossseverity": data['largelossseverity'],
	    		"noclaimdiscounts": data['noclaimdiscounts'], "scenarioname": 'Baseline',	   
            		}
	
	filename = "qs-streamlit/Baseline.txt"
	json.dump(Scenario, fs.open( filename,'w'))
	
	performRun(['Baseline'])

def ShowParams(	scenariooptions ):
	Scenariolist =[]
	for key in scenariooptions:
		Scenariolist.append(readscenario(key))
			
	df1 = pd.DataFrame.from_dict(Scenariolist)
	
	df1['FraudProbability'] = round(df1['FraudProbability']*100,4)
	df1['ClaimProbability'] = round(df1['ClaimProbability']*100,4)
	
	oldcols = [ 'RiskModel', 'FraudModel', 'BaselinePremium', 'AvgClaimSize', 'BaselineMarketSize', 'BaselineMarketShare', 'ReturnRate', 
		    'ClaimProbability', 'FraudProbability', 'MarketGrowth', 'OperatingExpenses', 'lossreservingmodel', 'lossreservingdevelopment', 
		  'PremiumChangePercentage', 'Gearing', 'largeloss', 'largelossseverity', 'noclaimdiscounts', 'scenarioname']
	newcols = [ 'Risk Model', 'Fraud Model', 'Premium ($)', 'Average Severity ($)', 'Market Size', 'Market Share', 'Investment Return Rate (%)', 
			'Claim Probability (%)', 'Fraud Probability (%)', 'Market Growth (%)', 'Operating Expenses', 'Loss Reserving Model', 'Loss Reserving Development',
		  'Premium Change (%)', 'Gearing', 'Large Loss', 'Large Loss Severity ($)', 'No Claim Discount Mix', 'scenarioname' ]
		
	df1 = df1[oldcols]
	columnmap = dict(zip(oldcols, newcols))
	df1 = df1.rename( columns = columnmap )	
	
	df1.set_index('scenarioname', inplace=True)	
	df1 = df1.apply(lambda x: x.astype(str), axis=1)
	df1 = df1.T
	df1.reset_index(inplace = True )
	df1.rename( columns = {'index': 'Scenario Name'})
	st.header("Selected Parameters for Scenarios")		
	AgGrid(df1, height=550, fit_columns_on_grid_load=True)
	
if basescenarioparams:
	ShowParams(['Baseline'])	
	
if scenarioaction:
	if action == "Delete":
		for key in scenariooptions:
			file = 'qs-streamlit/' + key + '.txt'
			fs.delete(file)	

	if action == "Show Parameters":
		if 'Baseline' not in scenariooptions:
			scenariooptions.append('Baseline')
		
		ShowParams(scenariooptions)
		
	if action == "Run":
		if 'Baseline' not in scenariooptions:
			scenariooptions.append('Baseline')
		performRun(scenariooptions)		
