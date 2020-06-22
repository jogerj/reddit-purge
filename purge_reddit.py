from multiprocessing import queues


class PurgeReddit:
    """
    A class that contains functions to purge reddit posts.

    =================== ===================================================
    Attribute           Description
    =================== ===================================================
    ``reddit``          An instance of :class:`praw.Reddit`, pre-initialized
                        with ``client_id``, ``client_secret``, ``user_agent``,
                        ``username``, and ``password`` attributes.
    ``options``         Dictionary of options with str as keys
    =================== ===================================================
    """

    def __init__(self, reddit, options):
        """
        Initializes :class:`PurgeReddit` instance

        :param reddit: initialized :class:`praw.Reddit` instance
        :param options: dictionary with options from config
        """
        reddit.validate_on_submit = True
        self._reddit = reddit
        self._options = options

    def get_comment_total(self):
        """
        Counts how many comments were made by 'username'.

        :return:
            int: number of comments
        """
        count = 0
        for c in self._reddit.redditor(
                self._reddit.config.username).comments.new(
                limit=self._options['limitation']):
            count += 1
        return count

    def get_submission_total(self):
        """
        Counts how many submissions were made by 'username'.

        :return:
            int: number of submissions
        """
        count = 0
        for s in self._reddit.redditor(
                self._reddit.config.username).submissions.new(
                limit=self._options['limitation']):
            count += 1
        return count

    def purge_comments(self, count: int = None, return_queue: queues = None):
        """
        Purge comments made by 'username'. If a comment could not be purged,
        it will be added to the list of skipped comments.

        :param count: Number of comments to purge, if unspecified then all.
        :param return_queue: Multiprocessing Queue to put list of skipped
        comments, if not specified then unused.
        :return: List of skipped comments.
        """
        # redditor = self._reddit.redditor(self._username)
        # limitation = self._limitation
        if count is None:
            count = self.get_comment_total()
        print(f"Purging {count} comments...")
        skipped = list()
        username = self._reddit.config.username
        comments = self._reddit.redditor(username).comments
        tries = 0
        if self._options['controversial_first']:
            posts = comments.controversial(limit=self._options['limitation'])
        else:
            posts = comments.new(limit=self._options['limitation'])
        while count > 0:
            for comment in posts:
                try:
                    comment.edit(self._options['redact_msg'])
                    if self._options['show_comment']:
                        msg = f"Comment {comment}: \"{comment.body[0:140]}\" redacted"
                    else:
                        msg = f"Comment {comment} redacted"
                    if not self._options['redact_only']:
                        comment.delete()
                        msg += " and deleted"
                    count -= 1
                    msg += f". {count} to go."
                    print(msg)
                except Exception as exc:
                    print(f"Failed to purge comment {comment}: ", exc)
                    skipped.append(comment)
                    count -= 1
            # retry skipped comments up to 3 times
            if count >= 1000 and len(skipped) > 0 and tries <= 3:
                print(f"Retrying {len(skipped)} skipped comments.")
                count += len(skipped)
                tries += 1
        if return_queue is not None:
            return_queue.put(skipped)
        return skipped

    def purge_submissions(self, count: int = None,
                          return_queue: queues = None):
        """
        Purge submissions made by 'username'. If a submission could not be
        purged, it will be added to the list of skipped submissions.
        If running on redact-only mode, only image/video/link submissions
        will be skipped.

        :param count: Number of submissions to purge, if unspecified then all.
        :param return_queue: Multiprocessing Queue to put list of skipped
        submissions, if unspecified then unused.
        :return: List of skipped submissions.
        """
        if count is None:
            count = self.get_submission_total()
        print(f"Purging {count} submissions...")
        skipped = list()
        username = self._reddit.config.username
        submissions = self._reddit.redditor(username).submissions
        tries = 0
        if self._options['controversial_first']:
            posts = submissions.new(limit=self._options['limitation'])
        else:
            posts = submissions.controversial(limit=self._options['limitation'])
        while count > 0:
            for submission in posts:
                try:
                    if self._options['show_title']:
                        msg = f"Submission {submission}: \"{submission.title[0:140]}\""
                    else:
                        msg = f"Submission {submission}"
                    # selftext == '' if post is image/link
                    if submission.selftext != '':
                        submission.edit(self._options['redact_msg'])
                        msg += " redacted"
                    elif self._options['redact_only']:
                        # not redacted/deleted
                        skipped.append(submission)
                        msg += " skipped"
                    if not self._options['redact_only']:
                        submission.delete()
                        msg += " and deleted"
                    count -= 1
                    msg += f". {count} to go."
                    print(msg)
                except Exception as exc:
                    print(f"Failed to purge submission {submission}: ", exc)
                    skipped.append(submission)
            # retry skipped submissions up to 3 times
            if count >= 1000 and len(skipped) > 0 and tries <= 3:
                print(f"Retrying {len(skipped)} skipped submissions.")
                count += len(skipped)
                tries += 1
        if return_queue is not None:
            return_queue.put(skipped)
        return skipped
