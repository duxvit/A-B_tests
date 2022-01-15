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

def test_report_2(chat=None):
    # Query for ACTIVE USERS by days (news_feed, messages< both services)
    users_both_services_per_day = Getch('''
        select day, users_both, users_feeds, users_msgs, 
    users_feeds - users_both as users_only_feeds,
    users_msgs - users_both as users_only_msgs,
    users_only_msgs + users_only_feeds + users_both as users_total
    from
    (
    select Count(user) as users_both, day
        from
        (select distinct user_id as user, toDate(time) as day
        from simulator_20211220.feed_actions
        ) t1
        inner join
        (
        select distinct user_id as user, toDate(time) as day
        from simulator_20211220.message_actions
        ) t2
        on t1.user = t2.user and t1.day = t2.day
        group by day
        order by day
    ) t1_t2
    inner join
    (
    select *
    from
    (
    select uniqExact(user_id) as users_feeds, toDate(time) as day
    from simulator_20211220.message_actions
    group by day
    order by day
    ) t3
    inner join 
    (
    select uniqExact(user_id) as users_msgs, toDate(time) as day
    from simulator_20211220.feed_actions
    group by day
    order by day
    ) t4
    on t3.day = t4.day 
    ) t3_t4
    on t1_t2.day = t3_t4.day
    having day < today() and day >= today() - 14
    ''').df

    # Query for new users by days (news_feed, messages< both services)
    new_users = Getch('''
    -- count total number of users who registred in feeds news, messages, and both services
    select reg_day, users_feed, users_msgs, users_both, 
    users_feed + users_msgs - users_both as new_users 
    from
    -- join t1 and t2 counts of news_feed and messages
    (
    select *
    from
    (
    -- count new users from feed news
    select count(user_id) as users_feed, reg_day
    from
    (
    select distinct user_id, min(toDate(time)) as reg_day
    from simulator_20211220.feed_actions
    group by user_id
    ) t1
    group by reg_day
    ) t1
    join
    (
    -- count new users from  messages
    select count(user_id) as users_msgs, reg_day
    from
    (
    select distinct user_id, min(toDate(time)) as reg_day
    from simulator_20211220.message_actions
    group by user_id
    ) t1
    group by reg_day
    ) t2
    on t1.reg_day = t2.reg_day
    )  t1_t2
    join
    (
    -- count new users both services
    select count(t1.user_id) as users_both, t1.reg_day
    from
    (
    select distinct user_id, min(toDate(time)) as reg_day
    from simulator_20211220.feed_actions
    group by user_id ) t1
    join
    (
    select distinct user_id, min(toDate(time)) as reg_day
    from simulator_20211220.message_actions
    group by user_id
    ) t2
    on t1.user_id = t2.user_id
    group by t1.reg_day
    ) t3
    on t1_t2.reg_day = t3.reg_day
    having reg_day < today() and reg_day >= today() - 14
    ''').df

    # Query for new users by days (source : organic or ads)
    new_feed_source = Getch('''
    select count(user_id) as new_users,reg_day, source
    from
    (
    select distinct user_id, min(toDate(time)) as reg_day, source
    from simulator_20211220.feed_actions
    group by user_id, source
    )

    group by reg_day, source
    having reg_day < today() and reg_day >= today() - 14
    order by reg_day, source
    ''').df

    # Query for new users by days (os : Android or iOS)
    new_feed_os = Getch('''
    select count(user_id) as new_users,reg_day, os
    from
    (
    select distinct user_id, min(toDate(time)) as reg_day, os
    from simulator_20211220.feed_actions
    group by user_id, os
    )
    group by reg_day, os
    having reg_day < today() and reg_day >= today() - 14
    order by reg_day, os

    ''').df

    #chat, where our messages will be sended
    chat_id_1 = 2033458470  # my chat
    chat_id_2 = -674009613  # chat of the team
    bot = telegram.Bot(token='5039125354:AAFoVMBy_XAwmk2vlOTa-wyqafZ1n11J3es') # token of my bot

    ### Create variables for our future report
    #report day
    day =new_users['reg_day'].iloc[-1].strftime("%d/%m/%Y")
    #metrics by os
    metric_ios = new_feed_os.iloc[-1]['os']
    metric_ios_count = new_feed_os.iloc[-1]['new_users']
    metric_android = new_feed_os.iloc[-2]['os']
    metric_android_count = new_feed_os.iloc[-2]['new_users']
    #metrics by source
    metric_organic = new_feed_source.iloc[-1]['source']
    metric_organic_count = new_feed_source.iloc[-1]['new_users']
    metric_ads = new_feed_source.iloc[-2]['source']
    metric_ads_count =new_feed_source.iloc[-2]['new_users']
    #metrics for new users both services
    metric_both = 'new users from both services'
    metric_both_count = new_users.iloc[-1]['new_users']
    #metric active users
    metric_only_feeds = users_both_services_per_day.columns[4]
    metric_only_feeds_count = users_both_services_per_day.iloc[-1][4]
    metric_only_msgs = users_both_services_per_day.columns[5]
    metric_only_msgs_count = users_both_services_per_day.iloc[-1][5]
    metric_active_both = users_both_services_per_day.columns[6]
    metric_active_both_count = users_both_services_per_day.iloc[-1][6]

    # Message for telegram chat
    msg= ''' <b>Report for {day}</b> 

    <b>New users(news feed) by os</b>: 
    {metric_ios} = {metric_ios_count}, {metric_android} = {metric_android_count}
    <b>New users (news feed) by source</b>: 
    {metric_organic} = {metric_organic_count}, {metric_ads} = {metric_ads_count}
    <b>New users (both services)</b>:
    {metric_both} = {metric_both_count}
    <b>Active users</b>:
    {metric_only_feeds} = {metric_only_feeds_count}, {metric_only_msgs} = {metric_only_msgs_count}, {metric_active_both} = {metric_active_both_count}
    '''.format(day=day,
                                                                                    metric_ios =metric_ios,
                                                                                    metric_ios_count=metric_ios_count,
                                                                                    metric_android=metric_android,
                                                                                    metric_android_count=metric_android_count,
            metric_organic=metric_organic,
            metric_organic_count=metric_organic_count,
            metric_ads=metric_ads,
            metric_ads_count=metric_ads_count,
            metric_both=metric_both,
            metric_both_count=metric_both_count,
            metric_only_feeds=metric_only_feeds,
            metric_only_feeds_count=metric_only_feeds_count,
            metric_only_msgs=metric_only_msgs,
            metric_only_msgs_count=metric_only_msgs_count,
            metric_active_both=metric_active_both,
            metric_active_both_count=metric_active_both_count)

    # SEND the message to the chats
    bot.sendMessage(chat_id=chat_id_1, text=msg, parse_mode='HTML')
    # bot.sendMessage(chat_id=chat_id_2, text=msg, parse_mode='HTML')

    # create data frames for suitable building the charts
    new_feed_os_android = new_feed_os[new_feed_os['os'] == 'Android'] # only androids
    new_feed_os_ios = new_feed_os[new_feed_os['os'] == 'iOS'] # only iOs

    new_feed_source_organic = new_feed_source[new_feed_source['source'] == 'organic']  # only organic
    new_feed_source_ads = new_feed_source[new_feed_source['source'] == 'ads']  # only ads

    # Build 1 image with 4 plots : 1.New users (by os), 2.New users (by source), 3.New users (both services), 4. Active users
    fig, axs = plt.subplots(2, 2, figsize=(20,10))
    # plot 1 for new users by os
    axs[0, 0].plot(new_feed_os_android['reg_day'], new_feed_os_android['new_users']) # android
    axs[0, 0].plot(new_feed_os_ios['reg_day'], new_feed_os_ios['new_users']) # iOS
    axs[0, 0].legend(labels=['Android', 'iOS'], loc='lower left') # legend for chart 1
    axs[0, 0].set_title('New users by OS (only feed news) 14 days') # title for chart
    # plot 2 for new users by source
    axs[0, 1].plot(new_feed_source_organic['reg_day'], new_feed_source_organic['new_users']) # organic
    axs[0, 1].plot(new_feed_source_ads['reg_day'], new_feed_source_ads['new_users']) # ads
    axs[0, 1].legend(labels=['organic', 'ads'], loc='lower left') # legend for chart 2
    axs[0, 1].set_title('New users by source (only feed news) 14 days') # title for chart 2
    #plot 3 for new users for both services (news feed + messages)
    axs[1, 0].plot(new_users['reg_day'], new_users['new_users']) # new users both services
    axs[1, 0].set_title('New users (both services) 14 days ') # title for chart 3
    # plot 4 for active users 
    axs[1, 1].plot(users_both_services_per_day['day'], users_both_services_per_day['users_total']) # users total every day
    axs[1, 1].plot(users_both_services_per_day['day'], users_both_services_per_day['users_only_msgs']) #  users only messages
    axs[1, 1].plot(users_both_services_per_day['day'], users_both_services_per_day['users_only_feeds']) # users only feed news 
    axs[1, 1].legend(labels=['Users (total)', 'Users (only messages)', 'Users (only news feed)'], loc='lower left') # legend for chart 4
    axs[1, 1].set_title('Active users 14 days ') # title for chart 4

    plot_object = io.BytesIO()
    plt.savefig(plot_object)
    plot_object.name = '14_prev_days_plots.png'
    plot_object.seek(0)
    plt.close()

    bot.sendPhoto(chat_id=chat_id_1, photo=plot_object)
    # bot.sendPhoto(chat_id=chat_id_2, photo=plot_object)
try:
    test_report_2()
except Exception as e:
    print(e)
