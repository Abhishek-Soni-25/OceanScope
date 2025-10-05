import plotly.express as px

def plot_time_series(df):
    fig_temp = px.line(df, x="juld", y="temp", title="Temperature over Time", color="platform_number")
    fig_psal = px.line(df, x="juld", y="psal", title="Salinity over Time", color="platform_number")
    return fig_temp, fig_psal
