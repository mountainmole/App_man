import osmnx as ox
import pandas as pd
import dash
from dash import html, dcc, Input, Output, dash_table
import folium
from shapely.geometry import Point, Polygon
import plotly.express as px
import plotly.graph_objects as go
import requests

import locale
try:
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
except locale.Error:
    print("Locale setting not supported. Using default locale settings.")


# Define the place you want to get data for
place = 'Al Muneera, Abu Dhabi, United Arab Emirates'

# Get the polygon data for the place
gdf = ox.features_from_place(place, tags={'building': True})

# List of names to keep (from the Excel data for merging)
names_to_keep = [
    'Al Rahba 1', 'Al Rahba 2', 'Al Maha 1 Block A', 'Al Maha 2 Block A'
]

# Filter the GeoDataFrame to keep only the specified names
gdf_filtered = gdf[gdf['name'].isin(names_to_keep)]

# Drop duplicates to keep only distinct names
gdf_filtered = gdf_filtered.drop_duplicates(subset='name')

# Fetch the data from GitHub
url = 'https://raw.githubusercontent.com/mountainmole/App_man/master/data_dict.json'
response = requests.get(url)
data_dict = response.json()

# Convert the data dictionary to a DataFrame
excel_data = pd.DataFrame(data_dict)
excel_data['bill_due_month'] = pd.to_datetime(excel_data['bill_due_month'])

# Filter the data for the months of November and December 2023
filtered_excel_data_dec = excel_data[excel_data['bill_due_month'] == '2023-12-31']
filtered_excel_data_nov = excel_data[excel_data['bill_due_month'] == '2023-11-30']

# Select relevant columns for display
columns_to_display = ['Precinct Name', 'bill_due_month', 'Billed', 'Received', 'Balance', 'Service charge', 'Rent', 'Misc.', 'Units', 'Average Price', 'Active', 'Inactive', 'Rental Yield', 'Contracts expiring', 'Renewal Rate', 'Renewed', 'Expired', 'Units rent delayed', 'Tickets', 'SLA', 'Type Access', 'Type Facilities', 'Type others']
filtered_excel_data_dec = filtered_excel_data_dec[columns_to_display]
filtered_excel_data_nov = filtered_excel_data_nov[columns_to_display]

# Merge the GeoDataFrame with the filtered Excel data for December
merged_gdf_dec = gdf_filtered.merge(filtered_excel_data_dec, how='inner', left_on='name', right_on='Precinct Name')

# Function to format values in UAE Dirhams
def format_currency(value):
    try:
        return locale.currency(value, grouping=True)
    except:
        return value

# Create a folium map
center = merged_gdf_dec.geometry.unary_union.centroid
m = folium.Map(location=[center.y, center.x], zoom_start=17)

# Add the filtered polygon data to the map with clickable polygons
for idx, row in merged_gdf_dec.iterrows():
    tooltip_text = (f"<b>Precinct Name:</b> {row['Precinct Name']}<br>"
                    f"<b>Billed:</b> {round(row['Billed'],1)}<br>"
                    f"<b>Received:</b> {round(row['Received'],1)}<br>"
                    f"<b>Balance:</b> {round(row['Balance'],1)}<br>"
                    f"<b>Units:</b> {round(row['Units'], 1)}<br>"
                    f"<b>Average Price:</b> {round(row['Average Price'],1)}<br>"
                    f"<b>Active:</b> {round(row['Active'], 1)}<br>"
                    f"<b>Inactive:</b> {round(row['Inactive'], 1)}<br>"
                    f"<b>Rental Yield:</b> {row['Rental Yield']*100:.2f}%")
    folium.GeoJson(row.geometry, tooltip=tooltip_text).add_to(m)

# Save the map to an HTML file
m.save('al_muneera_filtered_map.html')

# Read HTML file and encode it to base64
with open('al_muneera_filtered_map.html', 'r') as f:
    html_content = f.read()

# Calculate summary metrics for the table for December
summary_metrics_dec = filtered_excel_data_dec.agg({
    'Billed': 'sum',
    'Received': 'sum',
    'Balance': 'sum',
    'Units': 'sum',
    'Average Price': 'mean',
    'Active': 'sum',
    'Inactive': 'sum',
    'Rental Yield': 'mean',
    'Contracts expiring': 'sum',
    'Renewal Rate': 'mean',
    'Renewed': 'sum',
    'Expired': 'sum',
    'Units rent delayed': 'sum',
    'Tickets': 'sum',
    'SLA': 'mean',
    'Type Access': 'mean',
    'Type Facilities': 'mean',
    'Type others': 'mean'
}).reset_index()
summary_metrics_dec.columns = ['Metric', 'December Value']

# Calculate summary metrics for the table for November
summary_metrics_nov = filtered_excel_data_nov.agg({
    'Billed': 'sum',
    'Received': 'sum',
    'Balance': 'sum',
    'Units': 'sum',
    'Average Price': 'mean',
    'Active': 'sum',
    'Inactive': 'sum',
    'Rental Yield': 'mean',
    'Contracts expiring': 'sum',
    'Renewal Rate': 'mean',
    'Renewed': 'sum',
    'Expired': 'sum',
    'Units rent delayed': 'sum',
    'Tickets': 'sum',
    'SLA': 'mean',
    'Type Access': 'mean',
    'Type Facilities': 'mean',
    'Type others': 'mean'
}).reset_index()
summary_metrics_nov.columns = ['Metric', 'November Value']

# Merge the summary metrics for both months
summary_metrics = pd.merge(summary_metrics_dec, summary_metrics_nov, on='Metric')
summary_metrics['Variance'] = summary_metrics.apply(
    lambda row: round(float(row['December Value']) - float(row['November Value']), 2) if isinstance(row['December Value'], (int, float)) and isinstance(row['November Value'], (int, float)) else "N/A",
    axis=1
)

# Apply conditional formatting for color coding
def determine_background_color(metric, variance):
    positive_metrics = ['Billed', 'Received', 'Balance', 'Active', 'Rental Yield', 'Renewal Rate', 'Renewed', 'SLA', 'Type Access', 'Type Facilities', 'Type others']
    negative_metrics = ['Contracts expiring', 'Expired', 'Units rent delayed', 'Tickets', 'Inactive']
    if variance == "N/A":
        return ''
    elif metric in positive_metrics:
        return 'background-color: green;' if variance > 0 else 'background-color: yellow;'
    elif metric in negative_metrics:
        return 'background-color: green;' if variance < 0 else 'background-color: yellow;'
    return ''

# Function to format values in UAE Dirhams
def format_currency(value):
    try:
        return locale.currency(value, grouping=True)
    except:
        return value

# Format columns for currency and percentage
summary_metrics['December Value'] = summary_metrics.apply(
    lambda row: format_currency(row['December Value']) if row['Metric'] not in ['Units', 'Rental Yield', 'Renewal Rate', 'SLA', 'Type Access', 'Type Facilities', 'Type others', 'Active', 'Inactive', 'Contracts expiring', 'Renewed', 'Expired', 'Units rent delayed', 'Tickets'] else f"{round(row['December Value'] * 100, 2)}%" if row['Metric'] in ['Rental Yield', 'Renewal Rate', 'SLA', 'Type Access', 'Type Facilities', 'Type others'] else round(row['December Value'], 2),
    axis=1
)
summary_metrics['November Value'] = summary_metrics.apply(
    lambda row: format_currency(row['November Value']) if row['Metric'] not in ['Units', 'Rental Yield', 'Renewal Rate', 'SLA', 'Type Access', 'Type Facilities', 'Type others', 'Active', 'Inactive', 'Contracts expiring', 'Renewed', 'Expired', 'Units rent delayed', 'Tickets'] else f"{round(row['November Value'] * 100, 2)}%" if row['Metric'] in ['Rental Yield', 'Renewal Rate', 'SLA', 'Type Access', 'Type Facilities', 'Type others'] else round(row['November Value'], 2),
    axis=1
)

# Create the Dash app
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Al Muneera Details"),
    html.Div([
        html.Iframe(id='map', srcDoc=html_content, width='50%', height='400'),
        dash_table.DataTable(
            id='summary-table',
            columns=[{"name": i, "id": i} for i in summary_metrics.columns],
            data=summary_metrics.to_dict('records'),
            style_table={'width': '50%'},
            style_cell={
                'textAlign': 'left',
                'padding': '5px',
                'fontFamily': 'Arial',
                'fontSize': '15px'
            },
            style_header={
                'backgroundColor': 'lightgrey',
                'fontWeight': 'bold'
            },
            style_data_conditional=[
                {
                    'if': {'filter_query': '{Metric} = "Billed" && {Variance} > 0', 'column_id': 'Variance'},
                    'backgroundColor': 'green'
                },
                {
                    'if': {'filter_query': '{Metric} = "Billed" && {Variance} <= 0', 'column_id': 'Variance'},
                    'backgroundColor': 'yellow'
                },
                {
                    'if': {'filter_query': '{Metric} = "Received" && {Variance} > 0', 'column_id': 'Variance'},
                    'backgroundColor': 'green'
                },
                {
                    'if': {'filter_query': '{Metric} = "Received" && {Variance} <= 0', 'column_id': 'Variance'},
                    'backgroundColor': 'yellow'
                },
                {
                    'if': {'filter_query': '{Metric} = "Balance" && {Variance} > 0', 'column_id': 'Variance'},
                    'backgroundColor': 'green'
                },
                {
                    'if': {'filter_query': '{Metric} = "Balance" && {Variance} <= 0', 'column_id': 'Variance'},
                    'backgroundColor': 'yellow'
                },
                {
                    'if': {'filter_query': '{Metric} = "Active" && {Variance} > 0', 'column_id': 'Variance'},
                    'backgroundColor': 'green'
                },
                {
                    'if': {'filter_query': '{Metric} = "Active" && {Variance} <= 0', 'column_id': 'Variance'},
                    'backgroundColor': 'yellow'
                },
                {
                    'if': {'filter_query': '{Metric} = "Inactive" && {Variance} > 0', 'column_id': 'Variance'},
                    'backgroundColor': 'yellow'
                },
                {
                    'if': {'filter_query': '{Metric} = "Inactive" && {Variance} <= 0', 'column_id': 'Variance'},
                    'backgroundColor': 'green'
                },
                {
                    'if': {'filter_query': '{Metric} = "Rental Yield" && {Variance} > 0', 'column_id': 'Variance'},
                    'backgroundColor': 'green'
                },
                {
                    'if': {'filter_query': '{Metric} = "Rental Yield" && {Variance} <= 0', 'column_id': 'Variance'},
                    'backgroundColor': 'yellow'
                },
                {
                    'if': {'filter_query': '{Metric} = "Contracts expiring" && {Variance} > 0', 'column_id': 'Variance'},
                    'backgroundColor': 'yellow'
                },
                {
                    'if': {'filter_query': '{Metric} = "Contracts expiring" && {Variance} <= 0', 'column_id': 'Variance'},
                    'backgroundColor': 'green'
                },
                {
                    'if': {'filter_query': '{Metric} = "Renewal Rate" && {Variance} > 0', 'column_id': 'Variance'},
                    'backgroundColor': 'green'
                },
                {
                    'if': {'filter_query': '{Metric} = "Renewal Rate" && {Variance} <= 0', 'column_id': 'Variance'},
                    'backgroundColor': 'yellow'
                },
                {
                    'if': {'filter_query': '{Metric} = "Renewed" && {Variance} > 0', 'column_id': 'Variance'},
                    'backgroundColor': 'green'
                },
                {
                    'if': {'filter_query': '{Metric} = "Renewed" && {Variance} <= 0', 'column_id': 'Variance'},
                    'backgroundColor': 'yellow'
                },
                {
                    'if': {'filter_query': '{Metric} = "Expired" && {Variance} > 0', 'column_id': 'Variance'},
                    'backgroundColor': 'yellow'
                },
                {
                    'if': {'filter_query': '{Metric} = "Expired" && {Variance} <= 0', 'column_id': 'Variance'},
                    'backgroundColor': 'green'
                },
                {
                    'if': {'filter_query': '{Metric} = "Units rent delayed" && {Variance} > 0', 'column_id': 'Variance'},
                    'backgroundColor': 'yellow'
                },
                {
                    'if': {'filter_query': '{Metric} = "Units rent delayed" && {Variance} <= 0', 'column_id': 'Variance'},
                    'backgroundColor': 'green'
                },
                {
                    'if': {'filter_query': '{Metric} = "Tickets" && {Variance} > 0', 'column_id': 'Variance'},
                    'backgroundColor': 'yellow'
                },
                {
                    'if': {'filter_query': '{Metric} = "Tickets" && {Variance} <= 0', 'column_id': 'Variance'},
                    'backgroundColor': 'green'
                },
                {
                    'if': {'filter_query': '{Metric} = "SLA" && {Variance} > 0', 'column_id': 'Variance'},
                    'backgroundColor': 'green'
                },
                {
                    'if': {'filter_query': '{Metric} = "SLA" && {Variance} <= 0', 'column_id': 'Variance'},
                    'backgroundColor': 'yellow'
                },
                {
                    'if': {'filter_query': '{Metric} = "Type Access" && {Variance} > 0', 'column_id': 'Variance'},
                    'backgroundColor': 'green'
                },
                {
                    'if': {'filter_query': '{Metric} = "Type Access" && {Variance} <= 0', 'column_id': 'Variance'},
                    'backgroundColor': 'yellow'
                },
                {
                    'if': {'filter_query': '{Metric} = "Type Facilities" && {Variance} > 0', 'column_id': 'Variance'},
                    'backgroundColor': 'green'
                },
                {
                    'if': {'filter_query': '{Metric} = "Type Facilities" && {Variance} <= 0', 'column_id': 'Variance'},
                    'backgroundColor': 'yellow'
                },
                {
                    'if': {'filter_query': '{Metric} = "Type others" && {Variance} > 0', 'column_id': 'Variance'},
                    'backgroundColor': 'green'
                },
                {
                    'if': {'filter_query': '{Metric} = "Type others" && {Variance} <= 0', 'column_id': 'Variance'},
                    'backgroundColor': 'yellow'
                },
            ]
        )
    ], style={'display': 'flex'}),
    html.Label("Select Precinct:"),
    dcc.Dropdown(
        id='precinct-dropdown',
        options=[{'label': name, 'value': name} for name in names_to_keep],
        value=names_to_keep[0]
    ),
    html.Div([
        dcc.Graph(id='combined-chart', style={'display': 'inline-block', 'width': '48%'}),
        dcc.Graph(id='additional-metrics-chart', style={'display': 'inline-block', 'width': '48%'})
    ]),
    html.Div([
        dcc.Graph(id='contract-metrics-chart', style={'display': 'inline-block', 'width': '48%'}),
        dcc.Graph(id='sla-chart', style={'display': 'inline-block', 'width': '48%'})  # New chart for Tickets and SLA metrics
    ])
])

# Define the callback to update the charts based on selected precinct
@app.callback(
    [Output('combined-chart', 'figure'),
     Output('additional-metrics-chart', 'figure'),
     Output('contract-metrics-chart', 'figure'),
     Output('sla-chart', 'figure')],
    [Input('precinct-dropdown', 'value')]
)
def update_charts(selected_precinct):
    if selected_precinct:
        data = excel_data[excel_data['Precinct Name'] == selected_precinct]
        data = data.sort_values(by='bill_due_month')
        
        # Melt the dataframe to have Billed, Received, and Balance in one column
        melted_data = data.melt(id_vars=['bill_due_month'], value_vars=['Billed', 'Received', 'Balance'], 
                                var_name='Type', value_name='Amount')
        
        # Create a bar chart with multiple bars
        combined_fig = go.Figure()

        for metric in ['Billed', 'Received', 'Balance']:
            combined_fig.add_trace(
                go.Bar(x=melted_data[melted_data['Type'] == metric]['bill_due_month'],
                       y=melted_data[melted_data['Type'] == metric]['Amount'],
                       name=metric)
            )

        # Add Rental Yield as a line on the secondary y-axis
        combined_fig.add_trace(
            go.Scatter(x=data['bill_due_month'],
                       y=data['Rental Yield'] * 100,
                       name='Rental Yield (%)',
                       yaxis='y2',
                       mode='lines+markers')
        )

        # Update layout for dual y-axis
        combined_fig.update_layout(
            title='Billed, Received, Balance, and Rental Yield Over Time',
            xaxis=dict(title='Bill Due Month'),
            yaxis=dict(title='Amount'),
            yaxis2=dict(title='Rental Yield (%)', overlaying='y', side='right', tickformat='.2f')
        )
        
        # Calculate additional metrics
        data['Service charge collected'] = data['Billed'] * data['Service charge']
        data['Rent collected'] = data['Billed'] * data['Rent']
        data['Misc Expenses collected'] = data['Billed'] * data['Misc.']
        
        # Melt the dataframe for additional metrics
        additional_melted_data = data.melt(id_vars=['bill_due_month'], 
                                           value_vars=['Service charge collected', 'Rent collected', 'Misc Expenses collected'],
                                           var_name='Metric', value_name='Collected Amount')
        
        # Create a bar chart for additional metrics
        additional_fig = px.bar(additional_melted_data, x='bill_due_month', y='Collected Amount', color='Metric', barmode='group',
                                title='Service Charge, Rent, and Misc Expenses Collected Over Time')
        
        # Melt the dataframe for contract metrics
        contract_melted_data = data.melt(id_vars=['bill_due_month'], 
                                         value_vars=['Contracts expiring', 'Renewal Rate', 'Renewed', 'Expired', 'Units rent delayed'],
                                         var_name='Metric', value_name='Count')
        
        # Create a bar chart for contract metrics and add Renewal Rate as a line on the secondary axis
        contract_fig = go.Figure()

        for metric in ['Contracts expiring', 'Renewed', 'Expired', 'Units rent delayed']:
            contract_fig.add_trace(
                go.Bar(x=contract_melted_data[contract_melted_data['Metric'] == metric]['bill_due_month'],
                       y=contract_melted_data[contract_melted_data['Metric'] == metric]['Count'],
                       name=metric)
            )

        # Add Renewal Rate as a line on the secondary y-axis
        contract_fig.add_trace(
            go.Scatter(x=contract_melted_data[contract_melted_data['Metric'] == 'Renewal Rate']['bill_due_month'],
                       y=contract_melted_data[contract_melted_data['Metric'] == 'Renewal Rate']['Count'] * 100,
                       name='Renewal Rate (%)',
                       yaxis='y2',
                       mode='lines+markers')
        )

        # Update layout for dual y-axis
        contract_fig.update_layout(
            title='Contract Metrics Over Time',
            xaxis=dict(title='Bill Due Month'),
            yaxis=dict(title='Count'),
            yaxis2=dict(title='Renewal Rate (%)', overlaying='y', side='right', tickformat='.2f')
        )
        
        # Melt the dataframe for SLA metrics
        sla_melted_data = data.melt(id_vars=['bill_due_month'], 
                                    value_vars=['Tickets', 'SLA', 'Type Access', 'Type Facilities', 'Type others'],
                                    var_name='Metric', value_name='Percentage')

        # Create a bar chart for SLA metrics with stacked percentages
        sla_fig = go.Figure()

        # Add Tickets as a line on primary y-axis
        sla_fig.add_trace(
            go.Scatter(x=sla_melted_data[sla_melted_data['Metric'] == 'Tickets']['bill_due_month'],
                       y=sla_melted_data[sla_melted_data['Metric'] == 'Tickets']['Percentage'],
                       name='Tickets',
                       mode='lines+markers')
        )

        # Add SLA as a line on secondary y-axis
        sla_fig.add_trace(
            go.Scatter(x=sla_melted_data[sla_melted_data['Metric'] == 'SLA']['bill_due_month'],
                       y=sla_melted_data[sla_melted_data['Metric'] == 'SLA']['Percentage'] * 100,
                       name='SLA (%)',
                       yaxis='y2',
                       mode='lines+markers')
        )

        # Add Type Access, Type Facilities, and Type others as stacked bars on secondary y-axis
        for metric in ['Type Access', 'Type Facilities', 'Type others']:
            sla_fig.add_trace(
                go.Bar(x=sla_melted_data[sla_melted_data['Metric'] == metric]['bill_due_month'],
                       y=sla_melted_data[sla_melted_data['Metric'] == metric]['Percentage'] * 100,
                       name=metric,
                       yaxis='y2')
            )

        # Update layout for dual y-axis and stacked bars
        sla_fig.update_layout(
            title='Tickets and SLA Metrics Over Time',
            xaxis=dict(title='Bill Due Month'),
            yaxis=dict(title='Tickets Count'),
            yaxis2=dict(title='Percentage (%)', overlaying='y', side='right', tickformat='.2%'),
            barmode='stack'
        )
        
        return combined_fig, additional_fig, contract_fig, sla_fig
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)

