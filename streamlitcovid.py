import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_lottie import st_lottie
import requests

#page layout
st.set_page_config(layout= "wide",page_title="Covid U.S Map",page_icon="bar_chart")


#Reading in the us confirmed cases and county population
usconfirmed="https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv"
usdf = pd.read_csv(usconfirmed)
pop_url = 'https://usafactsstatic.blob.core.windows.net/public/data/covid-19/covid_county_population_usafacts.csv'
pop = pd.read_csv(pop_url)

#Removing nulls
print(usdf[usdf['FIPS'].isnull()])
usdf['FIPS'] = pd.to_numeric(usdf['FIPS'], errors='coerce')
usdf = usdf.dropna(subset=['FIPS'])

#Removing population data that has no value
pop=pop[pop.countyFIPS!=0]
pop=pop[pop.population!=0]
pop["FIPS"]=pop["countyFIPS"].astype(float)
newpop=pop[["FIPS","population"]]

#merging both data sets on the FIPS value.
df=pd.merge(usdf,newpop,on="FIPS",how='outer')
#Removing some additional rows it added
df=df[df["6/26/22"]!=0]

# Some states only had four digits for fips code which plotly couldnt graph.Using zfill to make sure its five digits fixed the problem.
df['FIPS'] = df['FIPS'].astype(int).astype(str).str.zfill(5)

#Moving population
move_pop=df.pop("population")
df.insert(11,"population",move_pop)
#Last month cases
df["Last_Month_Cases"]=df.iloc[:,-33:-32]
move=df.pop("Last_Month_Cases")
df.insert(12,"Last_Month_Cases",move)
#Total current cases
df["Total_Cases"]=df.iloc[:,-1:]
move_total=df.pop("Total_Cases")
df.insert(13,"Total_Cases",move_total)
#Percent differnce from last month
df["Percent_Change_from_Last_Month"]=round((df["Total_Cases"]-df["Last_Month_Cases"])/df["Last_Month_Cases"]*100,1)
move_percent=df.pop("Percent_Change_from_Last_Month")
df.insert(14,"Percent_Change_from_Last_Month",move_percent)
#Cases Per 100,000
df["Cases_Per_100k"]=np.ceil((df["Total_Cases"]/df["population"])*100000)
move_cases_100k=df.pop("Cases_Per_100k")
df.insert(15,"Cases_Per_100k",move_cases_100k)
df.Cases_Per_100k.fillna(0,inplace=True)
df.Cases_Per_100k=df.Cases_Per_100k.astype(int)

#Latest date
todays_date=df.columns[-1]
#Top columns
col1, col2 = st.columns((2,2))
with col1:
    st.title("COVID 19 Dashboard: Last updated on "+todays_date+"")

#Lottie animation
def load_lottie(url):
    r =requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()
lottie_animation=load_lottie("https://assets6.lottiefiles.com/packages/lf20_AQ3M8U.json")
with col2:
    st_lottie(lottie_animation,height=100,width=100)
###################################################
from urllib.request import urlopen
import json
with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)
#cases per 100k
token="pk.eyJ1Ijoia3l1bmxlZSIsImEiOiJjbDUwZHdyZTgwazBiM2l1czQ5MzdxMjdnIn0.1pSPPt_cXnK0tx6iibiq5A"
fig = px.choropleth_mapbox(df,geojson=counties,locations="FIPS",color="Cases_Per_100k",
                           color_continuous_scale=px.colors.diverging.Portland,
                           range_color=(0,50000),
                           zoom=3, center = {"lat": 37.0902, "lon": -95.7129},
                           opacity=0.9,
                           hover_data=["Combined_Key","population"],



                          )
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0},mapbox_accesstoken=token,mapbox_style ="mapbox://styles/kyunlee/cl50exg82002s15qv9695dek1"
                 )


#Total cases

fig1 = px.choropleth_mapbox(df,geojson=counties,locations="FIPS",color="Total_Cases",
                           color_continuous_scale=px.colors.diverging.Portland,
                           range_color=(0, 100000),
                           zoom=3, center = {"lat": 37.0902, "lon": -95.7129},
                           opacity=0.9,
                           hover_data=["Combined_Key"],
                           color_continuous_midpoint=(100000)


                          )
fig1.update_layout(margin={"r":0,"t":0,"l":0,"b":0},mapbox_accesstoken=token,mapbox_style ="mapbox://styles/kyunlee/cl50exg82002s15qv9695dek1"
                 )

#Percentage increase from last month

fig2 = px.choropleth_mapbox(df,geojson=counties,locations="FIPS",color="Percent_Change_from_Last_Month",
                           color_continuous_scale=px.colors.diverging.Portland,
                           range_color=(0,10),
                           zoom=3, center = {"lat": 37.0902, "lon": -95.7129},
                           opacity=0.9,
                           hover_data=["Combined_Key"],

                           labels={"Percent_Change_from_Last_Month":"Percent"}

                      )
fig2.update_layout(margin={"r":0,"t":0,"l":0,"b":0},mapbox_accesstoken=token,mapbox_style ="mapbox://styles/kyunlee/cl50exg82002s15qv9695dek1"
          )
# #Making it to long format (so I can make a timeseries)
@st.experimental_memo
def long_format(df):
    dfl=df
    dfl.drop(["UID","iso2","iso3","code3","Admin2","Province_State","Country_Region","Lat","Long_","population","Last_Month_Cases",
         "Total_Cases","Percent_Change_from_Last_Month","Cases_Per_100k"], axis=1, inplace=True)
    df_long=dfl.melt(id_vars=["FIPS","Combined_Key"],var_name="date",value_name="confirmed")
    df_long_first_day_each_month=df_long.loc[df_long['date'].str[2:4] == "1/"]
    return df_long_first_day_each_month

df_long_first_day=long_format(df)
#time series
@st.experimental_memo
def figure3():
    fig3 = px.choropleth_mapbox(df_long_first_day,geojson=counties,locations="FIPS",color=df_long_first_day["confirmed"],
                           color_continuous_scale=px.colors.diverging.Portland,
                           zoom=2.5, center = {"lat": 37.0902, "lon": -95.7129},
                           opacity=0.9,
                           hover_data=["Combined_Key"],
                           range_color=(0, 100000),
                           labels={"log10":"log10"},
                           animation_frame ="date"
                          )
    fig3.update_layout(margin={"r":0,"t":0,"l":0,"b":0},mapbox_accesstoken=token,mapbox_style ="mapbox://styles/kyunlee/cl50exg82002s15qv9695dek1"
          )
    fig3.update_layout(transition_duration=100000)
    return fig3
#line charts
@st.experimental_memo
def pxline():
    line = px.line(df_long_first_day,x="date",y=df_long_first_day["confirmed"],color="Combined_Key")
    return line

time_frame = st.selectbox("View by: ", ("CASES PER 100,000 PEOPLE", "TOTAL COVID CASES","PERCENTAGE INCREASE OVER A MONTH","TIME SERIES OF CASES","LINE CHART OF CASES BY COUNTY"),0)

if time_frame=="CASES PER 100,000 PEOPLE":
    st.text("Total confirmed cases per 100,000 inhabitant.")
    st.plotly_chart(fig,use_container_width=True)
elif time_frame=="TOTAL COVID CASES":
    st.text("Total confirmed cases up to " + todays_date +"")
    st.plotly_chart(fig1,use_container_width=True)
elif time_frame=="PERCENTAGE INCREASE OVER A MONTH":
    st.text("Percentage increase over a period of a month")
    st.plotly_chart(fig2,use_container_width=True)
elif time_frame=="TIME SERIES OF CASES":
    st.text("Time series of covid cases since the start of the pandemic.")
    st.plotly_chart(figure3(),use_container_width=True)
else:
    st.text("As you can see, there is seasonality within the data. Cases surge during the month of September untill March. \n This follow the same trend as Flu season which strikes the U.S. from the late fall to the spring, peaking from December to February")
    st.plotly_chart(pxline(),use_container_width=True)
