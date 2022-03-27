import csv
import os
import urllib.request

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from const import FARMS

# define some common stylings
COLORS = ['#636EFA', '#EF553B', '#00CC96',
          '#AB63FA', '#FFA15A', '#19D3F3',
          '#FF6692', '#B6E880', '#FF97FF',
          '#FECB52']
LIGHT_GREY = '#bebebe'
MAPBOX_TOKEN = os.environ.get('MAPBOX_TOKEN')

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
    hoverlabel=dict(namelength=-1),
    legend=horizontal_legend,)

url_prefix = 'https://raw.githubusercontent.com/hengwang322/wind_web_app/master/resources/'
url_suffix = '.gif'


def plot_map():
    farm_overview = 'https://services.aremi.data61.io/aemo/v6/csv/wind'
    response = urllib.request.urlopen(farm_overview)
    lines = [l.decode('utf-8') for l in response.readlines()]
    data_rows = list(csv.reader(lines))
    rows = data_rows[1:]

    data = [row for row in rows if row[20] in FARMS.keys()]
    names = [d[0] for d in data]
    power = [float(d[1]) for d in data]
    lat = [round(float(d[21]), 3) for d in data]
    lon = [round(float(d[22]), 3) for d in data]

    fig = go.Figure(go.Scattermapbox(
        lat=lat,
        lon=lon,
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=[i / 3 + 3 for i in power],
            color=power,
            colorscale='Viridis',
            colorbar=dict(
                title='Power (MW)',
                x=0.01,
                y=0.99,
                yanchor='top',
                len=0.3,
                bgcolor='white'
            )),
        hovertext=[f'{s}: {p} (MW)' for s, p in zip(names, power)],
    ))

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=10, t=10, b=10),
        mapbox=dict(
            accesstoken=MAPBOX_TOKEN,
            center={'lat': -35.5, 'lon': 137.5},
            zoom=5
        ),
    )

    return fig


def plot_forecast(time, pred, actual):
    latest = len([i for i in actual if i is None])
    fig = go.Figure()

    # Plot the dashed line first, hide their legends, then plot solid lines and
    # show legends. Legneds are grouped so they can be hide/unhide at same time
    fig.add_trace(go.Scatter(
        x=time[:latest+1],
        y=[round(i, 2) for i in pred[:latest+1]],
        name='Prediction (Forecast)',
        legendgroup='Forecast',
        showlegend=False,
        line={'dash': 'dash', 'color': COLORS[1]}
    ))
    fig.add_trace(go.Scatter(
        x=time,
        y=[round(i, 2) if i is not None else None for i in actual],
        name='Actual',
        legendgroup='Actual',
        line={'dash': 'solid', 'color': COLORS[0]}
    ))
    fig.add_trace(go.Scatter(
        x=time[latest:],
        y=[round(i, 2) if i is not None else None for i in pred[latest:]],
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


def plot_weather(time, actual, temperature, wind_gust, wind_speed):
    latest = len([i for i in actual if i is None])
    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.1)

    # Plot the dashed line first, hide their legends, then plot solid lines and
    # show legends. Legneds are grouped so they can be hide/unhide at same time
    fig.add_trace(go.Scatter(
        x=time[:latest+1],
        y=wind_speed[:latest+1],
        name='Wind (Forecast)',
        legendgroup='Wind',
        showlegend=False,
        line={'dash': 'dash', 'color': COLORS[2]}
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=time[:latest+1],
        y=wind_gust[:latest+1],
        name='Gust (Forecast)',
        legendgroup='Gust',
        showlegend=False,
        line={'dash': 'dash', 'color': COLORS[3]}
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=time[:latest+1],
        y=temperature[:latest+1],
        name='Temp (Forecast)',
        legendgroup='Temp',
        showlegend=False,
        line={'dash': 'dash', 'color': COLORS[4]}
    ), row=1, col=2)
    fig.add_trace(go.Scatter(
        x=time[latest:],
        y=wind_speed[latest:],
        name='Wind',
        legendgroup='Wind',
        line={'dash': 'solid', 'color': COLORS[2]}
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=time[latest:],
        y=wind_gust[latest:],
        name='Gust',
        legendgroup='Gust',
        line={'dash': 'solid', 'color': COLORS[3]}
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=time[latest:],
        y=temperature[latest:],
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
