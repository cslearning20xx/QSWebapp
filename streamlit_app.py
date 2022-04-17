import streamlit as st
import pandas as pd
 
st.write( "Welcome to QS!" )

with st.sidebar.form(key='my_form'):
    premium = st.number_input("Enter Premium amount", min_value=0, max_value=10000, value=1000)
    avgclaimsize = st.number_input("Enter Average Claim Amount", min_value=0, max_value=50000, value=21000)
    marketsize = st.number_input("Enter Market Size of policyholders", value=1000000)
    marketshare = st.slider('market share', min_value = 0.0, max_value = 100.0, value = 10.0, step = 0.01 ) 	
    submit_button = st.form_submit_button(label='Submit')

st.write("Premium is:", premium )
#elem = st.selectbox("Choose scenario", {"ScenarioUp", "ScenarioDown"})
#st.selectbox('Select flavor', ['Vanilla', 'Chocolate'], key=1)

col1, col2 = st.sidebar.columns(2)

with col1:
    with st.form('Form1'):
        premiumchange1 = st.slider('change in premium', min_value = 0.0, max_value = 10.0, value = -1.0, step = 0.01 )
        investmentreturn1 = st.slider('investment return', min_value = -20.0, max_value = 20.0, value = 5.0, step = 0.01 )
        submitted1 = st.form_submit_button('Submit Scenario1')

with col2:
    with st.form('Form2'):
        premiumchange2 = st.slider('change in premium', min_value = 0.0, max_value = 10.0, value = 1.0, step = 0.01 )
        investmentreturn2 = st.slider('investment return', min_value = -20.0, max_value = 20.0, value = 2.0, step = 0.01 )
        submitted2 = st.form_submit_button("Submit Scenario2")


if submitted1:
	st.write("you filled scenario 1")
if submitted2:
	st.write("you filled scenario 2")
