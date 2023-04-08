import dash
from dash import dcc, html, dash_table, Output, Input, State
import pandas as pd
import plotly.express as px
from dash.exceptions import PreventUpdate
import os
import itertools
import plotly.graph_objects as go
from calendar import month_name
from helpers import getDirNames, filter_processed, calculate_delta, get_calculated_csv_files


app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport",
                "content": "width=device-width, initial-scale=1"}],
)
server = app.server
app.title = "Dashboard"

app_color = {"graph_bg": "#FFFFFF", "graph_line": "#0091D5"}


YEARS_ROOT_DIR = r'./Data/Years'
years = getDirNames(YEARS_ROOT_DIR)


# --------------- Dashboard Layout ---------------------
app.layout = html.Div(
    [
        html.Div(
            [
                # graph plot
                html.Div(
                    [
                        html.Div([
                            html.Div(
                                [
                                    html.H6("Year Selection"),
                                    dcc.Dropdown(
                                        id="year_selection",
                                        className="dropdown",
                                        options=years,
                                        value=years[0],
                                    )
                                ],
                                className="four columns",
                            ),
                            html.Div(
                                [
                                    html.H6("Month Selection"),
                                    dcc.Dropdown(
                                        id="month_selection",
                                        className="dropdown"
                                    )
                                ],
                                className="four columns",
                            ),
                            html.Div(
                                [
                                    html.H6("Week Selection"),
                                    dcc.Dropdown(
                                        id="week_selection",
                                        className="dropdown"
                                    )
                                ],
                                className="four columns",
                            ),
                        ]),
                        dcc.Store(id='data_store', data=None),
                        html.Div(
                            [html.H6("GEX per Expiry", className="graph__title")]
                        ),
                        dcc.Loading([
                            dcc.Graph(
                                id="chart1",
                                figure=dict(
                                    layout=dict(
                                        plot_bgcolor=app_color["graph_bg"],
                                        paper_bgcolor=app_color["graph_bg"],
                                    )
                                ),
                                style={'padding': 0, 'margin-top': '10px',
                                       'width': '100%', 'height': '100%'}
                            ),
                        ]),
                        html.Div(
                            [html.H6("MM_Contracts or GEX per Strike",
                                     className="graph__title")]
                        ),
                        dcc.Loading([
                            dcc.RadioItems(
                                id="chart2_toggle",
                                options=['Running_MM_Contracts_balance',
                                    'GEX'],
                                value='Running_MM_Contracts_balance',
                                inline=True
                            ),
                            dcc.Graph(
                                id="chart2",
                                figure=dict(
                                    layout=dict(
                                        plot_bgcolor=app_color["graph_bg"],
                                        paper_bgcolor=app_color["graph_bg"],
                                    )
                                ),
                                style={'padding': 0, 'margin-top': '10px',
                                       'width': '100%', 'height': '100%'}
                            ),
                        ]),
                        html.Div(
                            [html.H6("Total GEX", className="graph__title")]
                        ),
                        dcc.Loading([
                            dcc.Graph(
                                id="chart3",
                                figure=dict(
                                    layout=dict(
                                        plot_bgcolor=app_color["graph_bg"],
                                        paper_bgcolor=app_color["graph_bg"],
                                    )
                                ),
                                style={'padding': 0, 'margin-top': '10px',
                                       'width': '100%', 'height': '100%'}
                            ),
                        ]),
                    ],
                    className="twelve columns subplots__container",
                ),
            ],
            className="app__content",
        ),
    ],
    className="app__container",
)


# ------------- Callback Methods ----------------

# callback method to get months from years
@app.callback(
    [Output("month_selection", "options"),
     Output("month_selection", "value")],
    [Input("year_selection", "value")]
)
def get_months(year):
    if year:
        month_lookup = list(month_name)
        monthsRootDir = f"./Data/Years/{year}"
        months = getDirNames(monthsRootDir)
        months = sorted(months, key=month_lookup.index)
        return [months, months[0]]
    raise PreventUpdate

# callback method to get weeks from years and months
@app.callback(
    [Output("week_selection", "options"),
     Output("week_selection", "value")],
    [Input("year_selection", "value"),
     Input("month_selection", "value")]
)
def get_weeks(year, month):
    if month:
        weeksRootDir = f"./Data/Years/{year}/{month}/C/"
        weeks = getDirNames(weeksRootDir)
        return [weeks, weeks[0]]
    raise PreventUpdate


# callback method to get graph 1 and graph 2 from year, month and week
@app.callback(
    [Output("chart1", "figure"),
     Output("chart2", "figure")],
    [Input("year_selection", "value"),
     Input("month_selection", "value"),
     Input("week_selection", "value"),
     Input("chart2_toggle", "value")],
    prevent_initial_call=True
)
def render_graphs(year, month, week, toggle_value):
    if week:
        option_C_path = f"./Data/Years/{year}/{month}/C/{week}/Raw/"
        option_P_path = f"./Data/Years/{year}/{month}/P/{week}/Raw/"
        option_C_files = filter_processed(option_C_path)
        option_P_files = filter_processed(option_P_path)

        calculated_C_data, calculated_P_data = get_calculated_csv_files(
            option_C_path, option_P_path, option_C_files, option_P_files)

        # combine both calculated csv files and add the GEX columns
        putgex_plus_callGex = pd.concat(
            [calculated_C_data, calculated_P_data], axis=0, join='outer')
        putgex_plus_callGex['GEX_Sum'] = putgex_plus_callGex.loc[:, [
            'GEX_C', 'GEX_P']].sum(axis=1)

        # group data by date ( 1 day ) and sum the GEX for each day
        grouped_C = calculated_C_data.groupby(
            'datetime')['GEX_C'].sum().reset_index()
        grouped_P = calculated_P_data.groupby(
            'datetime')['GEX_P'].sum().reset_index()
        grouped_P_C = putgex_plus_callGex.groupby(
            'datetime')['GEX_Sum'].sum().reset_index()

        # creating chart 1 figure
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=grouped_C['datetime'], y=grouped_C['GEX_C'],
                                  mode='lines',
                                  name='Call'))
        fig1.add_trace(go.Scatter(x=grouped_P['datetime'], y=grouped_P['GEX_P'],
                                  mode='lines',
                                  name='Put'))
        fig1.add_trace(go.Scatter(x=grouped_P_C['datetime'], y=grouped_P_C['GEX_Sum'],
                                  mode='lines',
                                  name='Call+Put'))
        fig1.update_layout(title='DateTime Vs GEX',
                           xaxis_title='DateTime',
                           yaxis_title='GEX',
                           template='plotly_dark',
                           )

        # creating chart 2 figure
        calculated_C_data.sort_values(
            by='datetime', ascending=False, inplace=True, ignore_index=True)
        calculated_P_data.sort_values(
            by='datetime', ascending=False, inplace=True, ignore_index=True)

        calculated_C_data = calculated_C_data[calculated_C_data['Date']
                                              == calculated_C_data.loc[0, 'Date']]
        calculated_P_data = calculated_P_data[calculated_P_data['Date']
                                              == calculated_P_data.loc[0, 'Date']]

        fig2 = go.Figure()
        # decide the column for GEX for Call and Put data
        if toggle_value == "GEX":
            toggle_C = f"GEX_C"
            toggle_P = f"GEX_P"
        else:
            toggle_C = toggle_value
            toggle_P = toggle_value

        fig2.add_trace(go.Bar(x=calculated_C_data['Strike'], y=calculated_C_data[toggle_C],
                              base=0,
                              name='Call'))
        fig2.add_trace(go.Bar(x=calculated_P_data['Strike'], y=calculated_P_data[toggle_P],
                              base=0,
                              name='Put'))
        fig2.update_layout(title=f'Strike Vs {toggle_value}',
                           xaxis_title='Strike',
                           yaxis_title=toggle_value,
                           xaxis=dict(type="category",
                                       categoryorder='category ascending'),
                           yaxis=dict(type="linear",
                                      autorange=True),
                           template='plotly_dark',
                           # barmode='group'
                           )
        return [fig1, fig2]
    raise PreventUpdate


@app.callback(
    [Output("chart3", "figure")],
    [Input("year_selection", "value"),
     Input("month_selection", "value"),
     Input("week_selection", "options")],
    prevent_initial_call=True
)
def render_chart3(year, month, weeks):
    if month:
        fig = go.Figure()
        master_files_path = f"./Data/Years/{year}/{month}/"
        try:
            master_grouped_C = pd.read_csv(
                master_files_path+"master_grouped_C.csv")
            master_grouped_P = pd.read_csv(
                master_files_path+"master_grouped_P.csv")
            master_grouped_P_C = pd.read_csv(
                master_files_path+"master_grouped_P_C.csv")
        except FileNotFoundError:
            master_grouped_C = pd.DataFrame()
            master_grouped_P = pd.DataFrame()
            master_grouped_P_C = pd.DataFrame()
            for week in weeks:
                option_C_path = f"./Data/Years/{year}/{month}/C/{week}/Raw/"
                option_P_path = f"./Data/Years/{year}/{month}/P/{week}/Raw/"
                option_C_files = filter_processed(option_C_path)
                option_P_files = filter_processed(option_P_path)

                calculated_C_data, calculated_P_data = get_calculated_csv_files(
                    option_C_path, option_P_path, option_C_files, option_P_files)

                # combine both calculated csv files and add the GEX columns
                putgex_plus_callGex = pd.concat(
                    [calculated_C_data, calculated_P_data], axis=0, join='outer')
                putgex_plus_callGex['GEX_Sum'] = putgex_plus_callGex.loc[:, [
                    'GEX_C', 'GEX_P']].sum(axis=1)

                grouped_C = calculated_C_data.groupby(
                    'datetime')['GEX_C'].sum().reset_index()
                grouped_P = calculated_P_data.groupby(
                    'datetime')['GEX_P'].sum().reset_index()
                grouped_P_C = putgex_plus_callGex.groupby(
                    'datetime')['GEX_Sum'].sum().reset_index()

                master_grouped_C = pd.concat([grouped_C, master_grouped_C])
                master_grouped_P = pd.concat([grouped_P, master_grouped_P])
                master_grouped_P_C = pd.concat(
                    [grouped_P_C, master_grouped_P_C])

            master_grouped_C.to_csv(
                master_files_path+"master_grouped_C.csv")
            master_grouped_P.to_csv(
                master_files_path+"master_grouped_P.csv")
            master_grouped_P_C.to_csv(
                master_files_path+"master_grouped_P_C.csv")

        master_grouped_C = master_grouped_C.groupby(
            'datetime')['GEX_C'].sum().reset_index()
        master_grouped_P = master_grouped_P.groupby(
            'datetime')['GEX_P'].sum().reset_index()
        master_grouped_P_C = master_grouped_P_C.groupby(
            'datetime')['GEX_Sum'].sum().reset_index()

        fig.add_trace(go.Scatter(x=master_grouped_C['datetime'], y=master_grouped_C['GEX_C'],
                                 mode='lines',
                                 name='Call'))
        fig.add_trace(go.Scatter(x=master_grouped_P['datetime'], y=master_grouped_P['GEX_P'],
                                 mode='lines',
                                 name='Put'))
        fig.add_trace(go.Scatter(x=master_grouped_P_C['datetime'], y=master_grouped_P_C['GEX_Sum'],
                                 mode='lines',
                                 name='Call+Put'))

        fig.update_layout(title='DateTime Vs GEX',
                          xaxis_title='DateTime',
                          yaxis_title='GEX',
                          template='plotly_dark',
                          )
        return [fig]
    raise PreventUpdate


if __name__ == "__main__":
    app.run_server(debug=True)
