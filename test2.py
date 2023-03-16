import pandas as pd
from pandas.core.tools.datetimes import to_datetime
import plotly.graph_objs as go
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import numpy as np
import base64
import datetime
from datetime import timedelta
import time

# Read and preprocess the data
def load_data():
    df = pd.read_csv("/home/ec2-user/project/myfile4.csv", header=None, names=["date", "prix"])
    df['prix'] = df['prix'].str.replace('$', '').astype(float)
    df['date'] = pd.to_datetime(df['date'], format='%d/%m/%y-%H:%M:%S')

    df18h = pd.read_csv("/home/ec2-user/project/last.csv", header=None, names=["date", "prix"])

    image_filename = '/home/ec2-user/project/Sandbox-SAND-logo.png'
    encoded_image = base64.b64encode(open(image_filename, 'rb').read()).decode('ascii')
    
    return df, df18h, encoded_image

# Create the application layout
def create_layout(encoded_image):
    layout = html.Div([
        html.Center(
            html.Img(src='data:image/png;base64,{}'.format(encoded_image), style={'width': '550px'})
        ),
        create_datepicker(),
        create_hour_range_slider(),
        create_dashboard_elements(),
    ], style={'width':'100%', 'padding': 0, 'height': '100vh', 'width': '100vw', 'background-color':'white'})

    return layout

# Create date picker
def create_datepicker():
    return html.Div([
        dcc.DatePickerRange(id='date-range',
                            min_date_allowed=df['date'].min(),
                            max_date_allowed=df['date'].max(),
                            start_date=df['date'].min(),
                            end_date=df['date'].max())
    ], style={'margin': '10px 80px'})

# Create hour range slider
def create_hour_range_slider():
    return html.Div([
        dcc.RangeSlider(
            id='hour-range',
            min=df['date'].dt.hour.min(),
            max=df['date'].dt.hour.max(),
            step=1,
            value=[df['date'].dt.hour.min(), df['date'].dt.hour.max()],
            marks={hour: f"{hour}h" for hour in range(df['date'].dt.hour.min(), df['date'].dt.hour.max() + 1)}
        )
    ], style={'margin': '0 70px'})

# Create dashboard elements
def create_dashboard_elements():
    return html.Div([
        html.Div([
            dcc.Graph(id='graph', style={'height': '650px', 'width': '60vw', 'display': 'inline-block', 'vertical-align': 'middle', 'text-align': 'center'}),
        ]),
        html.Div([
            create_stats_container(),
            create_stats24h_container(),
            create_actual_price_container()
        ], style={'display': 'flex', 'align-items': 'center', 'margin': '30px 80px'}),
    ], style={'width': '100%', 'height': '100vh', 'padding': 0, 'background-color': 'white'})

# Create stats container
def create_stats_container():
    return html.Div([
        html.H2("Statistiques de la Plage selectionnée ", style={'font-weight': 'bold', 'font-family': 'Calibri', 'font-weight':'normal', 'margin': '0', 'color': '#1f77b4'}),
        html.Div(id='stats')],
        style={'font-size': '120%', 'width': '33%', 'display': 'inline-block', 'text-align': 'center',
               'border-bottom': '1px solid black', 'padding': '10px', 'height': '450px'})

# Create stats24h container
def create_stats24h_container():
    return html.Div([
        html.H2("Statistiques de la journée (maj à 18h)", style={'font-weight': 'bold', 'font-family': 'Calibri', 'font-weight': 'normal', 'color': '#1f77b4'}),
        html.Div(id='stats24h')],
        style={'font-size': '120%', 'width': '33%', 'display': 'inline-block', 'text-align': 'center',
               'border-left': '1px solid black', 'border-bottom': '1px solid black', 'padding': '10px', 'height': '450px'})

# Create actual price container
def create_actual_price_container():
    return html.Div([
        html.H2("Prix Actuel", style={'font-weight': 'bold', 'font-family': 'Calibri', 'font-weight': 'normal', 'color': '#1f77b4'}),
        html.Div(id='Actual_price')],
        style={'font-size': '120%', 'width': '33%', 'display': 'inline-block', 'text-align': 'center', 'padding': '10px', 'height': '450px',
               'border-left': '1px solid black', 'border-bottom': '1px solid black'})



# Initialize the app
df, df18h, encoded_image = load_data()
app = dash.Dash(__name__)
app.layout = create_layout(encoded_image)

@app.callback(
    [Output('graph', 'figure'),
     Output('stats', 'children'),
     Output('stats24h', 'children'),
     Output('Actual_price', 'children')],
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('hour-range', 'value'),
     ])
# Main function to update data
def update_data(start_date, end_date, hour_range):
    # Vérifier si la plage de dates a été sélectionnée
    if start_date is not None and end_date is not None:
        # Filtrer les données en fonction de la plage de dates sélectionnée
        end = pd.to_datetime(end_date)
        filtered_data = df.loc[
        (df['date'] >= pd.to_datetime(start_date) + pd.Timedelta(hours=hour_range[0])) &
        (df['date'] <= pd.Timestamp(end.date()) + pd.Timedelta(hours= hour_range[1]))
        ]

        # Créer le graphique
        fig = {
            'data': [{
                'x': filtered_data['date'],
                'y': filtered_data['prix'],
                'type': 'line'
            }],
            'layout': {
                'title': 'Graph du Sandbox (mis à jour toutes les 5 minutes)',
                'xaxis': {'title': 'Date (UTC)'},
                'yaxis': {'title': 'Prix en $'}
            }
        }



        # Calculer la standard deviation
        var= 100*(filtered_data['prix'].iloc[-1]-filtered_data['prix'].iloc[0])/filtered_data['prix'].iloc[0]
        max_val = filtered_data['prix'].max()
        min_val = filtered_data['prix'].min()
        std = filtered_data['prix'].std()
        # Mettre à jour les statistiques
        stats = html.Div([
        html.P([f"Variation de prix: ", html.Span(f"{round(var,2)} %", style ={'color': 'red' if var < 0 else 'green'})], style={"color": "black"}),
        html.P(f"Maximum: {max_val} $"),
        html.P(f"Minimum: {min_val} $"),
        html.P(f"Volatilité: {round(std,5)}")
        ], style={'marginTop':'50px'})

    else:
        # Si aucune plage de dates n'a été sélectionnée, utiliser toutes les données
        fig = {
            'data': [{
                'x': df['date'],
                'y': df['prix'],
                'type': 'line'
            }],
            'layout': {
                'title': 'Graph du Sandbox (mis à jour toutes les 5 minutes)',
                'xaxis': {'title': 'Date (UTC)'},
                'yaxis': {'title': 'Prix en $'}
            }
        }

        # Calculer la standard deviation pour toutes les données
        var= 100*(df['prix'].iloc[-1]-df['prix'].iloc[0])/df['prix'].iloc[0]
        std = df['prix'].std()
        max_val = df['prix'].max()
        min_val = df['prix'].min()
        # Mettre à jour les statistiques
        stats = html.Div([
            html.P([f"Variation de prix: ", html.Span(f"{round(var,2)} %", style ={'color': 'red' if var < 0 else 'green'})], style={"color": "black"}),
        html.P(f"Maximum: {max_val} $"),
        html.P(f"Minimum: {min_val} $"),
        html.P(f"Volatilité: {round(std,5)}")
        ], style={'marginTop':'50px'})
    var18h=   100*(df18h['prix'].iloc[-1]-df18h['prix'].iloc[0])/df18h['prix'].iloc[0]

    # Calculer la standard deviation pour toutes les données

    max_val18h=df18h['prix'].max()
    min_val18h = df18h['prix'].min()
    std18h = df18h['prix'].std()

    # Mettre à jour les statistiques
    stats24h = html.Div([
        html.P([f"Variation de prix: ", html.Span(f"{round(var18h,2)} %", style ={'color': 'red' if var18h < 0 else 'green'})], style={"color": "black"}),
        html.P(f"Maximum: {max_val18h} $"),
        html.P(f"Minimum: {min_val18h} $"),
        html.P(f"Volatilité: {round(std18h,5)}")

        ], style={'marginTop':'50px'})
    Actual_price=html.P(f"{df['prix'].iloc[-1]} $")
    return fig, stats, stats24h, Actual_price
# Run the server
if __name__ == '__main__':
    app.run_server( port=8050, debug=True)
