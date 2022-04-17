# -*- coding: utf-8 -*-
"""
Created on Thu Apr 22 08:41:28 2021

@author: 91998
"""


import streamlit as st
import pandas as pd
 
txt = displayText()
st.write( txt )
st.write( "Welcome to QS!" )

with st.sidebar.form(key='my_form'):
	premium = st.number_input("Enter Premium amount", min_value=0, max_value=10000, value=1000) 	
	submit_button = st.form_submit_button(label='Submit')
	
st.write("Premium is:", premium )
#st.write("Selected scenario is:", elem )
#val1 = st.sidebar.slider("Pick a premium amount",min_value=0, max_value=10000, value=1000 )
#st.write("Selected Premium amount is:", val1 )
#elem = st.selectbox("Choose scenario", {"ScenarioUp", "ScenarioDown"})
#st.selectbox('Select flavor', ['Vanilla', 'Chocolate'], key=1)

col1, col2 = st.sidebar.columns(2)

# -*- coding: utf-8 -*-
"""
Created on Thu Apr 22 08:41:28 2021

@author: 91998
"""


import streamlit as st
import pandas as pd
 
txt = displayText()
st.write( txt )
st.write( "Welcome to QS!" )

with st.sidebar.form(key='my_form'):
	premium = st.number_input("Enter Premium amount", min_value=0, max_value=10000, value=1000) 	
	submit_button = st.form_submit_button(label='Submit')
	
st.write("Premium is:", premium )
#st.write("Selected scenario is:", elem )
#val1 = st.sidebar.slider("Pick a premium amount",min_value=0, max_value=10000, value=1000 )
#st.write("Selected Premium amount is:", val1 )
#elem = st.selectbox("Choose scenario", {"ScenarioUp", "ScenarioDown"})
#st.selectbox('Select flavor', ['Vanilla', 'Chocolate'], key=1)

col1, col2 = st.sidebar.columns(2)

with col1:
	with st.form('Form1'):
        	premiumchange1 = st.slider('change in premium', min_value = 0.0, max_value = 10.0, value = 1.0, step = 0.01 )
        	investmentreturn1 = st.slider('investment return', min_value = -20.0, max_value = 20.0, value = 3.0, step = 0.01 )	
		submitted1 = st.form_submit_button("Submit Scenario 1")
	
with col2:
	with st.form('Form2'):
        	premiumchange2 = st.slider('change in premium', min_value = 0.0, max_value = 10.0, value = 1.0, step = 0.01 )
        	investmentreturn2 = st.slider('investment return', min_value = -20.0, max_value = 20.0, value = 3.0, step = 0.01 )
		marketgrowth2 = st.slider('market growth', min_value = -20.0, max_value = 50.0, value = 5.0, step = 0.01 )
        	submitted2 = st.form_submit_button('Submit Scenario 2')

if submitted1:
	print("you filled scenario 1")
if submitted2:
	print("you filled scenario 2")
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 22 08:41:28 2021

@author: 91998
"""


import streamlit as st
import pandas as pd
 
txt = displayText()
st.write( txt )
st.write( "Welcome to QS!" )

with st.sidebar.form(key='my_form'):
	premium = st.number_input("Enter Premium amount", min_value=0, max_value=10000, value=1000) 	
	submit_button = st.form_submit_button(label='Submit')
	
st.write("Premium is:", premium )
#st.write("Selected scenario is:", elem )
#val1 = st.sidebar.slider("Pick a premium amount",min_value=0, max_value=10000, value=1000 )
#st.write("Selected Premium amount is:", val1 )
#elem = st.selectbox("Choose scenario", {"ScenarioUp", "ScenarioDown"})
#st.selectbox('Select flavor', ['Vanilla', 'Chocolate'], key=1)

col1, col2 = st.sidebar.columns(2)

with col1:
	with st.form('Form1'):
        	premiumchange1 = st.slider('change in premium', min_value = 0.0, max_value = 10.0, value = 1.0, step = 0.01 )
        	investmentreturn1 = st.slider('investment return', min_value = -20.0, max_value = 20.0, value = 3.0, step = 0.01 )
		submitted1 = st.form_submit_button("Submit Scenario 1")
	
with col2:
	with st.form('Form2'):
        	premiumchange2 = st.slider('change in premium', min_value = 0.0, max_value = 10.0, value = 1.0, step = 0.01 )
        	investmentreturn2 = st.slider('investment return', min_value = -20.0, max_value = 20.0, value = 3.0, step = 0.01 )
		marketgrowth2 = st.slider('market growth', min_value = -20.0, max_value = 50.0, value = 5.0, step = 0.01 )
        	submitted2 = st.form_submit_button('Submit Scenario 2')

if submitted1:
	print("you filled scenario 1")
if submitted2:
	print("you filled scenario 2")
	
with col2:
	with st.form('Form2'):
        	premiumchange2 = st.slider('change in premium', min_value = 0.0, max_value = 10.0, value = 1.0, step = 0.01 )
        	investmentreturn2 = st.slider('investment return', min_value = -20.0, max_value = 20.0, value = 3.0, step = 0.01 )
		marketgrowth2 = st.slider('market growth', min_value = -20.0, max_value = 50.0, value = 5.0, step = 0.01 )
        	submitted2 = st.form_submit_button('Submit Scenario 2')

if submitted1:
	print("you filled scenario 1")
if submitted2:
	print("you filled scenario 2")
