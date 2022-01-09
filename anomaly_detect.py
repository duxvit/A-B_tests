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

    @property
    def getchdf(self):
        try:
            self.df = pandahouse.read_clickhouse(self.query, connection=self.connection)

        except Exception as err:
            print("\033[31m {}".format(err))
            exit(0)


def check_anomaly(data, a=3):
    data['std'] = data.feed_users.rolling(4, min_periods=0).std()
    data['min_val'] = data['avg_users'] - a * data['std'] 
    data['max_val'] = data['avg_users'] + a * data['std'] 
    
    current_ts = data['ts'].max()
    quarter_hour_ago_ts = current_ts - pd.DateOffset(minutes=15)
    
    current_value = data[data['ts'] == current_ts]['feed_users'].iloc[0]
    quarter_hour_ago_value = data[data['ts'] == quarter_hour_ago_ts]['feed_users'].iloc[0]
    
    min_val = data[data['ts'] == quarter_hour_ago_ts]['min_val'].iloc[0]
    max_val = data[data['ts'] == quarter_hour_ago_ts]['max_val'].iloc[0]
    
    diff = abs(current_value / quarter_hour_ago_value - 1)
    
    if min_val  < current_value  < max_val :
        alert = 0
    else:
        alert = 1
    
    
    return alert, current_value, diff

def run_alert(chat=None):
    chat_id = chat or 2033458470
    bot = telegram.Bot(token='5039125354:AAFoVMBy_XAwmk2vlOTa-wyqafZ1n11J3es')
    
    data = Getch('''
        select uniqExact(user_id) as feed_users, toDate(ts) as date, formatDateTime(ts, '%R') as hm, 
        toStartOfFifteenMinutes(time) as ts, avg(feed_users) over w as avg_users
        from simulator_20211220.feed_actions
        where ts >= today() - 1 and ts < toStartOfFifteenMinutes(now()) 
        group by ts
        window w as (order by ts rows between 3 preceding and current row)
        order by ts 
        ''').df
    
    alert, current_value, diff = check_anomaly(data)
    
    metric = 'feed_users'
    
    if alert:
        msg = '''<b>Метрика {metric}</b>\nТекущее значение = {current_value:.2f}\nОтклонение от прошлых 15 минут {diff:.2%}'''.format(metric=metric, current_value=current_value, diff=diff)
        
        start_index = data[data['date'] == data['date'].max()].iloc[0].name - 4
        
        plt.figure(figsize=(15, 8))
        plt.plot()
        ax = sns.lineplot(data=data.loc[start_index:], x='hm', y=metric)

        for ind, label in enumerate(ax.get_xticklabels()):
            if ind % 8 == 0:
                label.set_visible(True)
            else:
                label.set_visible(False)

        ax.set(xlabel='time')
        ax.set(ylabel='{}'.format(metric))
        
        plot_object = io.BytesIO()
        plt.savefig(plot_object)
        plot_object.name = 'probe_plot.png'
        plot_object.seek(0)

        plt.close()
        
        bot.sendPhoto(chat_id=chat_id, photo=plot_object)
        bot.sendMessage(chat_id=chat_id, text=msg, parse_mode='HTML')
        
try:
    run_alert()
except Exception as e:
    print(e)
    
    
