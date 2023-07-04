# OSRS_Forecasting
This project covers the process of gathering daily snapshots of the OSRS Hiscores (https://secure.runescape.com/m=hiscore_oldschool/overall) for the purposes of analysis and forecasting.

## Data Scraping
### Overview
The initial idea for the project was to gather snapshots of players on the OSRS hiscores over time to track progression. The most basic (and useful) of the data was the last ranked player on the hiscores. This metric would indicate the total number of players participating in an activity. For example, looking at the last ranked player on the hiscores for a specific boss might show that they have a rank of 100,000 meaning that a total of 100,000 players have defeated the boss enough to show up on the hiscores. If the following day the last player has a rank of 100,025 we can conclude that 25 new players have defeated the boss and can calculate the rate of change over time.

The other segments of data are based on percentiles such as the top 1% of players for a given boss. While the data for these stratum is interesting, the inconsistencies due to movement make understanding the data difficult. For example, if there are 1,000 players on the hiscores for a specific boss, the top 1% is the player who is ranked 10th (1000 * 0.01 = 10). If the next day 100 new players show up on the hiscores, the top 1% is the player ranked 11th (1100 * 0.01 = 10). If rank 10 has defeated the boss 300 times and rank 11 has defeated the boss 250 times then the change day over day for the top 1% would be -50. The same result would appear in the data if the player who is ranked 10th gets banned for breaking game rules and is removed from the hiscores. A better option for a future iteration may be to use ranks rather than percentiles. So, instead of using the top 1%, use the player who is ranked 100th.

### Webpage Architecture
Each boss section of the hiscores can hold up to 2,000,000 players with 25 players being displayed per page for a maximum of 80,000 pages. Each entry on a page contains the rank, player name, and score. The URL of the hiscores can be manipulated to move directly to a specific page. The first page of the hiscores will only have a button to move to the next page, the last page will only have a button to move to the previous page, and any other page will have two buttons to move to the next or previous page. Links at the top and side of the page can change the boss or category (eg. Normal mode to Ironman) though these can also be manipulated via the URL.

### Limiting Request Timeouts with Binary Search
The largest issue is trying to find the last person on the hiscores for a given boss. Not only is this an important metric to track but the percentile calculations are all based on this number. This value can vary from boss to boss and changes day after day. The number of times the hiscores can be requested is limited before the webpage times out and produces a message asking you to wait before trying again. It is also not ideal to overload the website every day with requests. To find the last page of data we can utilize a binary search to decrease the number of page requests. 
We have all of the necessary criteria. A starting point (the first page, denoted by a single button to move to the next page) an ending point (page 80,000), a success case (the last page, denoted by a single button to move to the previous page), and a failure state of which there are two. The first failure state is if there are two buttons to move to the next or previous page. This means there are more pages after the current page and we are also not on the first page. The second failure state is if we try to go to a page that does not exist. For example, if the last page is page 10,000 and we try to load page 12,000 (which does not exist) the website will redirect us to the first page. This application of binary search brings the total number of possible searches down from 80,000 to a maximum of 17.

## Forecasting and Seasonal Decomposition
The daily cadence of the data allows us to create a variety of different machine learning models to predict the progression of hiscore growth over time. As noted in the Data Scraping Overview section, it can be difficult to work with the percentile data. The information that follows will utilize the metric of the last person ranked on the hiscores.

### Data Prep
There are several issues with the current data. The first is that a few last values are missing. This can be remedied by averaging the surrounding values. For example, if the last person on the hiscores on 2022-01-01 had a rank of 1000, 2022-01-02 was missing, and the last rank on 2022-01-03 was 1010 we can calculate the last rank on 2022-01-02 as (1000 + 1010)/2 = 1005.
The next issue is with missing dates. For these we can calculate the number of days between adjacent dates and, in the event there is a difference greater than one day, interpolate the last ranks for the missing days.

### STL Decomposition
A powerful tool in forecasting is seasonal decomposition which breaks down a set of data over time into three components. The first is the trend which indicates if the data is increasing, decreasing, or staying the same as time progresses. The second is the seasonal component which notes the changes in the data due to recurring seasonal effects. If we combine these two pieces we expect to get the actual value. However, if the calculated value is different than the actual value we get the third component of seasonal decomposition which is the residual or error. The residual is useful for identifying outliers in the data. 

In this use case, we can combine the residuals of all bosses and use the frequency to determine where there were abnormal numbers of new players and abnormal numbers of losses to the hiscores.
![image](https://github.com/Vinnie-Singleton/OSRS_Forecasting/blob/main/Pics/residuals_plot.png)

If we count the top days of increases and decreases we can narrow down the possible reasons for the discrepancies. For example, on 2022-07-08 there were a large number of bosses that saw an unexpected decrease in players. Coupled with the unexpected increase in players the day after on 2022-07-09 this could be evidence of a large number of bots being banned and then a large number of new bots being created and deployed.

![image](https://github.com/Vinnie-Singleton/OSRS_Forecasting/blob/main/Pics/upper_outliers.png)

![image](https://github.com/Vinnie-Singleton/OSRS_Forecasting/blob/main/Pics/lower_outliers.png)

### Forecasting Models
While exogenous variables may be used in the future to add additional predictive power to the models, a simple univariate approach is used here. The three models that were implemented are ARIMA, SARIMA, and LSTM. Each model was trained on the data for each boss excluding the last 30 days. Each model forecasted 30 days into the future and the predictions were compared to the actual values using the Mean Squared Error metric.

#### ARIMA and SARIMA
The d value of the ARIMA and SARIMA models were computed using an Augmented Dickey-Fuller test for stationarity and smoothed (using first, second, etc. differencing). To find the best model, a brute force approach was implemented where the p, q, P, and Q values were set using a range in combination with the itertools library to compute all possible permutations. The p and q values were set to a range of 0 to 6 for both ARIMA and SARIMA while the SARIMA models' seasonal parameters were set from 0 to 3 with a set seasonal trend of 7 to detect weekly seasonality. This created a list of 40 ARIMA models and 400 SARIMA models all having unique parameters.

#### LSTM
The LSTM model was created using Tensorflow with an LSTM node of size 32 using relu as the activation function followed by a Dense 16 and a Dense 8 layer both using relu and finishing with a Dense 1 layer using a linear activation function. A future experiment could expand the hyperparameter search but for the purposes of this project, a single model works.

### Results
The SARIMA model performed best for 47 of the bosses. ARIMA was the second most performative being the model of choice for 14 of the bosses. LSTM was the best choice for only 3 of the bosses. The predictions and actual values were all recorded to better be able to visualize the results.

![image](https://github.com/Vinnie-Singleton/OSRS_Forecasting/blob/main/Pics/forecast_graph_example.png)

## Activity Comparison 

### Tables
The simplest way to determine the most popular content would be to calculate the average rate of growth per day. When you sort the data by this value you get this table.

| Boss                             |   AVG_Growth_Per_Day |   Completions_Needed_for_HS |
|:---------------------------------|---------------------:|----------------------------:|
| Rifts_closed                     |                 1040 |                           2 |
| Phantom_Muspah                   |                  899 |                          50 |
| Clue_Scrolls_all                 |                  796 |                           2 |
| Clue_Scrolls_beginner            |                  672 |                           1 |
| Clue_Scrolls_easy                |                  373 |                           1 |
| Clue_Scrolls_medium              |                  342 |                           1 |
| Wintertodt                       |                  340 |                          50 |
| Hespori                          |                  315 |                           5 |
| Tombs_of_Amascut_Normal          |                  302 |                          50 |
| Clue_Scrolls_hard                |                  291 |                           1 |
| Skotizo                          |                  226 |                           5 |
| Tempoross                        |                  222 |                          50 |
| Obor                             |                  222 |                           5 |
| Clue_Scrolls_elite               |                  215 |                           1 |
| Barrows_Chests                   |                  215 |                          50 |
| Bryophyta                        |                  205 |                           5 |
| Vorkath                          |                  186 |                          50 |
| Kraken                           |                  160 |                          50 |
| LMS_Rank                         |                  157 |                         500 |
| Clue_Scrolls_master              |                  151 |                           1 |
| Dagannoth_Rex                    |                  145 |                          50 |
| The_Corrupted_Gauntlet           |                  138 |                           5 |
| Tombs_of_Amascut_Expert          |                  137 |                          50 |
| Zulrah                           |                  129 |                          50 |
| General_Graardor                 |                  120 |                          50 |
| King_Black_Dragon                |                  115 |                          50 |
| Giant_Mole                       |                  110 |                          50 |
| Mimic                            |                  105 |                           1 |
| TzTokJad                         |                  102 |                           5 |
| Cerberus                         |                   95 |                          50 |
| Thermonuclear_Smoke_Devil        |                   90 |                          50 |
| Soul_Wars_Zeal                   |                   90 |                         200 |
| Dagannoth_Supreme                |                   88 |                          50 |
| Dagannoth_Prime                  |                   88 |                          50 |
| Grotesque_Guardians              |                   84 |                          50 |
| Sarachnis                        |                   82 |                          50 |
| Alchemical_Hydra                 |                   75 |                          50 |
| Abyssal_Sire                     |                   74 |                          50 |
| Kril_Tsutsaroth                  |                   73 |                          50 |
| Kalphite_Queen                   |                   71 |                          50 |
| Zalcano                          |                   63 |                          50 |
| Callisto                         |                   62 |                          50 |
| Commander_Zilyana                |                   61 |                          50 |
| Nex                              |                   61 |                          50 |
| KreeArra                         |                   55 |                          50 |
| Crazy_Archaeologist              |                   55 |                          50 |
| Chambers_of_Xeric                |                   49 |                          50 |
| TzKalZuk                         |                   46 |                           1 |
| Chaos_Elemental                  |                   44 |                          50 |
| Venenatis                        |                   43 |                          50 |
| The_Gauntlet                     |                   41 |                          50 |
| Chaos_Fanatic                    |                   39 |                          50 |
| PvP_Arena_Rank                   |                   37 |                        2525 |
| Vetion                           |                   33 |                          50 |
| Scorpia                          |                   33 |                          50 |
| Corporeal_Beast                  |                   32 |                          50 |
| Chambers_of_Xeric_Challenge_Mode |                   27 |                           5 |
| Deranged_Archaeologist           |                   23 |                          50 |
| Theatre_of_Blood                 |                   17 |                          50 |
| Phosanis_Nightmare               |                   11 |                          50 |
| Theatre_of_Blood_Hard_Mode       |                    7 |                          50 |
| Nightmare                        |                    6 |                          50 |
| Bounty_Hunter_Rogue              |                    1 |                           2 |
| Bounty_Hunter_Hunter             |                   -5 |                           2 |

One reason this table is problematic is that different activities require different levels of completion to show up on the hiscores. For example, to show up on the Vorkath hiscores you need to defeat the boss 50 times compared to the Guardians of the Rift Mini Game (Rifts_closed) where you only need two completions. If we use linear interpolation we can calculate what the score would be for rank 50 for the bosses and activities that need less than 50 to show up on the hiscores. If we sort the data by this new column we get this table.

| Boss                             |   Adjusted_Growth |   Completions_Needed_for_HS |
|:---------------------------------|------------------:|----------------------------:|
| Phantom_Muspah                   |               899 |                          50 |
| Rifts_closed                     |               519 |                           2 |
| Wintertodt                       |               340 |                          50 |
| Tombs_of_Amascut_Normal          |               302 |                          50 |
| Clue_Scrolls_all                 |               294 |                           2 |
| Tempoross                        |               222 |                          50 |
| Barrows_Chests                   |               215 |                          50 |
| Vorkath                          |               186 |                          50 |
| Kraken                           |               160 |                          50 |
| LMS_Rank                         |               157 |                         500 |
| Dagannoth_Rex                    |               145 |                          50 |
| Tombs_of_Amascut_Expert          |               137 |                          50 |
| Zulrah                           |               129 |                          50 |
| Clue_Scrolls_easy                |               127 |                           1 |
| Clue_Scrolls_hard                |               125 |                           1 |
| General_Graardor                 |               120 |                          50 |
| Hespori                          |               116 |                           5 |
| King_Black_Dragon                |               115 |                          50 |
| Giant_Mole                       |               110 |                          50 |
| The_Corrupted_Gauntlet           |               106 |                           5 |
| Cerberus                         |                95 |                          50 |
| Soul_Wars_Zeal                   |                90 |                         200 |
| Thermonuclear_Smoke_Devil        |                90 |                          50 |
| Dagannoth_Prime                  |                88 |                          50 |
| Dagannoth_Supreme                |                88 |                          50 |
| Grotesque_Guardians              |                84 |                          50 |
| Sarachnis                        |                82 |                          50 |
| Clue_Scrolls_medium              |                81 |                           1 |
| Alchemical_Hydra                 |                75 |                          50 |
| Abyssal_Sire                     |                74 |                          50 |
| Kril_Tsutsaroth                  |                73 |                          50 |
| Kalphite_Queen                   |                71 |                          50 |
| Zalcano                          |                63 |                          50 |
| Callisto                         |                62 |                          50 |
| Commander_Zilyana                |                61 |                          50 |
| Nex                              |                61 |                          50 |
| Crazy_Archaeologist              |                55 |                          50 |
| KreeArra                         |                55 |                          50 |
| Clue_Scrolls_beginner            |                51 |                           1 |
| Chambers_of_Xeric                |                49 |                          50 |
| Chaos_Elemental                  |                44 |                          50 |
| Venenatis                        |                43 |                          50 |
| Clue_Scrolls_elite               |                42 |                           1 |
| The_Gauntlet                     |                41 |                          50 |
| Chaos_Fanatic                    |                39 |                          50 |
| PvP_Arena_Rank                   |                37 |                        2525 |
| Vetion                           |                33 |                          50 |
| Scorpia                          |                33 |                          50 |
| Corporeal_Beast                  |                32 |                          50 |
| Clue_Scrolls_master              |                31 |                           1 |
| Skotizo                          |                26 |                           5 |
| Deranged_Archaeologist           |                23 |                          50 |
| Theatre_of_Blood                 |                17 |                          50 |
| Bryophyta                        |                17 |                           5 |
| Chambers_of_Xeric_Challenge_Mode |                13 |                           5 |
| Phosanis_Nightmare               |                11 |                          50 |
| Theatre_of_Blood_Hard_Mode       |                 7 |                          50 |
| Nightmare                        |                 6 |                          50 |
| Obor                             |                 4 |                           5 |
| TzTokJad                         |                 3 |                           5 |
| TzKalZuk                         |                 0 |                           1 |
| Bounty_Hunter_Rogue              |                 0 |                           2 |
| Mimic                            |                 0 |                           1 |
| Bounty_Hunter_Hunter             |                -4 |                           2 |


### Graphs
We can compare the popularity of content by grouping bosses into categories and graphing the cumulative change over time and the total change over time. The cumulative change is useful for visualizing the rate of change while the totals provide a look into the overall popularity of a boss.

### Clue Scrolls
![image](https://github.com/Vinnie-Singleton/OSRS_Forecasting/blob/main/Pics/cum_clue_growth.png)
![image](https://github.com/Vinnie-Singleton/OSRS_Forecasting/blob/main/Pics/total_clue_growth.png)

### Skilling Bosses
![image](https://github.com/Vinnie-Singleton/OSRS_Forecasting/blob/main/Pics/cum_skillingboss_growth.png)
![image](https://github.com/Vinnie-Singleton/OSRS_Forecasting/blob/main/Pics/total_skillingboss_growth.png)

### Wilderness Bosses
![image](https://github.com/Vinnie-Singleton/OSRS_Forecasting/blob/main/Pics/cum_wildernessboss_growth.png)
![image](https://github.com/Vinnie-Singleton/OSRS_Forecasting/blob/main/Pics/total_wildernessboss_growth.png)

### PVP
![image](https://github.com/Vinnie-Singleton/OSRS_Forecasting/blob/main/Pics/cum_pvp_growth.png)
![image](https://github.com/Vinnie-Singleton/OSRS_Forecasting/blob/main/Pics/total_pvp_growth.png)

### Slayer Bosses
![image](https://github.com/Vinnie-Singleton/OSRS_Forecasting/blob/main/Pics/cum_slayerboss_growth.png)
![image](https://github.com/Vinnie-Singleton/OSRS_Forecasting/blob/main/Pics/total_slayerboss_growth.png)

### God Wars Bosses
![image](https://github.com/Vinnie-Singleton/OSRS_Forecasting/blob/main/Pics/cum_gwdboss_growth.png)
![image](https://github.com/Vinnie-Singleton/OSRS_Forecasting/blob/main/Pics/total_gwdboss_growth.png)

### Free to Play Bosses
![image](https://github.com/Vinnie-Singleton/OSRS_Forecasting/blob/main/Pics/cum_f2pboss_growth.png)
![image](https://github.com/Vinnie-Singleton/OSRS_Forecasting/blob/main/Pics/total_f2pboss_growth.png)

### Medium Bosses
![image](https://github.com/Vinnie-Singleton/OSRS_Forecasting/blob/main/Pics/cum_medboss_growth.png)
![image](https://github.com/Vinnie-Singleton/OSRS_Forecasting/blob/main/Pics/total_medboss_growth.png)

### Hard Bosses
![image](https://github.com/Vinnie-Singleton/OSRS_Forecasting/blob/main/Pics/cum_hardboss_growth.png)
![image](https://github.com/Vinnie-Singleton/OSRS_Forecasting/blob/main/Pics/total_hardboss_growth.png)

### Raids
![image](https://github.com/Vinnie-Singleton/OSRS_Forecasting/blob/main/Pics/cum_raids_growth.png)
![image](https://github.com/Vinnie-Singleton/OSRS_Forecasting/blob/main/Pics/total_raids_growth.png)

### End Game Bosses
![image](https://github.com/Vinnie-Singleton/OSRS_Forecasting/blob/main/Pics/cum_endgameboss_growth.png)
![image](https://github.com/Vinnie-Singleton/OSRS_Forecasting/blob/main/Pics/total_endgameboss_growth.png)

### Variable Time Bosses
![image](https://github.com/Vinnie-Singleton/OSRS_Forecasting/blob/main/Pics/cum_variabletimeboss_growth.png)
![image](https://github.com/Vinnie-Singleton/OSRS_Forecasting/blob/main/Pics/total_variabletimeboss_growth.png)

### Ironman
![image](https://github.com/Vinnie-Singleton/OSRS_Forecasting/blob/main/Pics/cum_ironman_growth.png)
![image](https://github.com/Vinnie-Singleton/OSRS_Forecasting/blob/main/Pics/total_ironman_growth.png)






