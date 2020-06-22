# Reddit-Purge
Simple python script using praw API to mass delete reddit submissions and/or comments. Support multiprocessing

# Installation

1. `git clone https://github.com/jogerj/reddit-purge.git`
2. `cd reddit-purge`
3. `pip -r install requirements`
4. Configure `purge_reddit.py`

# Usage
Run with `python3 purge_reddit.py`

# Getting API keys

1. Goto [User Settings > Privacy & Security > App Authorization > 'Create App'](https://old.reddit.com/prefs/apps/) ([Preview](https://user-images.githubusercontent.com/30559735/85273407-da069e80-b47d-11ea-93ba-02fe69e2016f.png))
2. Enter any name for your script (default = `PurgeBot`)
3. Set type to `script`
4. Enter `http://localhost:8080` as redirect url. (You can leave the rest blank)
5. Click Create

Use the script name, 14 chars client ID, and 27 chars key you're shown, enter them in `purge_reddit.py`.
![image](https://user-images.githubusercontent.com/30559735/85273897-7df04a00-b47e-11ea-8b35-0e827d3d0cec.png)
```
username = 'username'
password = 'password'
user_agent = 'PurgeBot'
client_id = 'CLIENTIDq00zTA'
client_secret = 'SECRETswQ_r0u7KlVojc4SECRET'
```

# To-Do
* Add whitelisting
* Use `.cfg` file
* Better logging
