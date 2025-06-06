## Summary Statistics for Daily Word Counts

|Stat|Result|
|-|-|
|count|     365.000000|
|mean|     2781.498630|
|std |      551.987725|
|min |     1616.000000|
|25% |     2366.000000|
|50% |     2743.000000|
|75% |     3146.000000|
|max |     4640.000000|

- A boxplot showing word count distributions per month has been saved as 'monthly_word_count_boxplot.png'

### Normality Test (D'Agostino's K^2)
P-value: 0.0024
The p-value is less than 0.05, so we reject the null hypothesis.
Conclusion: The data is likely NOT normally distributed.

### Outlier Detection (using 1.5*IQR method)
Days with reading counts outside the range (1196 to 4316 words):
| Day | WordCount|
|-|-|
| 726 |      4640|
| 123 |      4555|
|1005 |     4376|

## Advanced Statistical Analysis

- A plot of the monthly Gini coefficient has been saved to 'monthly_gini_plot.png'
**Interpretation: A higher bar means the daily word counts within that month are more unequal.**

- A plot of the 'Reading Challenge Score' has been saved to 'reading_challenge_score.png'

### Most Challenging Periods
The Reading Challenge score combines both high volume and high day-to-day volatility.
The peak challenge score occurs around: November 14.

Top 3 most challenging weeks (by average score):
|Weeks|Challenge Score|
|-|-|
|46|    2.209488
|4|     2.185230
|28|    2.151816