from __future__ import annotations
import os

import pandas as pd
import numpy as np
import arrow
import streamlit as st
import plotly
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pymongo import MongoClient
from const import FARMS, TZ

# define some common stylings
COLORS = px.colors.qualitative.Plotly
LIGHT_GREY = '#bebebe'

horizontal_legend = dict(
    orientation='h',
    yanchor='bottom',
    y=1.2,
    xanchor='right',
    x=1)
grid_colors = dict(gridcolor=LIGHT_GREY, zerolinecolor=LIGHT_GREY)
line_plot_layout = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    showlegend=True,
    hovermode='x unified',
    hoverlabel=dict(namelength = -1),
    legend=horizontal_legend,)

url_prefix = 'https://raw.githubusercontent.com/hengwang322/wind_web_app/master/resources/'
url_suffix = '.gif'


def plot_map():
    farms = pd.read_csv('https://services.aremi.data61.io/aemo/v6/csv/wind')
    farms.set_index('DUID', inplace=True)
    lastest_time = farms.dropna().iloc[:, 3][0]
    lastest_time = arrow.get(lastest_time).to(TZ).format('YYYY-MM-DD HH:mm')

    # Rectify negative values
    bad_index = farms[farms['Current Output (MW)'] < 0].index
    farms.loc[bad_index, 'Current Output (MW)'] = 0
    farms.fillna(0, inplace=True)
    farms['Power (MW)'] = farms['Current Output (MW)'].apply(
        lambda x: round(x, 1))
    farms['Station Name'] = farms['Station Name'].apply(
        lambda s: s.replace('Wind Farm', '').replace('Windfarm', ''))

    px.set_mapbox_access_token(os.environ.get('MAPBOX_TOKEN'))

    fig = px.scatter_mapbox(farms.loc[list(FARMS.keys()), :],
                            lat='Lat',
                            lon='Lon',
                            zoom=5,
                            text='Station Name',
                            size='Power (MW)',
                            color='Power (MW)',
                            color_continuous_scale=plotly.colors.sequential.haline,
                            center={'lat': -35.5, 'lon': 137.5},
                            )

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=10, t=10, b=10),
        coloraxis=dict(
            colorbar_x=0.01,
            colorbar_y=0.99,
            colorbar_yanchor='top',
            colorbar_len=0.3,
            colorbar_bgcolor='white'
        ),
    )
    return fig


def plot_forecast(df, farm):
    latest = df[df.actual.isna()].index[-1]+1
    fig = go.Figure()

    # Plot the dashed line first, hide their legends, then plot solid lines and
    # show legends. Legneds are grouped so they can be hide/unhide at same time
    fig.add_trace(go.Scatter(
        x=df[:latest+1].time,
        y=round(df[:latest+1].prediction, 2),
        name='Prediction (Forecast)',
        legendgroup='Forecast',
        showlegend=False,
        line={'dash': 'dash', 'color': COLORS[1]}
    ))
    fig.add_trace(go.Scatter(
        x=df.time,
        y=round(df['actual'], 2),
        name='Actual',
        legendgroup='Actual',
        line={'dash': 'solid', 'color': COLORS[0]}
    ))
    fig.add_trace(go.Scatter(
        x=df[latest:].time,
        y=round(df[latest:].prediction, 2),
        name='Prediction',
        legendgroup='Forecast',
        line={'dash': 'solid', 'color': COLORS[1]}
    ))

    fig.update_yaxes(ticksuffix=' MW', tickangle=45, **grid_colors)
    fig.update_xaxes(**grid_colors)
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        **line_plot_layout,
    )

    return fig


def format_title(s):
    return ' '.join([w.capitalize() for w in s.split('_')])


def plot_weather(df, farm):
    latest = df[df.actual.isna()].index[-1]+1
    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.1)

    # Plot the dashed line first, hide their legends, then plot solid lines and
    # show legends. Legneds are grouped so they can be hide/unhide at same time
    fig.add_trace(go.Scatter(
        x=df[:latest+1].time,
        y=df[:latest+1]['wind_speed'],
        name='Wind (Forecast)',
        legendgroup='Wind',
        showlegend=False,
        line={'dash': 'dash', 'color': COLORS[2]}
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=df[:latest+1].time,
        y=df[:latest+1]['wind_gust'],
        name='Gust (Forecast)',
        legendgroup='Gust',
        showlegend=False,
        line={'dash': 'dash', 'color': COLORS[3]}
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=df[:latest+1].time,
        y=df[:latest+1]['temperature'],
        name='Temp (Forecast)',
        legendgroup='Temp',
        showlegend=False,
        line={'dash': 'dash', 'color': COLORS[4]}
    ), row=1, col=2)
    fig.add_trace(go.Scatter(
        x=df[latest:].time,
        y=df[latest:]['wind_speed'],
        name='Wind',
        legendgroup='Wind',
        line={'dash': 'solid', 'color': COLORS[2]}
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=df[latest:].time,
        y=df[latest:]['wind_gust'],
        name='Gust',
        legendgroup='Gust',
        line={'dash': 'solid', 'color': COLORS[3]}
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=df[latest:].time,
        y=df[latest:]['temperature'],
        name='Temp',
        legendgroup='Temp',
        line={'dash': 'solid', 'color': COLORS[4]}
    ), row=1, col=2)

    fig.update_yaxes(row=1, col=1, ticksuffix=' m/s',
                     tickangle=45, **grid_colors)
    fig.update_yaxes(row=1, col=2, ticksuffix=' °C',
                     tickangle=45, **grid_colors)
    fig.update_xaxes(**grid_colors)

    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        **line_plot_layout,
    )
    return fig
