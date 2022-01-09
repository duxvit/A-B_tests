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

# Create function for checking anomaly

def check_anomaly(data, a=3): # a - alpha is coefficient for std
    # defining current time and previous 15 mins
    current_ts = data['ts'].max()
    quarter_hour_ago_ts = current_ts - pd.DateOffset(minutes=15)
    
    # create variables for the future
    values = []
    alert = []
    diff = []
    minimum = []
    maximum = []
    metric_name = []
    metrics = ['feed_users', 'likes', 'views', 'CTR', 'messages', 'msg_users']
    
    for i in data[metrics].columns:
        # Create new column STD (rolling std for 7+1 values) IMPORTANT!
        data['std_'+i] = data[i].rolling(8, min_periods=0).std() 
        data['min_val_'+i] = data['avg_'+i] - a * data['std_'+i]        # avg - a * std
        data['max_val_'+i] = data['avg_'+i] + a * data['std_'+i]        # avg + a * std

        # from current time & 15 minutes ago extract values of [feed_users, likes, views, CTR, messages, msg_users]
        current_value = data[data['ts'] == current_ts][i].iloc[0] 
        quarter_hour_ago_value = data[data['ts'] == quarter_hour_ago_ts][i].iloc[0]

        # find min & max acceptable values for 15 minutes ago
        min_val = data[data['ts'] == quarter_hour_ago_ts]['min_val_'+i].iloc[0]
        max_val = data[data['ts'] == quarter_hour_ago_ts]['max_val_'+i].iloc[0]

        #check, if current value between min & max values
        if min_val  < current_value  < max_val :
            metric_name.append(i)
            alert.append(0)
            values.append(current_value)
            diff.append(abs(current_value / quarter_hour_ago_value - 1))
            minimum.append(min_val)
            maximum.append(max_val)

        else:
            metric_name.append(i)
            alert.append(1)
            values.append(current_value)
            diff.append(abs(current_value / quarter_hour_ago_value - 1))
            minimum.append(min_val)
            maximum.append(max_val)
    
    data_alert = pd.DataFrame({'metric' : metric_name, 
                               'al' :alert, 
                               'val' :values, 
                               'dif' :diff, 
                               'min' : minimum, 
                               'max' : maximum})

    return data_alert

  
    # Creating  Alert function 

def run_alert(chat=None):
    # Telegram chat, where alerts will be sent
    chat_id = chat or 2033458470  
    bot = telegram.Bot(token='5039125354:AAFoVMBy_XAwmk2vlOTa-wyqafZ1n11J3es')
    
    # Import data from our database. Decided create fifteen minutes data and create rolling average with 8 values
    data = Getch('''
    select t1.*, t2.messages, t2.msg_users, 
    avg(t1.feed_users) over w as avg_feed_users, avg(t1.likes) over w as avg_likes, avg(t1.views) over w as avg_views,
    avg(t1.CTR)  over w as avg_CTR, avg(t2.messages) over w as avg_messages, avg(t2.msg_users) over w as avg_msg_users
    from
    (
    select  toStartOfFifteenMinutes(time) as ts, toDate(ts) as date,formatDateTime(ts, '%R') as hm,
    uniqExact(user_id) as feed_users, countIf(user_id, action = 'like') as likes,
    countIf(user_id, action = 'view') as views, likes / views as CTR
    from simulator_20211220.feed_actions
    where ts >= today() - 1 and  ts < toStartOfFifteenMinutes(now()) 
    group by ts
    order by ts
    ) t1
    inner join
    (
    select count(user_id) as messages, uniqExact(user_id) as msg_users, toStartOfFifteenMinutes(time) as ts
    from simulator_20211220.message_actions
    where ts >= today() - 1 and  ts < toStartOfFifteenMinutes(now()) 
    group by ts
    order by ts
    ) t2
    on t1.ts = t2.ts
    window w as (order by ts rows between 7 preceding and current row)
    ''').df

    # Check anomalies
    data_alert = check_anomaly(data)
    
    for i in range(0, len(data_alert)):
        # If anomaly = 1, then we will send message to our telegram chat
        if data_alert['al'].iloc[i] == 1:
            # create variables
            metric = data_alert['metric'].iloc[i]
            current_value = data_alert['val'].iloc[i]
            diff = data_alert['dif'].iloc[i]
            # create last variable 15 mins and last value at this time. I want to create red dot with current value on the plot
            last_hm = data['hm'].iloc[-1]
            last_value = data[metric].iloc[-1] 
            # Remove data from previous day except last 4 ticks
            start_index = data[data['date'] == data['date'].max()].iloc[0].name - 4
            
            # Create plot
            plt.figure(figsize=(15, 8))
            plt.plot()
            ax = sns.lineplot(data=data.loc[start_index:], x='hm', y=metric)
            # Draw red dot for the current value
            plt.plot(last_hm, last_value, 'ro')

            # this cycle is needed to discharge the X-axis coordinate signatures,
            for ind, label in enumerate(ax.get_xticklabels()):
                if ind % 4 == 0:
                    label.set_visible(True)
                else:
                    label.set_visible(False)

                    ax.set(xlabel='time')
                    ax.set(ylabel='{}'.format(metric))
                    ax.set_title(metric+' ANOMALY')
            # Create file object
            plot_object = io.BytesIO()
            plt.savefig(plot_object)
            plot_object.name = 'probe_plot.png'
            plot_object.seek(0)

            plt.close()
            # create message for the alert
            msg = '''
            <b>Метрика {metric}</b>\nТекущее значение = {current_value:.2f}\nОтклонение от предыдущей средней скользящей 15 минут <b>{diff:.2%}</b>
            '''.format(metric=metric, current_value=current_value, diff=diff)
            # send alert!
            bot.sendPhoto(chat_id=chat_id, photo=plot_object)
            bot.sendMessage(chat_id=chat_id, text=msg, parse_mode='HTML')

            
try:
    run_alert()
except Exception as e:
    print(e)
    
    
