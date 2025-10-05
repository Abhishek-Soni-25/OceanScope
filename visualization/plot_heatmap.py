import seaborn as sns
import matplotlib.pyplot as plt

def plot_correlation_heatmap(df):
    numeric_df = df.select_dtypes(include=['number'])
    corr = numeric_df.corr()

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", ax=ax)
    ax.set_title("Feature Correlation Heatmap")
    return fig
