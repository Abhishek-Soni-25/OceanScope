import plotly.express as px

def plot_float_path(df):
    fig = px.scatter_geo(
        df,
        lat="latitude",
        lon="longitude",
        color="platform_number",
        title="Float Path Map",
        projection="natural earth",
        hover_name="platform_number",
    )
    fig.update_traces(marker=dict(size=6))
    return fig
