#!/usr/bin/env python3
import multiprocessing as mp
from time import sleep
import praw

# from praw.exceptions import RedditAPIException

#### EDIT YOUR DETAILS  BELOW ####

# Your login details
username = 'username'
password = 'password'
# Your app details
user_agent = 'PurgeBot'  # Bot name
client_id = '##############'  # '14 alphanumeric client ID'
client_secret = '###########################'  # '27 alphanumeric client secret'

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
## Set to True to only edit posts to 'redact_msg' without deleting them.
redact_only = False

#### DO NOT EDIT BELOW ####
# Init
reddit = praw.Reddit(
    client_id=client_id,
    client_secret=client_secret,
    user_agent=user_agent,
    username=username,
    password=password)
reddit.validate_on_submit = True


def get_comment_total():
    """
    Counts how many comments were made by 'username'.

    :return:
        int: number of comments
    """
    count = 0
    for c in reddit.redditor(username).comments.new(limit=limitation):
        count += 1
    return count


def get_submission_total() -> int:
    """
    Counts how many submissions were made by 'username'.

    :return:
        int: number of submissions
    """
    count = 0
    for s in reddit.redditor(username).submissions.new(limit=limitation):
        count += 1
    return count


def purge_comments(count: int = None, return_queue: mp.Queue = None):
    """
    Purge comments made by 'username'. If a comment could not be purged,
    it will be added to the list of skipped comments.

    :param count: Number of comments to purge, if unspecified then all.
    :param return_queue: Multiprocessing Queue to put list of skipped comments,
    if not specified then unused.
    :return: List of skipped comments ID in str.
    """
    if count is None:
        count = get_comment_total()
    print(f"Purging {count} comments...")
    skipped = list()
    while count > 0:
        for comment in reddit.redditor(username).comments.new(
                limit=limitation):
            try:
                comment_to_delete = reddit.comment(comment)
                comment_to_delete.edit(redact_msg)
                msg = f"Comment {comment} redacted"
                if not redact_only:
                    comment_to_delete.delete()
                    msg += " and deleted"
                count -= 1
                msg += f". {count} to go."
                print(msg)
            except Exception as exc:
                print(f"Failed to purge comment {comment}: ", exc)
                skipped.append(f"{comment}")
    if return_queue is not None:
        return_queue.put(skipped)
    return skipped


def purge_submissions(count: int = None, return_queue: mp.Queue = None):
    """
    Purge submissions made by 'username'. If a submission could not be purged,
    it will be added to the list of skipped submissions. If running on
    redact-only mode, only image/video/link submissions will be skipped.

    :param count: Number of submissions to purge, if unspecified then all.
    :param return_queue: Multiprocessing Queue to put list of skipped
    submissions, if unspecified then unused.
    :return: List of skipped submissions ID in str.
    """
    if count is None:
        count = get_submission_total()
    print(f"Purging {count} submissions...")
    skipped = list()
    while count > 0:
        for submission in reddit.redditor(username).submissions.new(
                limit=limitation):
            try:
                submission_to_delete = reddit.submission(submission)
                msg = f"Submission {submission}"
                # selftext == '' if post is image/link
                if submission.selftext != '':
                    submission_to_delete.edit(redact_msg)
                    msg += " redacted"
                elif redact_only:
                    # not redacted/deleted
                    skipped.append(f'{submission}')
                    msg += " skipped"
                if not redact_only:
                    submission_to_delete.delete()
                    msg += " and deleted"
                count -= 1
                msg += f". {count} to go."
                print(msg)
            except Exception as exc:
                print(f"Failed to purge submission {submission}: ", exc)
                skipped.append(f'{submission}')
    if return_queue is not None:
        return_queue.put(skipped)
    return skipped


if __name__ == '__main__':
    # Check total to purge and confirm
    if purge_comments:
        print("Calculating number of comments, please wait...")
        comment_count = get_comment_total()
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
        submission_count = get_submission_total()
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

    # Init multiprocessing and start each thread
    skipped_comments_queue = mp.Queue()
    skipped_submissions_queue = mp.Queue()
    if purge_comments:
        p1 = mp.Process(target=purge_comments,
                        args=(comment_count, skipped_comments_queue,))
        p1.start()
        sleep(1)  # delay to avoid errors
    if purge_submissions:
        p2 = mp.Process(target=purge_submissions,
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
            print(f"Comments not purged:\n{skipped_comments}")
        else:
            print("All comments purged!")
    if purge_submissions:
        skipped_submissions = skipped_submissions_queue.get()
        p2.join()
        if len(skipped_submissions) > 0:
            print(f"Submissions not purged:\n{skipped_submissions}")
        else:
            print("All submissions purged!")

    print("All processes completed!")
