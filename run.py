#!/usr/bin/env python3
import multiprocessing as mp
import praw
from purge_reddit import PurgeReddit
from time import sleep

#### EDIT YOUR DETAILS  BELOW ####

# Your login details

username = 'username'
password = 'password'
user_agent = 'PurgeBot'  # Bot name
client_id = '##############'  # '14 char client ID'
client_secret = '###########################'  # '27 char client secret'

# Purge options
## Number of recent comments/submissions to delete.
## Set to None if no limits (purge ALL comments/submissions)
## Set to 10 will purge recent 10, etc.
limitation = None
## Set to False to not purge comments/submissions
purge_comments = True
purge_submissions = True
## Edit comments/submissions to this before deletion. This prevents archiving.
redact_msg = "[redacted]"
## Set to True to only edit posts to `redact_msg` without deleting them.
redact_only = True
## Use multiprocessing. Set to False if problems occur
use_multiprocessing = True
## Show comment body
show_comment = True
## Show submission titles
show_title = True
## Start purge from controversial first instead of newest
controversial_first = True

#### DO NOT EDIT BELOW ####

# Init
reddit = praw.Reddit(
    client_id=client_id,
    client_secret=client_secret,
    user_agent=user_agent,
    username=username,
    password=password)
options = {'controversial_first': controversial_first,
           'limitation': limitation,
           'redact_msg': redact_msg,
           'redact_only': redact_only,
           'show_title': show_title,
           'show_comment': show_comment}
if __name__ == '__main__':
    # Check total to purge and confirm
    pr = PurgeReddit(reddit, options)
    if purge_comments:
        print("Calculating number of comments, please wait...")
        comment_count = pr.get_comment_total()
        if comment_count == 0:
            print("Found no comments to delete.")
            purge_comments = False
        else:
            confirm = input(f"{comment_count} comments will be "
                            + ("redacted" if redact_only else "deleted")
                            + ". Are you sure? (N/y) ")
            if not confirm.lower().startswith("y"):
                print("Comment purge aborted.")
                purge_comments = False
    if purge_submissions:
        print("Calculating number of submissions, please wait...")
        submission_count = pr.get_submission_total()
        if submission_count == 0:
            print("Found no submissions to delete.")
            purge_submissions = False
        else:
            confirm = input(f"{submission_count} submissions will be "
                            + ("redacted" if redact_only else "deleted")
                            + ". Are you sure? (N/y) ")
            if not confirm.lower().startswith("y"):
                print("Submission purge aborted.")
                purge_submissions = False

    if not (purge_submissions or purge_comments):
        print("Nothing to purge today. Have a nice day!")
        exit()

    if use_multiprocessing:
        # Init multiprocessing and start each thread
        skipped_comments_queue = mp.Queue()
        skipped_submissions_queue = mp.Queue()
        if purge_comments:
            p1 = mp.Process(target=pr.purge_comments,
                            args=(comment_count, skipped_comments_queue,))
            p1.start()
            sleep(1)  # delay to avoid errors
        if purge_submissions:
            p2 = mp.Process(target=pr.purge_submissions,
                            args=(submission_count, skipped_submissions_queue,))
            p2.start()

        # Check if finished
        while purge_comments:
            if p1.is_alive():
                sleep(1)
            else:
                break
        while purge_submissions:
            if p2.is_alive():
                sleep(1)
            else:
                break
        # Get skipped posts
        if purge_comments:
            skipped_comments = skipped_comments_queue.get()
            p1.join()
            if len(skipped_comments) > 0:
                skipped_id = list(map(lambda c: f"{c.submission}/{c}",
                                      skipped_comments))
                print(f"Comments not purged:\n", skipped_id)
            else:
                print("All comments purged!")
        if purge_submissions:
            skipped_submissions = skipped_submissions_queue.get()
            p2.join()
            if len(skipped_submissions) > 0:
                skipped_id = list(map(lambda s: s.id, skipped_submissions))
                print("Submissions not purged:\n", skipped_id)
            else:
                print("All submissions purged!")
    else:
        # Serial method
        serial_msg = ""
        if purge_comments:
            skipped_comments = pr.purge_comments(comment_count)
            if len(skipped_comments) > 0:
                skipped_id = list(map(lambda c: f"{c.submission}/{c}",
                                      skipped_comments))
                serial_msg += f"Comments not purged:\n{skipped_id}\n"
            else:
                serial_msg += "All comments purged!\n"
        if purge_submissions:
            skipped_submissions = pr.purge_submissions(submission_count)
            if len(skipped_submissions) > 0:
                skipped_id = list(map(lambda s: s.id, skipped_submissions))
                serial_msg += f"Submissions not purged:\n{skipped_id}"
            else:
                serial_msg += "All submissions purged!"
        print(serial_msg)
    print("Done!")
