import matplotlib.pyplot as plt
import seaborn as sns

def plot_vertical_profiles(df):
    fig, axes = plt.subplots(1, 2, figsize=(12, 6))

    sns.lineplot(ax=axes[0], data=df, x="temp", y="pres", color="r")
    axes[0].invert_yaxis()
    axes[0].set_title("Temperature Profile")
    axes[0].set_xlabel("Temperature (°C)")
    axes[0].set_ylabel("Pressure (Depth)")

    sns.lineplot(ax=axes[1], data=df, x="psal", y="pres", color="b")
    axes[1].invert_yaxis()
    axes[1].set_title("Salinity Profile")
    axes[1].set_xlabel("Salinity (PSU)")
    axes[1].set_ylabel("Pressure (Depth)")

    plt.tight_layout()
    return fig
