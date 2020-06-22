# Reddit-Purge
Simple python script using praw API to mass delete reddit submissions and/or comments. Supports multiprocessing and redacts your messages (edit to something else) before deletion to prevent archiving. Requires only [praw](https://praw.readthedocs.io/en/latest/) and Python 3.5+ (runs on Windows/macOS/Linux).

# Installation

1. `git clone https://github.com/jogerj/reddit-purge.git`
2. `cd reddit-purge`
3. `pip -r install requirements`
4. Configure `run.py` (see below)

# Getting API keys

1. Goto [User Settings > Privacy & Security > App Authorization > 'Create App'](https://old.reddit.com/prefs/apps/) ([Preview](https://user-images.githubusercontent.com/30559735/85273407-da069e80-b47d-11ea-93ba-02fe69e2016f.png))
2. Enter any name for your script (default = `PurgeBot`)
3. Set type to `script`
4. Enter `http://localhost:8080` as redirect url. (You can leave the rest blank)
5. Click Create

Use the script name, 14 chars client ID, and 27 chars key you're shown, enter them in `run.py`.
![image](https://user-images.githubusercontent.com/30559735/85273897-7df04a00-b47e-11ea-8b35-0e827d3d0cec.png)
```
username = 'username'
password = 'password'
user_agent = 'PurgeBot'
client_id = 'CLIENTIDq00zTA'
client_secret = 'SECRETswQ_r0u7KlVojc4SECRET'
```
<sup>**Disclaimer**: Configuration above is only an example. You will need to setup your own configuration!</sup>
# Usage
Run with `python3 run.py`

# Purge options
| Options                                             | Description                                                                                                                                      |
|-----------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------|
| `limitation = None`                                 | Number of recent comments/submissions to delete. Set to None if no limits (purge ALL comments/submissions). Set to 10 will purge recent 10, etc. |
| `purge_comments = True`  `purge_submissions = True` | Set to False to not purge comments/submissions.                                                                                                  |
| `redact_msg = "[redacted]"`                         | Edit comments/submissions to this before deletion. This prevents archiving.                                                                      |
| `redact_only = False`                               | Set to True to only edit posts to `redact_msg` without deleting them.                                                                            |
| `use_multiprocessing = True`                        | Use multiprocessing. Set to False if problems occur                                                                                              |
| `show_comment = True`                               | Show comment body                                                                                                                                |
| `show_title = True`                                 | Show submission titles                                                                                                                           |
| `controversial_first = True`                        | Start purge from controversial first instead of newest                                                                                           |
# To-Do
* Add whitelisting
* Use `.cfg` file
* Better logging

# More info
* [Request your reddit data](https://www.reddit.com/settings/data-request) (if you want to backup before deletion)
* [pip installation](https://pip.pypa.io/en/stable/installing/)
* [praw](https://praw.readthedocs.io/en/latest/)
* Original code based on [this post in r/learnpython](https://www.reddit.com/r/learnpython/comments/aoq9yj/reddit_script_to_delete_all_comments_and/)
