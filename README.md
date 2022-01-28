# Analysis of the Social network

In this repo I analyzed the syntetic start-up social network, wich has <b>messenger and feed news</b>.
All work was did remotely in GitLab, JupiterHub, Superset, ClickHouse, Redash.

## The main tasks were:
### 1. Create 3 dashboards in Superset : 
    - Feed news dashboard (DAU, WAU, MAU, likes, views, CTR, Retention, Weekly audience,location, operational system, source of the trafic).
    - Operational data dashboard (active users today).
    - Crossing news feed and messenger dashboard.
    files:news_feed.jpg, news_feed_operational_data.jpg, news_feed_messages.jpg
    
    
### 2. Automatization of the daily reporting:
    - Creating the bot in Telegram.
    - Automatic report sending to the bot and creating schedule time to send message.  
    - Automatization in Gitlab CI/CD.
    - Storage the token of the bot in the secret.
    files:auto_report_HW1.py, auto_report_HW2.py


### 3. Anomaly detection
    - Anomaly detection by statistical methods (sigma laws, IQR).
    - Creating auto-checking the anomalies scrypt.      
    - Sending the alert message to the chat in telegram in case of detection the anomaly.
    file:anomaly_detector.py


### 4. A/B tests
    - Creating the splitting system for A/B tests.  
    - A/A testing.   AA_test_3_4.ipynb
    - Time and sample size for the A/B experiments. 
    files: AA_test_3_4.ipynb, AB_test_CTR_0_1-Copy1.ipynb, A_B_test_analysis.ipynb
    
    
___

## Details
There were two databases:
1. news_feed db
2. messenger db

The ![news_feed db](news_feed_operational_data.jpg)


