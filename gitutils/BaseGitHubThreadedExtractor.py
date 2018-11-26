import datetime
import threading
from math import ceil
from time import sleep

import wrapt
from github import Github

import sys

sys.path.append("/data2/adithya/szz")

import loggingcfg
logger = loggingcfg.initialize_logger('SZZ')


# see http://wrapt.readthedocs.io/en/latest/examples.html#thread-synchronization
@wrapt.decorator
def synchronized(wrapped, instance, args, kwargs):
    # Use the instance as the context if function was bound.

    if instance is not None:
        context = vars(instance)
    else:
        context = vars(wrapped)

    # Retrieve the lock for the specific context.
    lock = context.get('_synchronized_lock', None)

    if lock is None:
        # There was no lock yet associated with the function so we
        # create one and associate it with the wrapped function.
        # We use ``dict.setdefault()`` as a means of ensuring that
        # only one thread gets to set the lock if multiple threads
        # do this at the same time. This may mean redundant lock
        # instances will get thrown away if there is a race to set
        # it, but all threads would still get back the same one lock.

        lock = context.setdefault('_synchronized_lock',
                                  threading.RLock())

    with lock:
        return wrapped(*args, **kwargs)


class BaseGitHubThreadedExtractor(object):
    tokens = None
    tokens_queue = None
    tokens_map = None
    seen = None

    def __init__(self, _tokens, t_queue, t_map):
        self.tokens = _tokens
        self.tokens_queue = t_queue
        self.tokens_map = t_map
        self.seen = dict()

    def initialize(self):
        pass

    def reserve_token(self, tid):
        token = self.tokens_queue.get()
        self.tokens_map[tid] = token
        return token

    def release_token(self, tid, token):
        if self.tokens_map[tid] == token:
            self.tokens_queue.put(token)
            self.tokens_map.pop(tid)

    @staticmethod
    def get_rate_limit(g):
        core = g.get_rate_limit().raw_data['resources']['core']
        return core['remaining'], core['limit']

    @staticmethod
    def compute_sleep_duration(g):
        reset_time = datetime.datetime.fromtimestamp(g.rate_limiting_resettime)
        curr_time = datetime.datetime.now()
        return abs(int(ceil((reset_time - curr_time).total_seconds())))

    @synchronized
    def wait_if_depleted(self, pid, g):
        (remaining, _limit) = BaseGitHubThreadedExtractor.get_rate_limit(g)
        #print(remaining, _limit)
        sleep_duration = BaseGitHubThreadedExtractor.compute_sleep_duration(g)
        if not remaining > 5:
                logger.info(
                   "[tid: {0}] Process depleted, going to sleep for {1} min.".format(pid, int(sleep_duration / 60)))
                sleep(sleep_duration)


if __name__ == '__main__':
    from gitutils.api_tokens import Tokens
    tokens = Tokens().iterator()
    print("Token\t\t\t\t\t\t\t\t\tLimit\tRemaining")
    for t in tokens:
        g = Github(t)
        remaining, limit = BaseGitHubThreadedExtractor.get_rate_limit(g)
        print("{0}\t{1}\t{2}".format(t, limit, remaining))

