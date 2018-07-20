import logging
from datetime import timedelta
from time import clock

import szzBlameCommits as BlameAnalyzer

logger = logging.getLogger('SZZ')


class BlamedCommitAnalyzer:
    @staticmethod
    def run_analysis(id_slug_folder):
        repo_id, slug, repos_folder = id_slug_folder
        logger.info(msg='Starting analysis of blamed commits from repo {0}.'.format(slug))

        start = clock()
        BlameAnalyzer.get_blamed_commits(slug, repo_id, repos_folder)
        end = clock()
        logger.info(msg='Blaming of repo {0} commits completed in {1}.'.format(slug, timedelta(seconds=end - start)))
