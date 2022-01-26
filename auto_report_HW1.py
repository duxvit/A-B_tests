import pandahouse
import Getch  # this function is for connecting with db and eporting data to Jupiter Notebook
import telegram
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import io
import logging
import pandas as pd
import os
import datetime

sns.set()

# this function is for sending report to telegram chat with key metrics (DAU, views, likes, CTR) and plotting these metrics.
def test_report(chat=None):
    
    # function for query SQL from db
    data = Getch(
        "select t1_t2.day, t1_t2.users as num_actions, t1_t2.action, t1_t2.CTR, t3.users as daily_users \
        from \
        ( \
        select t1.day, t1.users, t1.action, CTR \
        from \
        ( \
        select count(user_id) as users, toStartOfDay(time) as day, action \
        from simulator_20211220.feed_actions \
        group by toStartOfDay(time), action \
        order by toStartOfDay(time) DESC, action \
        ) t1  \
        join  \
        ( \
        select round(countIf(user_id, action='like') / countIf(user_id, action='view'), 3)  as CTR,  \
        toStartOfDay(time) as day \
        from simulator_20211220.feed_actions \
        group by toStartOfDay(time) \
        ) as t2 \
        on t1.day = t2.day \
        order by t1.day DESC, action \
        ) as t1_t2 \
        join \
        ( \
        select uniqExact(user_id) as users, toStartOfDay(time) as day  \
        from simulator_20211220.feed_actions  \
        group by toStartOfDay(time)  \
        order by toStartOfDay(time) DESC  \
        ) t3  \
        on t1_t2.day = t3.day \
        order by day DESC \
        limit 16" 
        ).df

    chat_id_1 = chat or 2033458470 # my chat
    chat_id_2 = -674009613  # group chat 
    bot = telegram.Bot(token='TOKEN')  # secret token 


    day = data['day'][2].strftime("%d/%m/%Y")
    dau = data['daily_users'][2]
    likes = data['num_actions'][2]
    views = data['num_actions'][3]
    ctr = data['CTR'][2]
    msg = 'REPORT FOR '+ day + '           ' +' DAU:'+ str(dau) + ', Views:' + str(views) \
            + ', Likes:' +  str(likes) + ', CTR:' + str(ctr)
    bot.sendMessage(chat_id=chat_id_1, text=msg, parse_mode='HTML')
    bot.sendMessage(chat_id=chat_id_2, text=msg, parse_mode='HTML')


    data2 = data[data['action'] == 'like']
    data3 = data[data['action'] == 'view']
    fig, axs = plt.subplots(2, 2, figsize=(20,10))
    axs[0, 0].plot(data2['day'][1:], data2['daily_users'][1:])
    axs[0, 0].set_title('DAU')
    axs[0, 1].plot(data2['day'][1:], data3['num_actions'][1:], 'tab:orange') #тут action = 'view'
    axs[0, 1].set_title('Views')
    axs[1, 0].plot(data2['day'][1:], data2['num_actions'][1:], 'tab:red') #тут action = 'like'
    axs[1, 0].set_title('Likes')
    axs[1, 1].plot(data2['day'][1:], data2['CTR'][1:], 'tab:green')
    axs[1, 1].set_title('CTR')
    plot_object = io.BytesIO()
    plt.savefig(plot_object)
    plot_object.name = '7_prev_days_plots.png'
    plot_object.seek(0)
    plt.close()
    bot.sendPhoto(chat_id=chat_id_2, photo=plot_object)
    bot.sendPhoto(chat_id=chat_id_1, photo=plot_object)
    
 

try:
    test_report()
except Exception as e:
    print(e)
