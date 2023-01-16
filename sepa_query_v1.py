# -*- coding: utf-8 -*-
"""
Created on Sun Jan 15 22:23:31 2023

@author: lcawh
"""

import streamlit as st
import requests
import pandas as pd
import datetime as dt
import altair as alt

#dictionaries
dict_p = {'SG':'stage','Q':'flow','RE':'rainfall'}

dict_ts = {'15m.Cmd':'15 minute','15m.Total':'15 minute total',
           'HYear.Max':'Annual maximum','HYear.Mean':'Annual mean',
           'HDay.Total':'Daily total'}

s_dict = {'15 minute total rainfall':['RE','15m.Total'],
          'Daily total rainfall':['RE','HDay.Total'],
          '15 minute flow':['Q','15m.Cmd'],
          '15 minute stage':['SG','15m.Cmd'],
          'Annual maximum stage':['SG','HYear.Max'],
          'Annual maximum flow':['Q','HYear.Max'],
          'Annual mean stage':['SG','HYear.Mean'],
          'Annual mean flow':['Q','HYear.Mean']}

ts = ('15m.Cmd','15m.Total','HYear.Max','HYear.Mean','HDay.Total') 

#functions
def get_station_no(name):
    r = requests.get('https://timeseries.sepa.org.uk/KiWIS/KiWIS?service='
                     +'kisters&type=queryServices&datasource=0&request=getstationlist&'+
                     f'station_name={name}&returnfields=station_no,ca_sta')
    df = pd.read_html(r.text)
    df = df[0]
    df = df.iloc[1,0]
    return df  

def get_ts_names(name):
    #returns list in plain English of ts available
    r = requests.get('https://timeseries.sepa.org.uk/KiWIS/KiWIS?service='
                     +'kisters&type=queryServices&datasource=0&request=getTimeSeriesList&'+
                     f'station_name={name}&returnfields=site_no,station_no,stationparameter_no,'+
                     'ts_shortname,coverage&dateformat=yyyy-MM-dd HH:mm:ss')
    df = pd.read_html(r.text)
    df = df[0]
    df = df[df[3].isin(ts)]
    options=[]
    for i,j in zip(df[2],df[3]):
        p1 = dict_p[i]
        t1 = dict_ts[j]
        k = f'{t1} {p1}'
        options.append(k)
    
    return options

def get_ts(name,timeseries,startdate,enddate):
    sn = get_station_no(name)
    pa = s_dict[f'{timeseries}']
    r = requests.get('https://timeseries.sepa.org.uk/KiWIS/KiWIS?service='
                     +'kisters&type=queryServices&datasource=0&request=getTimeseriesValues&'+
                     f'ts_path=1/{sn}/{pa[0]}/{pa[1]}&from={startdate}&to={enddate}&'+
                     'returnfields=Timestamp,Value,Quality Code&format=dajson')
    
    #pull data out of its weird json dictionary or w/e
    s = r.json()[0]
    
    df = pd.DataFrame(s['data'],columns=('date',f'{timeseries}','quality code'))
    df['date'] = df['date'].astype('datetime64[ns]')
    
    return df

def df_to_csv(df):
    return df.to_csv().encode('utf-8')

#The streamlit bit
st.title('Download and plot SEPA API data')
st.markdown("This is a very experimental app to allow users without a coding background to plot and download data from the [SEPA API](https://timeseriesdoc.sepa.org.uk/). Currently only a limited number of timeseries are supported. What it does (sometimes): identifies available timeseries at a (correctly-spelled) SEPA station, plots and/or downloads it in CSV format. What it does not do (yet): tell you why when it doesn't. Do let me know if you break it in an interesting way.")
st.markdown('PS the SEPA API puts a daily limit on the amount of data that unregistered users can request so consider your choices before downloading 15 minute flow data from 1961-2022 for fifty stations. ')

#session state stuff
if 'stage' not in st.session_state:
    st.session_state.stage = 0

def set_stage(stage):
    st.session_state.stage = stage

name = st.text_input("Station name", "Sheriffmills")

st.button('Search for available data',on_click=set_stage,args=(1,))

if st.session_state.stage >0:

    options = get_ts_names(name)
    
    timeseries = st.selectbox("Available timeseries",options)
    startdate = st.date_input('Enter start date',dt.date(2023,1,1))
    enddate = st.date_input('Enter end date',dt.date(2023,1,2))
    sample = get_ts(name,timeseries,startdate,enddate) 
    
    csv = df_to_csv(sample)
    st.download_button(label='Download data as csv',
                       data=csv,
                       file_name='sepa_query.csv')
    if st.button('Plot data'):
        pa = s_dict[f'{timeseries}']
        st.line_chart(sample,x='date',y=f'{timeseries}')
		c = alt.Chart(sample).mark_line().encode(x='date',y=f'{timeseries}')
        st.altair_chart(c, use_container_width=True)