# -*- coding: utf-8 -*-
"""
Created on Thu Apr 22 08:41:28 2021

@author: 91998
"""


import streamlit as st
import pandas as pd

def displayText():
  return("sample text")
  
txt = displayText()
st.write( txt )
st.write( "Welcome to QS!" )

with st.sidebar.form(key='my_form'):
	premium = st.number_input("Enter Premium amount", min_value =0, max_value=10000)  
	elem = st.sidebar.selectbox("Choose scenario", {"ScenarioUp", "ScenarioDown"})
	submit_button = st.form_submit_button(label='Submit')

st.write("Premium is:", premium )
st.write("Selected scenario is:", elem )
#val1 = st.sidebar.slider("Pick a premium amount",min_value=0, max_value=10000, value=1000 )
#st.write("Selected Premium amount is:", val1 )





