# This python file is only for news feed anomaly detection 
#import libraries
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import telegram
import pandahouse
from datetime import date
import io
import sys
import os
from CH import Getch

#  Create a function to detect the anomalies
def check_anomaly(data,data_2, a=2.5, b=2): # a is for upper limit. b is for lower limit
    
    metrics = ['feed_users', 'likes', 'views', 'CTR'] # our metrics, we need to estimate
    # define min/max possible value of our metric


    # Create variables for the future
    values = [] #  current value of the metric
    alert = []  # if 1, then we detected anomaly
    diff = []  # difference between current value and  quarter hour ago value
    minimum = [] 
    maximum = []
    metric_name = [] # name of the metric

    for i in data[metrics].columns:
        data['min_val_'+i] = data['avg_'+i] - b * data['std_'+i]        # avg - b * std
        data['max_val_'+i] = data['avg_'+i] + a * data['std_'+i]        # avg + a * std

        # create min/ max val for previous quater of hour
        min_val = data['min_val_'+i].iloc[-1]  # min value of the metric
        max_val = data['max_val_'+i].iloc[-1]  # max value of the metric
        # find the value of our metric
        current_val = data_2[i].iloc[0]  # current value of the metric
        quarter_hour_ago_value = data[i].iloc[-1] # quarter hour ago value of the metric


        if min_val < current_val < max_val:
            metric_name.append(i)
            alert.append(0)
            values.append(current_val)
            diff.append(abs(current_val / quarter_hour_ago_value - 1))
            minimum.append(min_val)
            maximum.append(max_val)
        else:
            metric_name.append(i)
            alert.append(1)
            values.append(current_val)
            diff.append(abs(current_val / quarter_hour_ago_value - 1))
            minimum.append(min_val)
            maximum.append(max_val)

    data_alert = pd.DataFrame({'metric' : metric_name, 
                               'alert' :alert, 
                               'value' :values, 
                               'diff' :diff, 
                               'min' : minimum, 
                               'max' : maximum})

    return data_alert  # data frame with detected anomaies. If alert == 1, the anomaly is detected

#   Create a function to send alert messages to the chat in telegram
def run_alert(chat=None, data=None, data_2=None):
    
    # Telegram chat, where alerts will be sent
    chat_id_1 = chat or 2033458470  # my chat
    chat_id_2 = -674009613   # group chat
    
    bot = telegram.Bot(token=os.environ.get("token")) # token of my bot
    
    if data is None: # check, if we have already had data from the start of function
        # Query for feed_users, likes, views, CTR and their averages and stds. Interval 7 days
        data = Getch('''
        select  toStartOfFifteenMinutes(time) as ts, toDate(ts) as date,formatDateTime(ts, '%R') as hm, 
                toDayOfWeek(date) as day_of_week,
                uniqExact(user_id) as feed_users, countIf(user_id, action = 'like') as likes,
                countIf(user_id, action = 'view') as views, likes / views as CTR,
                -- avg and std for our metrics
                avg(feed_users) over w as avg_feed_users, stddevPop(feed_users) over w as std_feed_users,
                avg(likes) over w as avg_likes, stddevPop(likes) over w as std_likes,
                avg(views) over w as avg_views, stddevPop(views) over w as std_views,
                avg(CTR) over w as avg_CTR, stddevPop(CTR) over w as std_CTR

        from simulator_20211220.feed_actions
        -- take data of 7 previous days and now - 30 minutes. Next 30 minutes we will take in  next query
        where ts >= today() - 7 and  ts < toStartOfFifteenMinutes(FROM_UNIXTIME(toUnixTimestamp(now()) - 900)) 
        group by ts
        window w as (order by hm, day_of_week)
        order by ts
        ''').df
        
    if data_2 is None: #  the same step as previous
        # Query for defining current time and value
        data_2 = data_2 or Getch ('''
        select  toStartOfFifteenMinutes(time) as ts, toDate(ts) as date,formatDateTime(ts, '%R') as hm, 
                toDayOfWeek(date) as day_of_week,
                uniqExact(user_id) as feed_users, countIf(user_id, action = 'like') as likes,
                countIf(user_id, action = 'view') as views, likes / views as CTR
        from simulator_20211220.feed_actions
        where ts >= FROM_UNIXTIME(toUnixTimestamp(now()) - 1800)
        group by ts
        window w as (order by hm, day_of_week)
        order by ts
        ''').df
    
    #check, if we have any anomalies
    data_alert = check_anomaly(data, data_2)
    
    for i in range(0, len(data_alert)):
        # If anomaly = 1, then we will send message to our telegram chat
        if data_alert['alert'].iloc[i] == 1:
            # create variables
            metric = data_alert['metric'].iloc[i]
            current_value = data_alert['value'].iloc[i]
            diff = data_alert['diff'].iloc[i]
            
            # chart for 7 days
            
            data_7_days = pd.concat([data, data_2]).iloc[-672:]
            
            # Create plot
            plt.figure(figsize=(15, 8))
            plt.plot()
            ax = sns.lineplot(data=data_7_days, x='ts', y=metric, color='green')  # value of the metric
            sns.lineplot(data=data_7_days, x='ts', y='max_val_' + metric, color='red')  # max value of the metric
            sns.lineplot(data=data_7_days, x='ts', y='min_val_' + metric, color='blue') # min value of the metric
            ax.legend(labels=['value of the metric', 'maximum value', 'minimum value'], loc='upper left') #create legeng
        
            #create file object to send to telegram chat
            plot_object = io.BytesIO()
            plt.savefig(plot_object)
            plot_object.name = 'probe_plot.png'
            plot_object.seek(0)
            plt.close()

            # create message for the alert
            msg = '''
            <b>Метрика {metric}</b>\nТекущее значение = {current_value:.2f}\nОтклонение от предыдущего значения <b>{diff:.2%}</b>
            '''.format(metric=metric, current_value=current_value, diff=diff)
            # send alert!
            bot.sendPhoto(chat_id=chat_id_1, photo=plot_object)
            bot.sendPhoto(chat_id=chat_id_2, photo=plot_object)
            bot.sendMessage(chat_id=chat_id_1, text=msg, parse_mode='HTML')
            bot.sendMessage(chat_id=chat_id_2, text=msg, parse_mode='HTML')


try:
    run_alert()
except Exception as e:
    print(e)
    
    
