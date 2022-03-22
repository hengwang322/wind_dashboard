import os
import logging

import pandas as pd
from pymongo import MongoClient
import arrow
from dash import Dash, html, dcc
from dash.dependencies import Output, Input, State
from dash.html import Div
import dash_bootstrap_components as dbc
from dash_bootstrap_components import Card, CardBody, CardHeader, Row, Col

from plot import plot_map, plot_forecast, plot_weather
from const import FARMS, TZ


logging.basicConfig(level=logging.INFO)
logging.getLogger('numexpr').setLevel(logging.WARNING)

app = Dash(__name__,
           meta_tags=[{'name': 'viewport',
                       'content': 'width=device-width'}],
           external_stylesheets=[dbc.themes.FLATLY]
           )

app.title = 'Wind Dashboard'
server = app.server


DB = MongoClient(os.environ.get('MONGO_URI'))['wpp']
DEFAULT_FARM = list(FARMS.keys())[0]
DEFAULT_DAY = 4 * 24
FARM_OPTIONS = [{'label': v, 'value': k} for k, v in FARMS.items()]
RANGE_OPTIONS = [{'label': k, 'value': v} for k, v in
                 {'Past 2 Days': ((2+2)*24), 'Past Week': ((2+7)*24), 'Past Month': ((2+30)*24),
                  'Past 3 Months': ((2+90)*24), 'Past 6 Months': ((2+180)*24),
                  'Past Year': ((2+365)*24), 'All time': 0}.items()
                 ]

forecast_card = Card([
    CardHeader(id='plot-title', style={'height': '50px'}),
    CardBody(
        dcc.Graph(
            id='forecast-plot',
            config={'displayModeBar': False},
            style={'height': '250px'}
        )
    )], style={'margin': 5, 'height': '320px'}, className='card border-success')

weather_card = Card(CardBody(
    [dcc.Graph(
        id='weather-plot',
        config={'displayModeBar': False},
        style={'height': '200px'}
    )]), style={'margin': 5, 'height': '250px'}, className='card border-primary')

weather_info = Card(
    CardBody(id='weather'),
    style={'margin': 5, 'height': '250px'},
    className='card border-primary')

map_card = Card(
    [
        CardHeader(html.H5('Wind Farms in South Australia'),
                   style={'height': '50px'}),
        CardBody(dcc.Graph(
            id='farms-map',
            figure=plot_map(),
            config={'displayModeBar': False},
            style={'height': '500px'}
        ))],
    style={'margin': 5, 'height': '580px'}, className='card border-info')

about_modal = dbc.Modal([
    dbc.ModalHeader('About this dashboard'),
    dbc.ModalBody([
        html.P("""
                This dashboard is a demo for medium-range wind power predictions 
                for major wind farms in South Australia, using machine learning models. 
                The models are built using XGBoost by discovering the 
                relationship between weather data and power data. 
                This web app is built with Dash.
                """),
        html.P([
            'Weather data is provided by ',
            html.A(
                'Dark Sky API', href='https://darksky.net/poweredby/', target='_blank'),
            '. Power data is provided by ',
            html.A("""The Australian Renewable Energy Mapping 
                            Infrastructure Project (AREMI)""",
                   href='https://nationalmap.gov.au/renewables/', target='_blank'),
            '.'
        ]),
        html.P([
            'Please feel free to check out my other projects on my ',
            html.A(
                'Github', href='https://github.com/hengwang322', target='_blank'),
            ', or contact me on my ',
            html.A(
                'LinkedIn', href='https://www.linkedin.com/in/hengwang322/', target='_blank'),
            '.'
        ])]
    ),
    dbc.ModalFooter(
        dbc.Button('Close', id='close', className='ml-auto')
    ),
], id='modal')

navbar = dbc.NavbarSimple(
    Row([
        Col(dbc.Select(
            id='farm-select',
            options=FARM_OPTIONS,
            value=DEFAULT_FARM,
            style={'width': 200, 'margin': 5}), align='start'
            ),
        Col(dbc.Select(
            id='day-select',
            options=RANGE_OPTIONS,
            value=DEFAULT_DAY,
            style={'width': 120, 'margin': 5}), align='start'
            ),
        Col(
            Div([
                dbc.Button('About', id='open', style={'margin': 5}),
                about_modal
            ]), align='start')
    ], justify='center'),
    brand='Welcome to Wind Power Prediction Dashboard!',
    brand_style={'color': 'white'},
    color='success',
    sticky='top',
)


app.layout = Div([
    navbar,
    Row([
        Col([
            forecast_card,
            Row([Col(weather_info, lg=4),
                 Col(weather_card, lg=8)])
        ], lg=8, align='start'),
        Col(map_card, lg=4, align='start')
    ],
        style={'width': '90%', 'margin': 'auto'})
])


@app.callback(
    Output('forecast-plot', 'figure'),
    Input('farm-select', 'value'),
    Input('day-select', 'value')
)
def update_forecast_plot(farm, day):
    if not farm:
        farm = DEFAULT_FARM
    if not day:
        day = DEFAULT_DAY
    df = pd.DataFrame(DB[farm].find(
        {}, {'prediction': 1, 'actual': 1}).sort('_id', -1).limit(int(day)))
    df['time'] = df._id.apply(lambda t: arrow.get(
        t).to(TZ).format('YYYY-MM-DD HH:mm:SS'))

    return plot_forecast(df, farm)


@app.callback(
    Output('weather-plot', 'figure'),
    Input('farm-select', 'value'),
    Input('day-select', 'value')
)
def update_weather_plot(farm, day):
    if not farm:
        farm = DEFAULT_FARM
    if not day:
        day = DEFAULT_DAY

    df = pd.DataFrame(DB[farm].find({}, {'temperature': 1, 'wind_gust': 1,
                                         'wind_speed': 1, 'actual': 1}).sort('_id', -1).limit(int(day)))
    df['time'] = df._id.apply(lambda t: arrow.get(
        t).to(TZ).format('YYYY-MM-DD HH:mm:SS'))

    return plot_weather(df, farm)


@app.callback(
    Output('plot-title', 'children'),
    Input('farm-select', 'value'),
)
def update_plot_title(farm):
    if not farm:
        farm = DEFAULT_FARM

    return html.H5(f'Hourly wind power forecast at {FARMS[farm]}')


@app.callback(
    Output('weather', 'children'),
    Input('farm-select', 'value'),
)
def update_weather(farm):
    if not farm:
        farm = DEFAULT_FARM

    df = pd.DataFrame(DB[farm].find({}, {'icon': 1,  'temperature': 1,
                                         'wind_gust': 1, 'wind_speed': 1, 'actual': 1}).sort('_id', -1).limit(3*24))
    df['time'] = df._id.apply(lambda t: arrow.get(
        t).to(TZ).format('YYYY-MM-DD HH:mm:SS'))

    latest = df[df.actual.isna()].index[-1]+1

    icon = df.loc[latest, 'icon']
    if not icon:
        icon = 'default'

    url = f'https://raw.githubusercontent.com/hengwang322/wind_web_app/master/resources/{icon}.gif'
    temp = df.loc[latest, 'temperature']
    wind = df.loc[latest, 'wind_speed']
    gust = df.loc[latest, 'wind_gust']

    weather = [
        html.H5(f'Current Weather:'),
        html.P(
            f'Wind: {wind} (m/s), gust: {gust} (m/s), temperature: {temp} °C.'),
        html.Img(src=url, style={'width': 150, 'height': 120})
    ]

    return weather


@app.callback(
    Output('modal', 'is_open'),
    [Input('open', 'n_clicks'), Input('close', 'n_clicks')],
    [State('modal', 'is_open')],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


if __name__ == '__main__':
    app.run_server(debug=True)
