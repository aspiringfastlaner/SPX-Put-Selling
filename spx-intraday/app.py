# Import required libraries
import os
import datetime as dt

import numpy as np
import pandas as pd
import plotly.plotly as py
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go

from data_spxfetch import *


# Setup app
# server = flask.Flask(__name__)
# server.secret_key = os.environ.get('secret_key', 'secret')
# app = dash.Dash(__name__, server=server, url_base_pathname='/dash/gallery/volatility-surface', csrf_protect=False)
app = dash.Dash()

external_css = ["https://fonts.googleapis.com/css?family=Overpass:300,300i",
                "https://cdn.rawgit.com/plotly/dash-app-stylesheets/dab6f937fd5548cebf4c6dc7e93a10ac438f5efb/dash-technical-charting.css"]

for css in external_css:
    app.css.append_css({"external_url": css})

if 'DYNO' in os.environ:
    app.scripts.append_script({
        'external_url': 'https://cdn.rawgit.com/chriddyp/ca0d8f02a1659981a0ea7f013a378bbd/raw/e79f3f789517deec58f41251f7dbb6bee72c44ab/plotly_ga.js'
    })



# Make app layout
app.layout = html.Div(
    [
        html.Div([
            html.Img(
                src="http://fchen.info/wp-content/uploads/2016/10/fclogo2.png",
                className='two columns',
                style={
                    'height': '60',
                    'width': '60',
                    'float': 'left',
                    'position': 'relative',
                },
            ),
            html.H1(
                'Intraday SPX Movements',
                className='eight columns',
                style={'text-align': 'center'}
            ),
            html.Img(
                src="https://s3-us-west-1.amazonaws.com/plotly-tutorials/logo/new-branding/dash-logo-by-plotly-stripe.png",
                className='two columns',
                style={
                    'height': '60',
                    'width': '135',
                    'float': 'right',
                    'position': 'relative',
                },
            ),
        ],
            className='row'
        ),
        html.Hr(style={'margin': '0', 'margin-bottom': '5'}),
        html.Div([
            html.H4(
                'Intraday Vol Plot',
                className='twelve columns',
                style={'text-align': 'center'}
            ),
        ],
            className='row',
            style={'margin-bottom': '20'}
        ), 
        html.Div([
            dcc.Graph(id='intraday_vol_plot', style={'max-height': '600', 'height': '60vh'}),
            dcc.Interval(
                    id='interval-component',
                    interval=60*1000, # in milliseconds
                    n_intervals=0
                    )
        ],
            className='row',
            style={'margin-bottom': '20'}
        ),
    
        html.Div([
            html.Div([
                dcc.Graph(id='std_historical_plot', style={'max-height': '400', 'height': '40vh'}),
            ],
                className='twelve columns'
            )
        ],
            className='row',
            style={'margin-bottom': '20'}
        ),
    
        
    ],
    style={
        'width': '85%',
        'max-width': '1200',
        'margin-left': 'auto',
        'margin-right': 'auto',
        'font-family': 'overpass',
        'background-color': '#FFFFFF',
        'padding': '40',
        'padding-top': '20',
        'padding-bottom': '20',
    },
)

#%%

# Multiple components can update everytime interval gets fired.
@app.callback(Output('intraday_vol_plot', 'figure'),
              [Input('interval-component', 'n_intervals')])
def update_graph_live(n):
    intraday_data = get_intraday_data()

    trace1 = {
        'name':'Intraday Dollar Vol',
        "type": 'bar',
        'mode': 'markers',
        'x': intraday_data.index,
        'y': intraday_data['Dollar Std Move'],
        'boxpoints': 'outliers',
        'marker': {'color': '#00aaff', 'opacity': 0.8}
    }
    
    trace2 = {
        "type": 'scatter',
        'mode': 'lines+markers',
        'name': 'SPX Close',
        'x': intraday_data.index,
        'y': intraday_data['Last'],
        'yaxis': 'y2',
        'marker': {'color': '#ff7f0e', 'opacity': 0.8}
    }   
    
    layout = {
        'margin': {
            'l': 60,
            'r': 10,
            'b': 60,
            't': 10,
        },
        'paper_bgcolor': '#FAFAFA',
        "xaxis": {
            "title": "Date",
        },
        "yaxis": {
            "rangemode": "tozero",
            "title": "Dollar Return Std.",
            "side": "left"
        },
        "yaxis2": {
            "title": "SPX",
            "overlaying": "y",
            "side": "right"}
    }
        
    data = [trace1, trace2]
    figure = dict(data=data, layout=layout)
    return figure

# Make side std hist plot
@app.callback(Output('hv_std_hist', 'figure'),
              [Input('filtered_container', 'hidden'),
               Input('ticker_dropdown', 'value'),
               Input('graph_toggles', 'values')],
              [State('graph_toggles', 'values'),
               State('hv_std_hist', 'relayoutData')])
def make_dollar_hist(hidden, ticker, graph_toggles,
                     graph_toggles_state, iv_scatter_layout):

    if hidden == 'loaded':

        if 'discrete' in graph_toggles:
            shading = 'contour'
        else:
            shading = 'heatmap'

        typ = 'histogram'

        trace1 = {
            "type": typ,
            'mode': 'markers',
            'histnorm': 'probability',
            'x': hist_data.daily_dollar_std_direction,
            'marker': {'color': '#00aaff', 'opacity': 0.8}
        }

        layout = {
            'margin': {
                'l': 60,
                'r': 10,
                'b': 60,
                't': 10,
            },
            'paper_bgcolor': '#FAFAFA',
            "hovermode": "closest",
            "xaxis": {
                "title": "Dollar Return Std.",
            },
            "yaxis": {
                "rangemode": "tozero",
                "title": "Percentage Distribution",
            },
            'bargap' : 0.2,
            'bargroupgap': 0.1
        }

        if (iv_scatter_layout is not None and 'lock' in graph_toggles_state):

            try:
                x_range_left = iv_scatter_layout['xaxis.range[0]']
                x_range_right = iv_scatter_layout['xaxis.range[1]']
                layout['xaxis']['range'] = [x_range_left, x_range_right]
            except:
                pass

            try:
                y_range_left = iv_scatter_layout['yaxis.range[0]']
                y_range_right = iv_scatter_layout['yaxis.range[1]']
                layout['yaxis']['range'] = [x_range_left, x_range_right]
            except:
                pass

        data = [trace1]
        figure = dict(data=data, layout=layout)
        return figure

if __name__ == '__main__':
    app.server.run(port=1000, debug=True, threaded=True, use_reloader=False)
