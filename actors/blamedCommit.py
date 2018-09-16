import logging
from datetime import timedelta
from time import clock

from szzBlameCommits import Blamer
from gitutils.api_tokens import Tokens
from queue import Queue


logger = logging.getLogger('SZZ')

projects = []
with open ('/data2/adithya/szz/control-group.txt','r') as f:
    for line in f.readlines():
        projects.append(line.strip())

class BlamedCommitAnalyzer:
    @staticmethod
    def run_analysis(id_slug_folder):
        repo_id, slug, repos_folder = id_slug_folder
        if(slug not in projects):
            return
        logger.info(msg='Starting analysis of blamed commits from repo {0}.'.format(slug))
        start = clock()
        tokens = Tokens()
        tokens_iter = tokens.iterator()
        tokens_queue = Queue()
        for token in tokens_iter:
            tokens_queue.put(token)
        tokens_map = dict()

        b = Blamer(tokens, tokens_queue, tokens_map)
        b.get_blamed_commits(db_repo_id = repo_id, slug = slug, repos_folder = repos_folder)
        
        
        end = clock()
        logger.info(msg='Blaming of repo {0} commits completed in {1}.'.format(slug, timedelta(seconds=end - start)))
