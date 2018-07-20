import getopt
import os
import sys
import time
from concurrent import futures
from datetime import timedelta
from glob import glob

from sqlalchemy import and_

from actors import commit, blamedCommit
from loggingcfg import initialize_logger
from orm.initdb import SessionWrapper
from orm.tables import IssueLink, Repo


class SZZ:
    @staticmethod
    def start(argv):
        analyze_commits = False
        blame_commits = False
        repos_folder = None
        engine = 'multitasking'
        max_workers = 16

        try:
            opts, args = getopt.getopt(argv, "hr:e:t:ab",
                                       ["repos=", "engine=", "thread=", "analyze", "blame", "help"])
        except getopt.GetoptError as err:
            # print help information and exit:
            print(err)  # will print something like "option -a not recognized"
            print(
                'Usage:\n szz.py -r|--repos=<path> -a|--analyze|-b|--blame [-e|--engine=<name>, -t|--thread]')
            sys.exit(2)
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print('Usage:\n szz.py -r|--repos=<path> -a|--analyze|-b|--blame [-e|--engine=<name>, -t|--thread]')
                sys.exit(0)
            elif opt in ("-a", "--analyze"):
                analyze_commits = True
            elif opt in ("-b", "--blame"):
                blame_commits = True
            elif opt in ("-t", "--thread"):
                max_workers = int(arg)
            elif opt in ("-r", "--repos"):
                repos_folder = os.path.abspath(arg)
                if not os.path.exists(repos_folder):
                    logger.error(msg="Folder '%s' does not exist." % repos_folder)
                    sys.exit(3)
            elif opt in ("-e", "--engine"):
                # TODO unused for now - ie, can't change db name
                engine = arg
                logger.warning("Argument  -e|--engine currently unimplemented.")
            else:
                assert False, "unhandled option"

        # create a new session and init db tables
        session = SessionWrapper.new(init=True)

        n = 0
        start = time.time()

        if analyze_commits:
            logger.info("Retrieving repo list from %s" % repos_folder)
            depth1 = glob('{0}{1}*'.format(repos_folder, os.path.sep))
            slugs = list(filter(lambda f: os.path.isdir(f), depth1))
            # slugs = session.query(GhIssue.slug).distinct()
            logger.info("%s retrieved" % len(slugs))
            repos = [(slug.split(repos_folder)[1], repos_folder) for slug in slugs]
            with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                executor.map(commit.CommitAnalyzer.run_analysis, sorted(repos))

        if blame_commits:
            logger.info(
                "Retrieving from the database repos that have valid issues referring to alleged bug-fixing commits")
            repos = session.query(IssueLink.repo_id, Repo.slug).filter(
                and_(IssueLink.repo_id == Repo.id, IssueLink.is_pr == 0, IssueLink.delta_open > 0,
                     IssueLink.delta_closed <= 0)).distinct().all()
            logger.info("%s retrieved" % len(repos))
            repos = [(repo_id, slug, repos_folder) for (repo_id, slug) in repos]
            with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                executor.map(blamedCommit.BlamedCommitAnalyzer.run_analysis, sorted(repos))

        end = time.time()
        logger.info(msg="Time taken: %s" % timedelta(seconds=end - start))


if __name__ == '__main__':
    logger = initialize_logger(name='SZZ')

    try:
        SZZ.start(sys.argv[1:])
    except KeyboardInterrupt:
        logger.error("Received Ctrl-C or another break signal. Exiting.")
