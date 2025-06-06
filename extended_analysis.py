import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import numpy as np

def perform_extended_analysis(csv_filepath='daily_word_counts.csv'):
    """
    Loads the daily word count data and performs extended statistical analysis.
    """
    try:
        df = pd.read_csv(csv_filepath)
    except FileNotFoundError:
        print(f"Error: The file '{csv_filepath}' was not found.")
        print("Please run your main script first to generate the CSV file.")
        return

    print("--- Extended Statistical Analysis ---")

    # --- 1. Time Series Analysis: Rolling Average ---
    # This smooths out daily variations to show longer-term trends in reading load.
    df['Rolling_7_Day_Avg'] = df['WordCount'].rolling(window=7, center=True).mean()
    
    plt.figure(figsize=(15, 7))
    plt.plot(df['WordCount'], label='Daily Word Count', alpha=0.5, marker='.', linestyle='none')
    plt.plot(df['Rolling_7_Day_Avg'], label='7-Day Rolling Average', color='firebrick', linewidth=2)
    plt.title('Daily Word Counts and 7-Day Rolling Average')
    plt.xlabel('Day of the Year (Index)')
    plt.ylabel('Number of Words')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.savefig('rolling_average_plot.png')
    print("\n[+] A plot showing the 7-day rolling average has been saved to 'rolling_average_plot.png'")
    plt.show()

    # --- 2. Monthly Reading Load Analysis ---
    # We create a proper date to extract month names for grouping.
    # We'll assume a non-leap year; the specific year doesn't matter for this analysis.
    df['Date'] = pd.to_datetime('2025' + df['Day'].astype(str).str.zfill(4), format='%Y%m%d')
    df['Month'] = df['Date'].dt.month_name()
    
    month_order = ['January', 'February', 'March', 'April', 'May', 'June', 
                   'July', 'August', 'September', 'October', 'November', 'December']
    
    plt.figure(figsize=(15, 8))
    sns.boxplot(x='Month', y='WordCount', data=df, order=month_order, palette="viridis")
    plt.title('Distribution of Daily Reading Word Counts by Month')
    plt.xlabel('Month')
    plt.ylabel('Daily Word Count')
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig('monthly_word_count_boxplot.png')
    print("\n[+] A boxplot showing word count distributions per month has been saved as 'monthly_word_count_boxplot.png'")
    plt.show()

    # --- 3. Distribution and Normality Test ---
    # This formally tests if the word count distribution is "normal" (a bell curve).
    k2, p = stats.normaltest(df['WordCount'])
    print("\n--- Normality Test (D'Agostino's K^2) ---")
    print(f"P-value: {p:.4f}")
    if p < 0.05:
        print("The p-value is less than 0.05, so we reject the null hypothesis.")
        print("Conclusion: The data is likely NOT normally distributed.")
    else:
        print("The p-value is greater than 0.05, so we cannot reject the null hypothesis.")
        print("Conclusion: The data could be normally distributed.")

    # --- 4. Outlier Detection ---
    # This identifies days with an unusually high or low number of words to read.
    Q1 = df['WordCount'].quantile(0.25)
    Q3 = df['WordCount'].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    outliers = df[(df['WordCount'] < lower_bound) | (df['WordCount'] > upper_bound)]
    print("\n--- Outlier Detection (using 1.5*IQR method) ---")
    print(f"Days with reading counts outside the range ({lower_bound:.0f} to {upper_bound:.0f} words):")
    if not outliers.empty:
        # Sort by word count to see the most extreme outliers first
        print(outliers[['Day', 'WordCount']].sort_values(by='WordCount', ascending=False).to_string(index=False))
    else:
        print("No significant outliers found.")

def gini(x):
    """Calculates the Gini coefficient of a numpy array."""
    # Requires a sorted array
    x = np.asarray(x)
    sorted_x = np.sort(x)
    n = len(x)
    if n == 0 or np.sum(sorted_x) == 0:
        return 0 # Gini is 0 for empty or all-zero lists
    # Gini coefficient calculation
    index = np.arange(1, n + 1)
    return (np.sum((2 * index - n - 1) * sorted_x)) / (n * np.sum(sorted_x))

def perform_advanced_analysis(csv_filepath='daily_word_counts.csv'):
    """
    Loads the daily word count data and performs advanced analysis,
    including Gini coefficient and a "Reading Challenge Score".
    """
    try:
        df = pd.read_csv(csv_filepath)
    except FileNotFoundError:
        print(f"Error: The file '{csv_filepath}' was not found.")
        print("Please run your main script first to generate the CSV file.")
        return

    print("--- Advanced Statistical Analysis ---")

    # --- Setup: Create Date-based columns ---
    # Assume a non-leap year. The year itself is arbitrary.
    df['Date'] = pd.to_datetime('2025' + df['Day'].astype(str).str.zfill(4), format='%Y%m%d')
    df['Month'] = df['Date'].dt.month_name()
    df = df.sort_values(by='Date').reset_index(drop=True)
    month_order = ['January', 'February', 'March', 'April', 'May', 'June', 
                   'July', 'August', 'September', 'October', 'November', 'December']

    # --- 1. Gini Coefficient by Month (Reading Load Inequality) ---
    monthly_gini = df.groupby('Month')['WordCount'].apply(gini).loc[month_order]
    
    plt.figure(figsize=(12, 6))
    monthly_gini.plot(kind='bar', color=sns.color_palette("plasma", 12))
    plt.title('Monthly Reading Load "Inequality" (Gini Coefficient)')
    plt.xlabel('Month')
    plt.ylabel('Gini Coefficient')
    plt.xticks(rotation=45)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('monthly_gini_plot.png')
    print("\n[+] A plot of the monthly Gini coefficient has been saved to 'monthly_gini_plot.png'")
    plt.show()
    print("Interpretation: A higher bar means the daily word counts within that month are more unequal.")


    # --- 2. Reading Challenge Score (Potential "Drop-off" Periods) ---
    window = 14 # Use a 14-day window to assess difficulty
    
    # Calculate rolling volume (mean) and volatility (standard deviation)
    df['Volume'] = df['WordCount'].rolling(window=window, center=True).mean()
    df['Volatility'] = df['WordCount'].rolling(window=window, center=True).std()
    
    # Normalize by the overall mean/std to create a comparable score
    df['Challenge_Score'] = (df['Volume'] / df['WordCount'].mean()) + (df['Volatility'] / df['WordCount'].std())

    fig, ax = plt.subplots(figsize=(15, 7))
    ax.plot(df['Date'], df['Challenge_Score'], color='darkred', label='Reading Challenge Score')
    ax.set_title(f'{window}-Day Reading Challenge Score Over the Year')
    ax.set_xlabel('Date')
    ax.set_ylabel('Challenge Score (Volume + Volatility)')
    ax.legend()
    # Fill the area under the curve to highlight challenging periods
    ax.fill_between(df['Date'], 0, df['Challenge_Score'], color='darkred', alpha=0.2)
    ax.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig('reading_challenge_score.png')
    print("\n[+] A plot of the 'Reading Challenge Score' has been saved to 'reading_challenge_score.png'")
    plt.show()

    # Identify the most challenging period
    most_challenging_date = df.loc[df['Challenge_Score'].idxmax()]['Date']
    print("--- Most Challenging Periods ---")
    print("The Reading Challenge score combines both high volume and high day-to-day volatility.")
    print(f"The peak challenge score occurs around: {most_challenging_date.strftime('%B %d')}.")
    
    # Get the top 3 most challenging weeks
    df['Week'] = df['Date'].dt.isocalendar().week
    weekly_challenge = df.groupby('Week')['Challenge_Score'].mean().nlargest(3)
    print("\nTop 3 most challenging weeks (by average score):")
    print(weekly_challenge)


if __name__ == '__main__':
    perform_extended_analysis()
    perform_advanced_analysis()