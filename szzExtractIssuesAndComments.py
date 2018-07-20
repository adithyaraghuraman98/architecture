import getopt
import logging
import os
import socket
import sys
import threading
import traceback
from concurrent import futures
from queue import Queue

from _mysql_exceptions import IntegrityError
from github import Github
from github.GithubException import *

from csvmanager import CsvWriter, CsvReader
from gitutils.BaseGitHubThreadedExtractor import BaseGitHubThreadedExtractor
from gitutils.api_tokens import Tokens
from loggingcfg import initialize_logger
from orm import SessionWrapper
from orm.ghissue import GhIssue
from orm.issue_comments import IssueComment


class IssueAndCommentExtractor(BaseGitHubThreadedExtractor):
    @staticmethod
    def parse_issue(issue):
        issue_id = issue.id  # int
        issue_number = issue.number  # int
        state = issue.state  # string
        created_at = str(issue.created_at)  # datetime
        closed_at = str(issue.closed_at)  # datetime

        created_by = issue.user  # NamedUser
        created_by_login = None
        if created_by is not None:
            created_by_login = created_by.login

        closed_by = issue.closed_by  # NamedUser
        closed_by_login = None
        if closed_by is not None:
            closed_by_login = closed_by.login

        assignee = issue.assignee  # NamedUser
        assignee_login = None
        if assignee is not None:
            assignee_login = assignee.login

        title = issue.title.strip().replace("\n", "").replace("\r", "")  # string
        num_comments = issue.comments  # int
        labels = ','.join([l.name for l in issue.labels])  # [Label]

        pull_request = issue.pull_request  # IssuePullRequest
        pr_num = None
        if pull_request is not None:
            pr_html_url = pull_request.html_url
            pr_num = pr_html_url.split('/')[-1]

        metadata = [issue_id,
                    issue_number,
                    state,
                    created_at,
                    closed_at,
                    created_by_login,
                    closed_by_login,
                    assignee_login,
                    title,
                    num_comments,
                    labels,
                    pr_num]

        return metadata

    def parse_comments(self, pid, g, slug, issue):
        comments = list()

        comments_pglist = issue.get_comments()
        for comment in comments_pglist:
            comment_id = comment.id
            body = comment.body.strip()
            created_at = comment.created_at
            updated_at = comment.updated_at
            user_login = comment.user.login
            user_gh_id = comment.user.id
            comments.append(
                [slug, issue.id, issue.number, comment_id, body, created_at, updated_at, user_login, user_gh_id])

        if issue.pull_request is not None:  # is an actual issue:  # is a PR
            self.wait_if_depleted(pid, g)
            pr = issue.repository.get_pull(issue.number)

            self.wait_if_depleted(pid, g)
            comments_pglist = pr.get_review_comments()
            for comment in comments_pglist:
                comment_id = comment.id
                created_at = comment.created_at
                updated_at = comment.updated_at
                body = comment.body.strip()
                try:
                    user_login = comment.user.login
                    user_gh_id = comment.user.id
                    comments.append(
                        [slug, pr.id, pr.number, comment_id, body, created_at, updated_at, user_login, user_gh_id])
                except AttributeError:
                    logger.error("Skipped comment {0} in project {1} with None as user".format(comment_id, slug))
                    continue

        return comments

    def fetch_issues_comments(self, slug):
        pid = threading.get_ident()
        issues = list()
        comments = list()

        # if slug in self.seen:
        if slug in self.seen.keys():
            logging.info('[tid: {0}] Skipping {1}'.format(pid, slug))
            return slug, pid, None, issues, comments, 'Skipped'
        else:
            self.seen[slug] = True

        logger.info('[tid: {0}] Processing {1}'.format(pid, slug))

        try:
            _token = self.reserve_token(pid)
            g = Github(_token)
            # check rate limit before starting
            self.wait_if_depleted(pid, g)
            logger.info(msg="[tid: %s] Process not depleted, keep going." % pid)
            repo = g.get_repo(slug)

            if repo:  # and repo.has_issues: sometimes returns False even when there are some
                self.wait_if_depleted(pid, g)
                _issues = repo.get_issues(state=u'closed')
                for issue in _issues:
                    try:
                        logger.info(
                            msg='[tid: {0}] Fetching closed issue/pull-request {1} from {2}'.format(pid, issue.number,
                                                                                                    slug))
                        self.wait_if_depleted(pid, g)
                        metadata_issue = self.parse_issue(issue)
                        issues.append(metadata_issue)

                        self.wait_if_depleted(pid, g)
                        metadata_comments = self.parse_comments(pid, g, slug, issue)
                        if metadata_comments:
                            comments.append(metadata_comments)
                    except socket.timeout as ste:
                        logger.error("Socket timeout parsing issue %s" % issue, ste)
                    except RateLimitExceededException:
                        self.wait_if_depleted(pid, g)
                        continue
                    except GithubException as e:
                        traceback.print_exc(e)
                        continue

                self.wait_if_depleted(pid, g)
                _issues = repo.get_issues(state=u'open')
                for issue in _issues:
                    try:
                        logger.info(
                            msg='[tid: {0}] Fetching open issue/pull-request {1} from {2}'.format(pid, issue.number,
                                                                                                  slug))
                        self.wait_if_depleted(pid, g)
                        metadata = self.parse_issue(issue)
                        issues.append(metadata)

                        self.wait_if_depleted(pid, g)
                        metadata = self.parse_comments(pid, g, slug, issue)
                        if metadata:
                            comments.append(metadata)
                    except socket.timeout as ste:
                        logger.error("Socket timeout parsing issue %s" % issue, ste)
                        continue
                    except RateLimitExceededException:
                        self.wait_if_depleted(pid, g)
                        continue
                    except GithubException as e:
                        traceback.print_exc(e)
                        continue
        except BadCredentialsException:
            logger.warning("Repository %s seems to be private (raised 401 error)" % slug)
            return slug, pid, None, issues, comments, "%s seems to be private" % slug
        except UnknownObjectException:
            logger.warning("Repository %s cannot be found (raised 404 error)" % slug)
            return slug, pid, None, issues, comments, "%s not found" % slug
        except RateLimitExceededException as rle:
            return slug, pid, None, issues, comments, str(rle).strip().replace("\n", " ").replace("\r", " ")
        except GithubException as ghe:
            logger.warning("Error for repository %s, most likely there is no tab Issues in the repo" % slug)
            return slug, pid, None, issues, comments, str(ghe).strip().replace("\n", " ").replace("\r", " ")
        except Exception as e:
            traceback.print_exc(e)
            return slug, pid, None, issues, comments, str(e).strip().replace("\n", " ").replace("\r", " ")

        self.release_token(pid, _token)
        return slug, pid, _token, issues, comments, None

    def start(self, projects_f, issues_f, comments_f):
        # create a new session and init db tables
        session = SessionWrapper.new(init=True)
        for s in session.query(GhIssue.slug).distinct():
            self.seen[s] = True
        logger.info(msg="DB projects with issues: {0}".format(len(self.seen)))

        output_folder = os.path.abspath('./')
        log_writer = CsvWriter(os.path.join(output_folder, 'extracted-issues-error.log'), 'a')

        header = None
        f = os.path.join(output_folder, issues_f)
        if not os.path.exists(f):
            header = ['slug', 'issue_id', 'issue_number', 'state', 'created_at',
                      'closed_at', 'created_by_login', 'closed_by_login', 'assignee_login', 'title', 'num_comments',
                      'labels', 'pr_num']
        issue_writer = CsvWriter(f, 'w')
        if header:
            issue_writer.writerow(header)
        logger.debug("Opened issues file %s" % issues_f)

        header = None
        f = os.path.join(output_folder, comments_f)
        if not os.path.exists(f):
            header = ['slug', 'issue_id', 'issue_number', 'comment_id', 'body', 'created_at', 'updated_at',
                      'user_login', 'user_github_id']
        comment_writer = CsvWriter(f, 'w')
        if header:
            comment_writer.writerow(header)
        logger.debug("Opened comments file %s" % comments_f)

        projects = list()
        with open(projects_f, 'r') as infile:
            for line in infile:
                prj = line.strip()
                if prj.count('/') == 1:  # sanity check, some slugs have multiple '/'
                    projects.append(prj)

        #projects = ["nononononon/nonononononononon","roya3000/react-native-demo",
                    # "frankschmitt/flyway", "gm0t/angular.js"]
                    # ["bateman/dynkaas", "bateman/filebotology", "fujimura/git-gsub", "rbrito/tunesviewer"]

        max_workers = min(len(projects), self.tokens.length())
        max_workers = max(max_workers, 1)

        with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = executor.map(self.fetch_issues_comments, sorted(projects))
            for result in results:
                (slug, pid, _token, issues, comments_list, error) = result
                if error is not None:
                    logging.error(msg=[slug, error])
                    log_writer.writerow([slug, error])
                elif comments_list:
                    logger.info("Saving issues to temp file")
                    for issue in issues:
                        logger.debug(msg="Adding issue {0} {1}".format([slug], issue))
                        issue_writer.writerow([slug] + issue)
                    logger.info("Saving comments to temp file")
                    for comments in comments_list:
                        for comment in comments:
                            logger.debug(msg="Adding issue/pull-request comment {0} {1}".format([slug], comment[1:]))
                            comment_writer.writerow([slug] + comment[1:])
                issue_writer.flush()
                comment_writer.flush()
                logger.info('Done processing %s.' % slug)

        logger.info("Closing temp files")
        log_writer.close()
        issue_writer.close()
        comment_writer.close()

    @staticmethod
    def add_to_db(issue_f, comments_f):
        # create a new session but don't init db tables
        session = SessionWrapper.new(init=False)

        old_issues = dict()
        logger.info(msg="Loading existing issues.... (it may take a while).")
        for issue_id in session.query(GhIssue.issue_id):
            old_issues[issue_id[0]] = True
        logger.info(msg="Issues already in the db: {0}".format(len(old_issues)))

        output_folder = os.path.abspath('./')
        issues = CsvReader(os.path.join(output_folder, issue_f), mode='r')

        idx = 0
        logger.info("Importing new issues into the database.")
        for issue in issues.readrows():
            if idx == 0:
                idx += 1
                continue  # skip header
            try:
                [slug, issue_id, issue_number, state, created_at, closed_at,
                 created_by_login, closed_by_login, assignee_login, title,
                 num_comments, labels, pr_num] = issue

                if assignee_login == 'None' or assignee_login == '':
                    assignee_login = None
                if pr_num == 'None' or pr_num == '':
                    pr_num = None

                if not int(issue_id) in old_issues:
                    gi = GhIssue(slug, int(issue_id), issue_number, state,
                                 created_at, closed_at, created_by_login,
                                 closed_by_login, assignee_login, title,
                                 num_comments, labels, pr_num)
                    logger.debug("Adding issue %s." % gi)
                    session.add(gi)
                    idx += 1

                if not idx % 1000:
                    try:
                        logger.info("Issues added so far: %s" % idx)
                        session.commit()
                    except IntegrityError:
                        # this shouldn't happen, unless the dupe is in the file, not the db
                        logger.error("Duplicate entry for comment %s" % issue_id)
                        continue
            except Exception as e:
                traceback.print_exc(e)
                logger.error(issue, e)
                continue

        session.commit()
        logger.info("New issues added to the database: %s" % str(idx - 1))

        old_comments = dict()
        logger.info(msg="Loading existing comments.... (it may take a while).")
        for comment_id in session.query(IssueComment.comment_id).all():
            old_comments[comment_id[0]] = True
        logger.info(msg="Comments already in the db: {0}".format(len(old_comments)))

        comments = CsvReader(os.path.join(output_folder, comments_f), mode='r')

        idx = 0
        logger.info("Importing new comments into the database.")
        for comment in comments.readrows():
            if idx == 0:
                idx += 1
                continue  # skip header
            try:
                [slug, issue_id, issue_number, comment_id, body, created_at, updated_at, user_login,
                 user_github_id] = comment
                # clean up utf from body
                # does this work???
                body = bytes(body, 'utf-8').decode('utf-8', 'ignore')

                if not int(comment_id) in old_comments:
                    c = IssueComment(comment_id, slug, issue_id, issue_number, created_at, updated_at, user_github_id,
                                     user_login, body)
                    logger.debug("Adding issue comment %s." % c)
                    session.add(c)
                    session.commit()
                    idx += 1

                if not idx % 1000:
                    try:
                        logger.info("Comments added so far: %s" % idx)
                        # session.commit()
                    except IntegrityError:
                        # this shouldn't happen, unless the dupe is in the file, not the db
                        logger.error("Duplicate entry for comment %s" % comment_id)
                        continue
            except Exception as e:
                traceback.print_exc(e)
                logger.error(comment, e)
                continue

        session.commit()
        logger.info("New comments added to the database: %s" % str(idx - 1))


if __name__ == '__main__':
    project_file = None
    issue_file = None
    comment_file = None
    into_db = False

    logger = initialize_logger(name="SZZ:ISSUES_COMMENTS")

    try:
        if not sys.argv[1:]:
            raise getopt.GetoptError('No arguments passed from the command line. See help instructions.')
        opts, args = getopt.getopt(sys.argv[1:], "hf:i:c:", ["from=", "issues=", "comments=", "help"])
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print(
                    'Usage:\n szzExtractIssuesAndComments.py -f|--from=<file> -i|--issues=<file> -c|--comments=<file>')
                sys.exit(0)
            elif opt in ("-f", "--from"):
                project_file = arg
                if not os.path.exists(project_file):
                    logging.error('%s does not exist.' % project_file)
            elif opt in ("-c", "--comments"):
                comment_file = arg
            elif opt in ("-i", "--issues"):
                issue_file = arg
            else:
                assert False, "unhandled option"
    except getopt.GetoptError as err:
        # print help information and exit:
        logger.error(err)  # will print something like "option -a not recognized"
        print('Usage:\n szzExtractIssuesAndComments.py -i|--issues=<file> -c|--comments=<file>')
        sys.exit(1)

    tokens = Tokens()
    tokens_iter = tokens.iterator()
    tokens_queue = Queue()
    for token in tokens_iter:
        tokens_queue.put(token)
    tokens_map = dict()

    try:
        extractor = IssueAndCommentExtractor(tokens, tokens_queue, tokens_map)
        logger.info("Beginning data extraction.")
        extractor.start(project_file, issue_file, comment_file)
        logger.info("Beginning data import into db.")
        extractor.add_to_db(issue_file, comment_file)
        logger.info("Done.")
        exit(0)
    except KeyboardInterrupt:
        logger.error("Received Ctrl-C or another break signal. Exiting.")
