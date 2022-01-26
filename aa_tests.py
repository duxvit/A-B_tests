### class to conduct the A/A tests

# import libriaries
import numpy as np
import pandas as pd
from scipy import stats

# create class wich compare two groups by ttest and collecting p-values. 
class New():
    def __init__(self, data_1, data_2, n=500, iteration=10000):
        '''
        data_1    - first data we will compare
        data_2    - second data we will compare
        n         - number of sampling, wich will be extracted with replacement from our groups
        iteration - number of p-values we collect
        '''
        
        self.data_1 = data_1
        self.data_2 = data_2
        self.n = n
        self.iteration = iteration


    def implementation(self):
        try:
            p_values = []  # create list to add all our p-values after test
            for i in range(self.iteration):
                data_1_samples = self.data_1.sample(n=self.n, replace=True)  #sampling from data_1 n samples with replace
                data_2_samples = self.data_2.sample(n=self.n, replace=True)
                # compare the difference of our groups by ttest and extract p-value
                p_value_ttest = stats.ttest_ind(data_1_samples, data_2_samples, equal_var=True)[1]
                p_values.append(p_value_ttest)  # add p-value to our list

            percents = sum(np.array(p_values) <= 0.05) / len(p_values)
            result = 'p-values <= 0.05 in {percents:.2f}%\nNormal percentage(%) of p-values should be about ~5%'.format(percents=percents*100)

            return p_values, result
        except Exception as err:
                print("\033[31m {}".format(err))
                exit(0)