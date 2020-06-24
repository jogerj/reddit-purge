#!/usr/bin/env python3
import multiprocessing as mp
import praw
import prawcore.exceptions
import refresh_token
from purge_reddit import PurgeReddit
import time

#### EDIT YOUR DETAILS  BELOW ####

# Your login details
username = ''  # optional
password = ''  # optional
user_agent = 'PurgeBot'  # Bot name
client_id = '##############'  # '14 char client ID'
client_secret = '###########################'  # '27 char client secret'

# Purge options
## Number of recent comments/submissions to delete.
## Set to None if no limits (purge ALL comments/submissions)
## Set to 10 will purge recent 10, etc.
limitation = None
## Only purge posts with score <= this number. Set to None if no threshold
max_score = None
## Set to False to not purge comments/submissions
purge_comments = True
purge_submissions = True
## Edit comments/submissions to this before deletion. This prevents archiving.
redact_msg = "[redacted]"
## Set to True to only edit posts to `redact_msg` without deleting them.
redact_only = False
## Use multiprocessing. Set to False if problems occur
use_multiprocessing = True
## Show comment body
show_comment = False
## Show submission titles
show_title = False
## Start purge from controversial first instead of newest
controversial_first = True
## Do not prompt at all. Use with EXTRA caution!
no_prompt = False
## Debug mode
debug = False

## Whitelist e.g.`['id1', 'id2', 'id3']`
comment_whitelist = []
submissions_whitelist = []

#### DO NOT EDIT BELOW ####

options = {'controversial_first': controversial_first,
           'debug': debug,
           'limitation': limitation,
           'redact_msg': redact_msg,
           'redact_only': redact_only,
           'max_score': max_score,
           'show_title': show_title,
           'show_comment': show_comment,
           'comment_whitelist': comment_whitelist,
           'submissions_whitelist': submissions_whitelist}


def save_log(log_type: str, entries: list):
    filename = f"log/{log_type} {time.asctime().replace(':', '.')}.log"
    try:
        f = open(filename, "w")
        for entry in entries:
            f.write(entry + '\n')
        f.close()
    except IOError:
        print(f"Could not write to {filename}")


if __name__ == '__main__':
    # Initialize reddit
    if password != '' and username != '':
        # use username and password
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
            username=username,
            password=password,
            redirect_uri="http://localhost:8080")
    else:
        # use OAuth
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
            redirect_uri="http://localhost:8080")
    # Check authentication key
    print("Checking authentication...")
    if client_id == '##############' \
            or client_secret == '###########################':
        print("Missing client ID/secret key!")
        exit()
    elif len(client_id) != 14 or len(client_secret) != 27:
        print("Failed to authenticate!",
              "Your client ID/secret key isn't the correct length.")
        print("Please check your configuration again!")
        exit()
    try:
        # Test authentication
        if reddit.user.me() is None:
            refresh_token.authorize_token(reddit)
    except prawcore.exceptions.ResponseException as exc:
        if f'{exc}'.find('401') != -1:
            # 401 error, invalid key ?
            print("ERROR 401: There's a problem with your authentication key."
                  + "\nPlease check your configuration again!")
        else:
            print("\nResponseException:", exc)
            if debug:
                raise exc
        exit()
    except prawcore.exceptions.OAuthException:
        print("Failed to authenticate credentials! Possible causes:")
        print("1. Wrong username/password.")
        print("2. 2FA is enabled.")
        print("3. Invalid client ID/secret key.")
        try:
            refresh_token.authorize_token(reddit)
        except refresh_token.TokenException as exc:
            print("TokenException:", exc)
            if debug:
                raise exc
            exit()
    except refresh_token.TokenException as exc:
        print("TokenException:", exc)
        print("Could not authorize token!")
        exit()
    # Authkey all good! Check total to purge and confirm
    pr = PurgeReddit(reddit, options)
    comment_count = 0
    submission_count = 0
    if purge_comments:
        print("Calculating number of comments, please wait...")
        comment_count = pr.get_comment_total()
        if comment_count == 0:
            print("Found no comments to delete.")
            purge_comments = False
        elif not no_prompt:
            confirm = input(f"{comment_count} comments will be "
                            + ("redacted" if redact_only else "deleted")
                            + ". Are you sure? [y/N] ")
            if not confirm.lower().startswith("y"):
                print("Comment purge aborted.")
                purge_comments = False
    if purge_submissions:
        print("Calculating number of submissions, please wait...")
        submission_count = pr.get_submission_total()
        if submission_count == 0:
            print("Found no submissions to delete.")
            purge_submissions = False
        elif not no_prompt:
            confirm = input(f"{submission_count} submissions will be "
                            + ("redacted" if redact_only else "deleted")
                            + ". Are you sure? [y/N] ")
            if not confirm.lower().startswith("y"):
                print("Submission purge aborted.")
                purge_submissions = False
    if not (purge_submissions or purge_comments):
        print("Nothing to purge today. Have a nice day!")
        exit()
    # Begin purge
    while True:
        if use_multiprocessing:
            # Init multiprocessing and start each thread
            skipped_comments_queue = mp.Queue()
            skipped_submissions_queue = mp.Queue()
            if purge_comments:
                p1 = mp.Process(target=pr.purge_comments,
                                args=(comment_count, skipped_comments_queue,))
                p1.start()
                time.sleep(2)  # delay to avoid errors
            if purge_submissions:
                p2 = mp.Process(target=pr.purge_submissions,
                                args=(submission_count,
                                      skipped_submissions_queue,))
                p2.start()
            # Get skipped posts
            if purge_comments:
                skipped_comments = skipped_comments_queue.get()
                p1.join()
                if len(skipped_comments) > 0:
                    skipped_id = list(map(
                        lambda c:
                        f"{c.submission}/{c} in {c.subreddit}",
                        skipped_comments))
                    print(f"Comments not purged:\n", skipped_id)
                    save_log('skipped_comments', skipped_id)
                else:
                    print("All comments purged!")
            if purge_submissions:
                skipped_submissions = skipped_submissions_queue.get()
                p2.join()
                if len(skipped_submissions) > 0:
                    skipped_id = list(map(lambda s: f'{s} in {s.subreddit}',
                                          skipped_submissions))
                    print("Submissions not purged:\n", skipped_id)
                    save_log('skipped_submissions', skipped_id)
                else:
                    print("All submissions purged!")
        else:
            # Serial method
            serial_msg = ""
            if purge_comments:
                skipped_comments = pr.purge_comments(comment_count)
                if len(skipped_comments) > 0:
                    skipped_id = list(map(
                        lambda c:
                        f"{c.submission}/{c} in {c.subreddit}",
                        skipped_comments))
                    serial_msg += f"Comments not purged:\n{skipped_id}"
                    save_log('skipped_comments', skipped_id)
                else:
                    serial_msg += "All comments purged!"
            if purge_submissions:
                skipped_submissions = pr.purge_submissions(submission_count)
                if len(skipped_submissions) > 0:
                    skipped_id = list(map(lambda s: f'{s} in {s.subreddit}',
                                          skipped_submissions))
                    serial_msg += f"Submissions not purged:\n{skipped_id}"
                    save_log('skipped_submissions', skipped_id)
                else:
                    serial_msg += "All submissions purged!"
            print(serial_msg)
        # if there were more than 1000, prompt to delete more
        if (submission_count >= 1000 or comment_count >= 1000) \
                and not redact_only:
            if not no_prompt:
                confirm = input("There were more than 1000 submissions/comments!",
                                "Delete more? [y/N] ")
            if no_prompt or confirm.lower().startswith('y'):
                if limitation is not None:
                    limitation -= 1000
                print("Calculating remaining submissions/comments...")
                if purge_comments:
                    comment_count = pr.get_comment_total()
                    print(f"{comment_count} remaining...")
                if purge_submissions:
                    submission_count = pr.get_submission_total()
                    print(f"{submission_count} remaining...")
        else:
            break
    print("Done!")
