import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import dash_table
import plotly.express as px

df = pd.read_csv('aggr.csv', parse_dates=['Entry time'])

df['Entry time'] = pd.to_datetime(df['Entry time'])
df['YearMonth'] = pd.to_datetime(df['Entry time'].map(lambda x: x.strftime('%Y-%m')))

#def filter_df(Exchange, Margin, start_date, end_date, df):
#    data = [df['Exchange'] == Exchange & df['Margin'] == int(Margin) & df['Entry time'] >= start_date & df['Entry time'] <= end_date ]
#    return data

def filter_df(df,exchange,margin,start_date,end_date):
    #Filters
    dfTemp = df[df['Exchange'] == exchange]
    dfTemp = dfTemp[dfTemp['Margin'] == int(margin)]
    dfTemp = dfTemp[dfTemp['Entry time'] >= start_date]
    dfTemp = dfTemp[dfTemp['Entry time'] <= end_date]
    #Sort
    dfTemp.sort_values(by='Entry time', ascending = False)
    return dfTemp


app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/uditagarwal/pen/oNvwKNP.css', 'https://codepen.io/uditagarwal/pen/YzKbqyV.css'])

app.layout = html.Div(children=[
    html.Div(
            children=[
                html.H2(children="Bitcoin Leveraged Trading Backtest Analysis", className='h2-title'),
            ],
            className='study-browser-banner row'
    ),
    html.Div(
        className="row app-body",
        children=[
            html.Div(
                className="twelve columns card",
                children=[
                    html.Div(
                        className="padding row",
                        children=[
                            html.Div(
                                className="two columns card",
                                children=[
                                    html.H6("Select Exchange",),
                                    dcc.RadioItems(
                                        id="exchange-select",
                                        options=[
                                            {'label': label, 'value': label} for label in df['Exchange'].unique()
                                        ],
                                        value='Bitmex',
                                        labelStyle={'display': 'inline-block'}
                                    )
                                ]
                            ),
                            # Leverage Selector
                            html.Div(
                                className="two columns card",
                                children=[
                                    html.H6("Select Leverage"),
                                    dcc.RadioItems(
                                        id="leverage-select",
                                        options=[
                                            {'label': str(label), 'value': str(label)} for label in df['Margin'].unique()
                                        ],
                                        value='1',
                                        labelStyle={'display': 'inline-block'}
                                    ),
                                ]
                            ),
                            html.Div(
                                className="three columns card",
                                children=[
                                    html.H6("Select a Date Range"),
                                    dcc.DatePickerRange(
                                        id="date-range",
                                        display_format="MMM YY",
                                        start_date=df['Entry time'].min(),
                                        end_date=df['Entry time'].max()
                                    ),
                                ]
                            ),
                            html.Div(
                                id="strat-returns-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="strat-returns", className="indicator_value"),
                                    html.P('Strategy Returns', className="twelve columns indicator_text"),
                                ]
                            ),
                            html.Div(
                                id="market-returns-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="market-returns", className="indicator_value"),
                                    html.P('Market Returns', className="twelve columns indicator_text"),
                                ]
                            ),
                            html.Div(
                                id="strat-vs-market-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="strat-vs-market", className="indicator_value"),
                                    html.P('Strategy vs. Market Returns', className="twelve columns indicator_text"),
                                ]
                            ),
                        ]
                )
        ]),
        html.Div(
            className="twelve columns card",
            children=[
                dcc.Graph(
                    id="monthly-chart",
                    figure={
                        'data': []
                    }
                )
            ]
        ),
        html.Div(
                className="padding row",
                children=[
                    html.Div(
                        className="six columns card",
                        style={'height': '400px', 'margin-left': '0px'},
                        children=[
                            dash_table.DataTable(
                                id='table',
                                columns=[
                                    {'name': 'Number', 'id': 'Number'},
                                    {'name': 'Trade type', 'id': 'Trade type'},
                                    {'name': 'Exposure', 'id': 'Exposure'},
                                    {'name': 'Entry balance', 'id': 'Entry balance'},
                                    {'name': 'Exit balance', 'id': 'Exit balance'},
                                    {'name': 'Pnl (incl fees)', 'id': 'Pnl (incl fees)'},
                                ],
                                style_cell={'width': '50px'},
                                style_table={
                                    'maxHeight': '450px',
                                    'overflowY': 'scroll'
                                },
                            )
                        ]
                    ),
                    dcc.Graph(
                        id="pnl-types",
                        className="six columns card",
                        style={'height': '300px', 'margin-left': '0px'},
                        figure={}
                    )
                ]
            ),
            html.Div(
                className="padding row",
                children=[
                    dcc.Graph(
                        id="daily-btc",
                        className="six columns card",
                        style={'height': '500px', 'margin-left': '0px'},
                        figure={}
                    ),
                    dcc.Graph(
                        id="balance",
                        className="six columns card",
                        style={'height': '500px', 'margin-left': '0px'},
                        figure={}
                    )
                ]
            )
        ]
    )        
])


#Update Dates
@app.callback(
        [
        dash.dependencies.Output('date-range', 'start_date'), # input with id date-picker-range and the start_date parameter
        dash.dependencies.Output('date-range', 'end_date')
        ],
        (dash.dependencies.Input('exchange-select', 'value'),)
)
def update_date_values(value):
    dfTemp = df[df['Exchange'] == value]
    dfTemp['Entry time'] = pd.to_datetime(dfTemp['Entry time'])
    return (dfTemp['Entry time'].min(), dfTemp['Entry time'].max())



def update_date_range(value):
    df2 = df[df['Exchange'] == value]
    start_date = df2['Entry time'].min()
    end_date = df2['Entry time'].max()
    return  (start_date, end_date)

def calc_returns_over_month(dff):
    out = []

    for name, group in dff.groupby('YearMonth'):
        exit_balance = group.head(1)['Exit balance'].values[0]
        entry_balance = group.tail(1)['Entry balance'].values[0]
        monthly_return = (exit_balance*100 / entry_balance)-100
        out.append({
            'month': name,
            'entry': entry_balance,
            'exit': exit_balance,
            'monthly_return': monthly_return
        })
    return out

def calc_btc_returns(dff):
    btc_start_value = dff.tail(1)['BTC Price'].values[0]
    btc_end_value = dff.head(1)['BTC Price'].values[0]
    btc_returns = (btc_end_value * 100/ btc_start_value)-100
    return btc_returns

def calc_strat_returns(dff):
    start_value = dff.tail(1)['Exit balance'].values[0]
    end_value = dff.head(1)['Entry balance'].values[0]
    returns = (end_value * 100/ start_value)-100
    return returns

def update_monthly(exchange, leverage, start_date, end_date):
    dff = filter_df(df, exchange, leverage, start_date, end_date)
    data = calc_returns_over_month(dff)
    btc_returns = calc_btc_returns(dff)
    strat_returns = calc_strat_returns(dff)
    strat_vs_market = strat_returns - btc_returns

    return {
        'data': [
            go.Candlestick(
                open=[each['entry'] for each in data],
                close=[each['exit'] for each in data],
                x=[each['month'] for each in data],
                low=[each['entry'] for each in data],
                high=[each['exit'] for each in data]
            )
        ],
        'layout': {
            'title': 'Overview of Monthly performance'
        }
    }, f'{btc_returns:0.2f}%', f'{strat_returns:0.2f}%', f'{strat_vs_market:0.2f}%'

#Update Candle Chart
@app.callback(
    [
        dash.dependencies.Output('monthly-chart', 'figure'),
        dash.dependencies.Output('market-returns', 'children'),
        dash.dependencies.Output('strat-returns', 'children'),
        dash.dependencies.Output('strat-vs-market', 'children'),
    ],
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range', 'start_date'),
        dash.dependencies.Input('date-range', 'end_date'),

    )
)
def update_monthly(exchange, leverage, start_date, end_date):
    dff = filter_df(df, exchange, leverage, start_date, end_date)
    data = calc_returns_over_month(dff)
    btc_returns = calc_btc_returns(dff)
    strat_returns = calc_strat_returns(dff)
    strat_vs_market = strat_returns - btc_returns

    return {
        'data': [
            go.Candlestick(
                open=[each['entry'] for each in data],
                close=[each['exit'] for each in data],
                x=[each['month'] for each in data],
                low=[each['entry'] for each in data],
                high=[each['exit'] for each in data]
            )
        ],
        'layout': {
            'title': 'Overview of Monthly performance'
        }
    }, f'{btc_returns:0.2f}%', f'{strat_returns:0.2f}%', f'{strat_vs_market:0.2f}%'


#Update Bar chart
@app.callback(
    dash.dependencies.Output('pnl-types', 'figure'),
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range', 'start_date'),
        dash.dependencies.Input('date-range', 'end_date'),
    )
)
def update_bar_chart(exchange, leverage, start_date, end_date):
    dfTemp = filter_df(df, exchange, leverage, start_date, end_date)
    dff_long = dfTemp[dfTemp['Trade type']=='Long']
    dff_short = dfTemp[dfTemp['Trade type']=='Short']
    return {
        'data': [go.Bar(
                    x=dff_long['Entry time'],
                    y=dff_long['Pnl (incl fees)'],
                    name='PNL Types',
                    marker_color='blue'
                    ),
            go.Bar(
                x=dff_short['Entry time'],
                y=dff_short['Pnl (incl fees)'],
                name='short',
                marker_color='black'
            )
                ],
            'layout': {
                'title': 'Bar chart PNL Types'
            }
    }

#Update table
@app.callback(
    dash.dependencies.Output('table', 'data'),
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range', 'start_date'),
        dash.dependencies.Input('date-range', 'end_date'),
    )
)
def update_table(exchange, leverage, start_date, end_date):
    dff = filter_df(df, exchange, leverage, start_date, end_date)
    return dff.to_dict('records')


#Update line Charts
@app.callback(
    dash.dependencies.Output('daily-btc', 'figure'),
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range', 'start_date'),
        dash.dependencies.Input('date-range', 'end_date'),
    )
)
def update_daily_btc(exchange, leverage, start_date, end_date):
    dfTemp = filter_df(df, exchange, leverage, start_date, end_date)
    return {
        'data' : [go.Scatter(x=dfTemp['Entry time'], y=dfTemp['BTC Price'],
                    marker_color ='green',
                    name='BTC Balance')],

                    'layout' : {
                        'title' : 'BTC Daily'
                    }
    }


@app.callback(
    dash.dependencies.Output('balance', 'figure'),
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range', 'start_date'),
        dash.dependencies.Input('date-range', 'end_date'),
    )
)
def update_balance(exchange, leverage, start_date, end_date):
    dfTemp = filter_df(df, exchange, leverage, start_date, end_date)
    return {
        'data' : [go.Scatter(x=dfTemp['Entry time'], y=dfTemp['Exit balance'],
                    marker_color ='Blue',
                    name='Daily Balance')],

                    'layout' : {
                        'title' : 'Balance'
                    }

    }



if __name__ == "__main__":
    app.run_server(debug=True)

