# import libriaries 
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import telegram
import pandahouse
from datetime import date
from statsmodels.stats.power import TTestIndPower
from scipy import stats
from CH import Getch
import numpy as np
import io
import sys
import os

%matplotlib inline

# export data from our database
df = Getch('''
SELECT user_id,
       exp_group,
       countIf(action='like') as likes,
       countIf(action='view') as views,
       likes / views as CTR
FROM simulator_20211220.feed_actions
where toDate(time) >= toDate('2021-12-08') and toDate(time) <= toDate('2021-12-14') 
      and exp_group in (2, 3)
group by user_id, exp_group
''').df

df_group_2 = df[df['exp_group'] == 2]  # create dataframe only with rows from exp_group 2  
df_group_3 = df[df['exp_group'] == 3]  # create dataframe only with rows from exp_group 3 


# Function to do A/A test with p-values. If  
def aa_test(data_1, data_2, n=500, iteration=10000, test='ttest'):
    p_values = []   # create list to add all our p-values after test
    if test == 'ttest':
        for i in range(iteration):
            data_1_samples = data_1.sample(n=n, replace=True)   # sampling from data_1 n samples with replace
            data_2_samples = data_2.sample(n=n, replace=True)   # sampling from data_2 n samples with replace


            # compare the difference of our groups by ttest and extract p-value
            p_value_ttest = stats.ttest_ind(data_1_samples, data_2_samples, equal_var=True)[1]    
            p_values.append(p_value_ttest)   # add p-value to our list
    else:  # if test != 'ttest' implement mannwhitneyu test
        for i in range(iteration):
            data_1_samples = data_1.sample(n=n, replace=True)   # sampling from data_1 n samples with replace
            data_2_samples = data_2.sample(n=n, replace=True)   # sampling from data_2 n samples with replace


            # compare the difference of our groups by ttest and extract p-value
            p_value_ttest = stats.mannwhitneyu(data_1_samples, data_2_samples)[1]    
            p_values.append(p_value_ttest)   # add p-value to our list
        
    percents = sum(np.array(p_values) <= 0.05) / len(p_values)
        
    return p_values, percents

# acomplish our A/A test
p_values, percents = aa_test(df_group_2.CTR, df_group_3.CTR, test='none')

sns.displot(p_values, kde=False)  # plot p-values

print('p-values <= 0.05 in {percents:.3f}%\nNormal percentage(%) of p-values should be about 5%'.
      format(percents=percents) )

# As you can see A/A test shows us normal distribution of both exp_groups(2, 3) 