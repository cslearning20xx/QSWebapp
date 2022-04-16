# -*- coding: utf-8 -*-
"""
Created on Thu Apr 22 08:41:28 2021

@author: 91998
"""


import streamlit as st
import pandas as pd

st.write( "Welcome to QS!" )

val = st.number_input("Enter Premium amount", min_value =0, max_value=10000)
st.write("Premium amount is:", val )

val1 = st.slider("Pick a premium amount",min_value=0, max_value=10000, value=1000 )
st.write("Premium amount is:", val1 )

elem = st.selectbox("Choose scenario", {"ScenarioUp", "ScenarioDown"})
st.write("Selected scenario is:", elem )



