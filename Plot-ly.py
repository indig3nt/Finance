from dash import html, dcc, Output, Input, Dash, State
import sqlite3
import time
import math
import dash_bootstrap_components as dbc


colors = {

    'background': 'black',
    'text': '#7FDBFF'
}


frequency = 200

fig = dict(data = [{'x': [], 'y': [], 'line': dict(color='blue', width=3)}],
           layout = dict(
               title = dict(text="Trade Volume Over (Current) Time (ms)", font=dict(size=15, color = "grey")),
               xaxis = dict(title = "Time", range=(-1,1), autorange = True, visible = False),
               yaxis = dict(title = "Volume", range=(0,10000), autorange = True, color = "white"),
               paper_bgcolor="black",
               plot_bgcolor="black",
               margin = dict(l=70, r=70, t=70),
               autosize = True,
           ))

app = Dash(external_stylesheets=[dbc.themes.COSMO])
app.layout = html.Div(style={'backgroundColor': colors['background']}, children=[
    html.H1(
        id = "price-ticker",
        style={"text-align": "center", 'color': 'white', "padding-top": "100px", 'padding-bottom': '70px'}  
    ),
    dcc.Graph(id = "graph", figure = fig),
    dcc.Interval(id = "update", interval = frequency),
    ]
)

@app.callback(

    Output("graph", "extendData"), # Updates the H1 text    
    Output("price-ticker", "children"), 
    Input("update", "n_intervals") # Triggered by the dcc.Interval component
)

def update_data(intervals):

    connection = sqlite3.connect("./data.db")
    cursor = connection.cursor()


    time_from = math.floor((time.time() - 60) *1000)
    data = cursor.execute(
            f"SELECT * FROM trades WHERE time > {time_from} ORDER BY TIME DESC").fetchall()

    current_price = data[0][3]
    total_trades = len(data)
    print(total_trades)
    print(current_price)

    return ({'x': [[time.time()]], 'y': [[total_trades]]}, [0], 100), current_price

if __name__ == "__main__":
    app.run_server(debug=True)