import os

import arrow
import dash_bootstrap_components as dbc
from dash import Dash, dcc, html
from dash.dependencies import Input, Output, State
from dash.html import Div
from dash_bootstrap_components import Card, CardBody, CardHeader, Col, Row
from pymongo import MongoClient

from const import FARMS, TZ
from plot import plot_forecast, plot_map, plot_weather

app = Dash(__name__,
           meta_tags=[{'name': 'viewport',
                       'content': 'width=device-width'}],
           external_stylesheets=[dbc.themes.FLATLY]
           )
app.title = 'Wind Dashboard'

MONGO_URI = os.environ.get('MONGO_URI')
DB = MongoClient(MONGO_URI)['wpp']
DEFAULT_FARM = list(FARMS.keys())[0]
DEFAULT_DAY = 4 * 24
FARM_OPTIONS = [{'label': v, 'value': k} for k, v in FARMS.items()]
RANGE_OPTIONS = [{'label': k, 'value': v} for k, v in
                 {'Past 2 Days': ((2+2)*24), 'Past Week': ((2+7)*24), 'Past Month': ((2+30)*24),
                  'Past 3 Months': ((2+90)*24), 'Past 6 Months': ((2+180)*24),
                  'Past Year': ((2+365)*24), 'All time': 0}.items()
                 ]
TIME_FORMAT = 'YYYY-MM-DD HH:mm:SS'

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
            style={'width': 150, 'margin': 5}), align='start'
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

    projections = {'prediction': 1, 'actual': 1}
    conn = DB[farm].find({}, projections).sort('_id', -1).limit(int(day))
    data = list(conn)

    time = [d['_id'] for d in data]
    time = [arrow.get(t).to(TZ).format(TIME_FORMAT) for t in time]
    pred = [d['prediction'] for d in data]
    actual = [d.get('actual') for d in data]
    actual = [round(i, 2) if i is not None else None for i in actual]

    return plot_forecast(time, pred, actual)


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

    projections = {'temperature': 1, 'wind_gust': 1,
                   'wind_speed': 1, 'actual': 1}
    conn = DB[farm].find({}, projections).sort('_id', -1).limit(int(day))
    data = list(conn)

    time = [d['_id'] for d in data]
    time = [arrow.get(t).to(TZ).format(TIME_FORMAT) for t in time]
    actual = [d.get('actual') for d in data]
    actual = [round(i, 2) if i is not None else None for i in actual]
    temperature = [d.get('temperature') for d in data]
    wind_gust = [d.get('wind_gust') for d in data]
    wind_speed = [d.get('wind_speed') for d in data]

    return plot_weather(time, actual, temperature, wind_gust, wind_speed)


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
    filters = {"actual": {"$exists": "true"}}
    projections = {'icon': 1,  'temperature': 1,
                   'wind_gust': 1, 'wind_speed': 1}

    conn = DB[farm].find(filters, projections).sort('_id', -1).limit(1)
    data = list(conn)[0]

    icon = data.get('icon')
    temp = data['temperature']
    wind = data['wind_speed']
    gust = data['wind_gust']

    if not icon:
        icon = 'default'

    url = f'https://raw.githubusercontent.com/hengwang322/wind_web_app/master/resources/{icon}.gif'

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

dapp = app.server.wsgi_app

if __name__ == '__main__':
    app.run_server(debug=True)
