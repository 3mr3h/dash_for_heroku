'''
    DeepDive Team, Ekrem Bilgehan Uyar, Sana Basharat, Emre Caglar Hosgor
    18.12.2022
    DI 502
    Prof. Tugba Taskaya Temizel
    Prof. Altan Kocyigit
    
    Python Dash-based implementation for displaying
        the investment recommendations to a user about
        TRY-based KKM or USD gain.
'''
import base64
import io
import plotly.graph_objs as go
import cufflinks as cf

# Dash imports
import dash
from dash import Dash, dash_table, html, dcc
from dash.dependencies import Input, Output, State
# Dataframe imports
import pandas as pd
file = 'final_buysell_preds.xls' #predictions for arima
#file = input("input the file: ")
df = pd.read_excel(file)

# External CSS for styling
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# app is an Dash instance for HTML layout and app callbacks.
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
app = Dash(__name__)

# Web page wide settings
colors = {
    "graphBackground": "#f8f8f8",
    "background": "#f8f8f8",
    "text": "#505050"
}

# HTML layout
# A file upload is at the top
# a graph is in the middle
# a dynamic table is at the bottom.
app.layout = html.Div(children=[
    dcc.Upload(
        id='upload-data',
        children=html.Div(['Drag and Drop, ', html.A('Select File'), html.Br(), ' To test download and use ', html.A('test file', href="https://github.com/3mr3h/dash_for_heroku/blob/cd3e25ddb08ae436667cee9d442ce111e3397e76/lstm_preds.csv", target="_blank")]),
        style={ 
            'width': '60%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'solid',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=True
    ),
    # Usage details of the dashboard.
    html.Div([
        html.P("Usage: The BASE MODEL PREDICTIONS is fixed, in order to compare and contrast DEEP LEARNING MODEL PREDICTIONS:"),
        html.P("You should;"),
        html.Ul(children=[
            html.Li("Upload the predictions file (csv, xls, txt)"),
            html.Li("Wait for the second scatter graph to populate"),
            html.Li("After two graphs are visible you can compare different predictions.")
        ]),
        html.P("The table at the bottom is dynamic, you can get KKM Interest Return, Comparison Against Inflation Rate, Gain/Loss Amount and Risk Margin according to predicted USD Sell/Buy values.")
    ]),
    html.Div([
        html.Div([
            html.H5('BASE MODEL PREDICTIONS (ARIMA)'),
            dcc.Graph(id='MyArimaGraph', figure={
                                        'data': [
                                            go.Scatter(
                                                x = df['Date'],
                                                y = df['sell']
                                            )
                                        ],
                                        'layout' : go.Layout(
                                            legend={'x':0, 'y':1},
                                            hovermode='closest',
                                            plot_bgcolor=colors["graphBackground"],
                                            paper_bgcolor=colors["graphBackground"]
                                        )
                                        })
        ], className="six columns"),
        
        html.Div([
            html.H5('DEEP LEARNING MODEL PREDICTIONS (LSTM, DeepAR)'),
            dcc.Graph(id='Mygraph')
        ], className="six columns")
        ], className="row"),
    
    html.Div(dash_table.DataTable(
        id='computed-table',
        columns=[
            {'name': 'Capital', 'id': 'capital'},
            {'name': 'KKM Interest GAIN', 'id': 'kkm'},
            {'name': 'Normalized Capital', 'id': 'ncapital'},
            {'name': 'Capital Gain/Loss', 'id': 'gainloss'},
            {'name': 'Potential USD Return', 'id': 'usdret'},
            {'name': 'Capital Gain/Loss Margin', 'id': 'GLmargin'},
            {'name': 'Confidence Level', 'id': 'conf'}
        ],
        data=[{'capital': (i+1)*10000} for i in range(6)],
        editable=True
    )),
])
app.css.append_css({'external_url':'https://codepen.io/chriddyp/pen/bWLwgP.css'})

# Method: parse_data()
# Gets XLS, CSV, TXT files from the user
# Returns a Pandas dataframe
# Parameters:
#   contents - content of the file uploaded
#   filename - name of the file with propoer extension
def parse_data(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV or TXT file
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
        elif 'txt' or 'tsv' in filename:
            # Assume that the user upl, delimiter = r'\s+'oaded an excel file
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), delimiter = r'\s+')
    except Exception as e:
        print(e)
        return html.Div(['There was an error processing this file.'])
    return df

# Dash app callback part for the figure
@app.callback(Output('Mygraph', 'figure'),
            [
                Input('upload-data', 'contents'),
                Input('upload-data', 'filename')
            ])

# Method: update_graph()
# Updates the figure/graph on the web page
# Returns a Plotly graph
# Before returning calls parse_data() method.
# Parameters:
#   contents - content of the file uploaded
#   filename - name of the file with propoer extension
def update_graph(contents, filename):
    fig = {
        'layout': go.Layout(
            plot_bgcolor=colors["graphBackground"],
            paper_bgcolor=colors["graphBackground"])
    }

    if contents:
        contents = contents[0]
        filename = filename[0]
        df = parse_data(contents, filename)
        df = df.set_index(df.columns[0])
        fig = df.iplot(asFigure=True, kind='scatter', mode='lines+markers', size=1)
    return fig

# Dash app callback part for the dynamic table
@app.callback(
    Output('computed-table', 'data'),
    Input('computed-table', 'data_timestamp'),
    State('computed-table', 'data'))

# Method: update_columns()
# Updates each column according the user input on the capital colum in row-wise.
# Returns an updates HTML table.
# in calculations it uses dataframe at the top for std() calculations and USD buy/sell predictions.
# Parameters:
#   timestamps - timestamp
#   rows - rows of the table
def update_columns(timestamp, rows):
    for row in rows:
        kkm = 0.15
        interest = 0.84/4
        usd_volatility = df['buy'].std()
        expected_change = (df.at[274,'buy']-df.at[184,'sell'])/df.at[184,'sell']
        try:
            row['kkm'] = int(float(row['capital']) * (kkm/4+1))
            row['ncapital'] = int(float(row['capital']) * (interest+1))
            row['gainloss'] = int((float(row['capital']) * (kkm/4+1)) - (float(row['capital']) * (interest+1)))
            #row['GLmargin'] = int(((float(row['capital']) * (kkm/4+1)) - (float(row['capital']) * (interest+1))) * usd_volatility *0.05)
            row['usdret'] = int(float(row['capital'])*expected_change)
            row['GLmargin'] = int(float(row['capital'])*usd_volatility*expected_change)
            row['conf'] = '95%: 14.8 - 21.5, 99%: 13.1 - 23.1'
        except:
            row['kkm'] = 'NA'
            row['ncapital'] = 'NA'
            row['gainloss'] = 'NA'
            row['usdret'] = 'NA'
            row['GLmargin'] = 'NA'
            row['conf'] = 'NA'
    return rows

# main starts here :)
if __name__ == '__main__':
    app.run_server(debug=False)