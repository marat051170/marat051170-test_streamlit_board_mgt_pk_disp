import plotly.express as px
import streamlit as st
import pandas as pd
from math import log, floor
import altair as alt



@st.cache
def get_data_vipuskall():
    df = pd.read_excel('test_vipuskall.xlsx', dtype={'time_value': int, 'no_free_routes': int})
    df = df[(df['time_value'] == 9999) & (df['no_free_routes'] == 0)]
    return df


def human_format(number):
    units = ['', 'K', 'M', 'G', 'T', 'P']
    k = 1000.0
    magnitude = int(floor(log(number, k))) if number != 0 else 0
    return '%.1f%s' % (number / k**magnitude, units[magnitude])


def release_fact_on_plan(df):
    df = df.groupby('week_name').sum().reset_index()
    df = pd.melt(df, id_vars=['week_name'], var_name='plan_fact')
    return df


def calc_fact_on_plan(df):
    try:
        return df.query('plan_fact == "fact"')['value'].iloc[0] / df.query('plan_fact == "plan"')['value'].iloc[0]
    except IndexError:
        return 0


def two_empty_rows():
    for i in range(1, 3):
        st.markdown('#')


def weekly_delta(df):
    df['week_number'] = df['week_name'].apply(lambda x: int(x.split('_')[0]))
    current_week = df[df['end_week'] == max(df['end_week'])]['week_number'].unique()[0]
    previous_week = (current_week - 1) if current_week != 1 else 52
    df_current_week = df[df['week_number'] == current_week].groupby('week_name').sum()
    current_week_fact_to_plan = df_current_week.assign(fact_to_plan=df_current_week['fact'] / df_current_week['plan'])['fact_to_plan'].max()
    df_previous_week = df[df['week_number'] == previous_week].groupby('week_name').sum()
    previous_week_fact_to_plan = df_previous_week.assign(fact_to_plan=df_previous_week['fact'] / df_previous_week['plan'])['fact_to_plan'].max()

    print(current_week_fact_to_plan, previous_week_fact_to_plan)

    if previous_week_fact_to_plan == previous_week_fact_to_plan:
        return "{:10.1f} pp".format((current_week_fact_to_plan - previous_week_fact_to_plan) * 100)
    else:
        return 0



st.set_page_config(page_title='ПК Диспетчерская', page_icon=':bar_chart:', layout='wide')
st.title('3: Эффективность использования парка')

st.markdown('***ВНИМАНИЕ! Дорабатывается и дополняется для валидации, целевой дэшборд будет иметь другой вид !***')
st.sidebar.header('Фильтры')


# Filters -------------------------------------------------------------------------
cols_for_filters = ['month', 'dsc', 'week_name']
filter_values = get_data_vipuskall()[cols_for_filters].drop_duplicates()

depots = st.sidebar.multiselect(
    'Парк:', options=sorted(filter_values['dsc'].unique()), default=filter_values['dsc'].unique())
filter_values_depot = filter_values.query('dsc == @depots')

months = st.sidebar.multiselect(
    'Месяц:', options=sorted(filter_values_depot['month'].unique(), reverse=True), default=max(filter_values_depot['month'].unique()))
filter_values_depot_month = filter_values_depot.query('month == @months')

weeks = st.sidebar.multiselect(
    'Неделя:', options=sorted(filter_values_depot_month['week_name'].unique(), reverse=True), default=filter_values_depot_month['week_name'].unique())
filter_values_depot_month_week = filter_values_depot_month.query('week_name == @weeks')


# Факт и план ---------

df_bus = get_data_vipuskall().query(
    'вид_парка == "Автобусный" & dsc == @depots & month == @months & week_name == @weeks')[['end_week', 'week_name', 'plan', 'fact']]
df_elbus = get_data_vipuskall().query(
    'вид_парка == "Электробусный" & dsc == @depots & month == @months & week_name == @weeks')[['end_week', 'week_name', 'plan', 'fact']]

col1, col2 = st.columns(2)
with col1:
    st.header('Автобусный парк')
with col2:
    st.header('Электробусный парк')

two_empty_rows()

col1, col2, col3, col4 = st.columns([3, 1, 3, 1], gap='small')

# --- автобусный --- bars
with col1:
    bus_data = release_fact_on_plan(df_bus).groupby('plan_fact').sum().query("plan_fact == 'plan' | plan_fact == 'fact'").copy().reset_index()
    bars = alt.Chart(bus_data).mark_bar().encode(x='value:Q', y="plan_fact:O")
    text = bars.mark_text(align='left', dx=3).encode(text='value:Q')
    st.altair_chart((bars + text), theme="streamlit")

# --- автобусный --- metrics
with col2:
    st.metric(label='', value="{0:.1f}%".format((calc_fact_on_plan(bus_data) - 1) * 100))

# --- электробусный --- bars
with col3:
    elbus_data = release_fact_on_plan(df_elbus).groupby('plan_fact').sum().query("plan_fact == 'plan' | plan_fact == 'fact'").copy().reset_index()
    bars = alt.Chart(elbus_data).mark_bar().encode(x='value:Q', y="plan_fact:O")
    text = bars.mark_text(align='left', dx=3).encode(text='value:Q')
    st.altair_chart((bars + text), theme="streamlit")

# --- электробусный --- metrics
with col4:
    st.metric(label='', value="{0:.1f}%".format((calc_fact_on_plan(elbus_data) - 1) * 100))


# выполнение плана ----

two_empty_rows()

col1, col2 = st.columns(2)

with col1:
    st.metric(
        label="Выполнение плана выпуска", value="{0:.1f}%".format(calc_fact_on_plan(bus_data) * 100), delta=weekly_delta(df_bus))

with col2:
    st.metric(
        label="Выполнение плана выпуска", value="{0:.1f}%".format(calc_fact_on_plan(elbus_data) * 100), delta=weekly_delta(df_elbus))

