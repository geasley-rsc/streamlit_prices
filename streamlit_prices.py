import streamlit as st
import requests
import pandas as pd
import numpy as np
import altair as alt

import datetime
import holidays

def find_last_trading_day(input_date):
    # Define today's date
    #today = datetime.datetime.today()

    nyse_holidays = holidays.NYSE()

    # Function to check if a given date is a weekend (Saturday or Sunday)
    def is_weekend(date:datetime.datetime):
        return date.weekday() >= 5  # 5 represents Saturday, 6 represents Sunday
    
    def is_holiday(date:datetime.datetime):
        return date in nyse_holidays

    # Find the last trading day before today (excluding weekends)
    last_trading_day = input_date - datetime.timedelta(days=1)
    while is_weekend(last_trading_day) or is_holiday(last_trading_day):
        last_trading_day -= datetime.timedelta(days=1)

    return last_trading_day


def pull_settlements(pull_date:datetime.datetime=None):

    if pull_date is None:
        pull_date = find_last_trading_day(datetime.datetime.now())

    out_date =  pull_date.strftime('%Y-%m-%d')
    pull_date = pull_date.strftime('%m/%d/%Y')

    # WTI
    # https://www.cmegroup.com/CmeWS/mvc/Settlements/Futures/Settlements/425/FUT?strategy=DEFAULT&tradeDate=10/02/2023&pageSize=500&isProtected&_t=1696434720201

    # Henry Hub
    #https://www.cmegroup.com/CmeWS/mvc/Settlements/Futures/Settlements/444/FUT?strategy=DEFAULT&tradeDate=10/03/2023&pageSize=500&isProtected&_t=1696434665324

    # Brent
    #https://www.cmegroup.com/CmeWS/mvc/Settlements/Futures/Settlements/424/FUT?strategy=DEFAULT&tradeDate=10/03/2023&pageSize=500&isProtected&_t=1696434522187


    url = f'https://www.cmegroup.com/CmeWS/mvc/Settlements/Futures/Settlements/425/FUT?strategy=DEFAULT&tradeDate={pull_date}&pageSize=500&isProtected&_t=1696434720201'
    l_wti = requests.get(url).json()
     
    l_wti = pd.DataFrame(l_wti)
    l_wti = pd.DataFrame(l_wti['settlements'].to_list())
    l_wti = l_wti.drop(l_wti.index[-1])
    

    l_wti = l_wti[['month','settle']]
    l_wti['month'] = l_wti['month'].str.replace('JLY','JUL')

    l_wti['month'] = pd.to_datetime(l_wti['month'], format='%b %y')
    l_wti['settle'] = pd.to_numeric(l_wti['settle'])


    l_hh = requests.get(f'https://www.cmegroup.com/CmeWS/mvc/Settlements/Futures/Settlements/444/FUT?strategy=DEFAULT&tradeDate={pull_date}&pageSize=500&isProtected&_t=1696434665324').json()
     
    l_hh = pd.DataFrame(l_hh)
    l_hh = pd.DataFrame(l_hh['settlements'].to_list())

    l_hh = l_hh.drop(l_hh.index[-1])
    l_hh = l_hh[['month','settle']]
    l_hh['month'] = l_hh['month'].str.replace('JLY','JUL')

    l_hh['month'] = pd.to_datetime(l_hh['month'], format='%b %y')
    l_hh['settle'] = pd.to_numeric(l_hh['settle'])


    l_brent = requests.get(f'https://www.cmegroup.com/CmeWS/mvc/Settlements/Futures/Settlements/424/FUT?strategy=DEFAULT&tradeDate={pull_date}&pageSize=500&isProtected&_t=1696434522187').json()
     
    l_brent = pd.DataFrame(l_brent)
    l_brent = pd.DataFrame(l_brent['settlements'].to_list())

    l_brent = l_brent.drop(l_brent.index[-1])
    l_brent = l_brent[['month','settle']]
    l_brent['month'] = l_brent['month'].str.replace('JLY','JUL')

    l_brent['month'] = pd.to_datetime(l_brent['month'], format='%b %y')
    l_brent['settle'] = pd.to_numeric(l_brent['settle'])


    return l_wti, l_hh, l_brent, out_date

def make_graph(input_df):

    nearest = alt.selection_point(nearest=True, on='mouseover',
                        fields=['month'], empty=False)
    
    domain = ['Henry Hub', 'Brent', 'WTI']
    range_ = ['red', 'green', 'chartreuse']

    base = alt.Chart(input_df).encode(
        alt.Color('Product:N').scale(scheme='dark2'),
        alt.X('month:T', axis=alt.Axis(title='Settlement Month'))
    )


    oil_chart = base.transform_filter(
        alt.datum.Product != 'Henry Hub'
    ).mark_line().encode(
        y=alt.Y('settle:Q', axis=alt.Axis(title='Oil Price, $/BBL')),
    )

    gas_chart = base.transform_filter(
        alt.datum.Product == 'Henry Hub'
    ).mark_line().encode(
        y=alt.Y('settle:Q', axis=alt.Axis(title='Gas Price, $/MMSCF')),
    )

    selectors = base.mark_point().encode(
        opacity=alt.value(0),
        tooltip='month:T'
    ).add_params(
        nearest
    )
   

    # Draw text labels near the points, and highlight based on selection
    oil_text = oil_chart.mark_text(align='left', dx=5, dy=-5).encode(
        text=alt.condition(nearest, 'settle:Q', alt.value(' '))
    )

    gas_text = gas_chart.mark_text(align='left', dx=5, dy=-5).encode(
        text=alt.condition(nearest, 'settle:Q', alt.value(' '))
    )


    rules = base.mark_rule(color='gray').encode(
        x='month:T',
        #tooltip='month:T'
    ).transform_filter(
        nearest
    )

    # Combine the charts
    final_chart = alt.layer(
        (oil_chart+oil_text), (gas_chart+gas_text),selectors,rules,  #gas_text
    ).properties(
        width=600, height=300
    ).resolve_scale(
        y='independent'
    )


    

    return final_chart


if __name__ == '__main__':

    l_wti, l_hh, l_brent, out_date = pull_settlements()

    l_wti['Product'] = 'WTI'
    l_hh['Product'] = 'Henry Hub'
    l_brent['Product'] = 'Brent'

    combined_df = pd.concat([l_wti,l_hh,l_brent])

    altair_chart = make_graph(combined_df)

    st.altair_chart(altair_chart, use_container_width=False, theme="streamlit")

