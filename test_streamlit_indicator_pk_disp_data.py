import plotly.express as px
import streamlit as st



@st.cache
def get_data_vipuskall():
    df = read('test_vipuskall.xlsx')