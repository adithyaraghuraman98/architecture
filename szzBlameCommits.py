import itertools
import threading
import traceback
from queue import Queue

import pygit2
from github import Github
from sqlalchemy import and_
from sqlalchemy.orm import exc

from activityclassifier import BasicFileTypeClassifier
from gitutils.BaseGitHubThreadedExtractor import BaseGitHubThreadedExtractor
from gitutils.api_tokens import Tokens
from orm import Commit, Blame, User, IssueLink, Repo
from orm.initdb import SessionWrapper
from szzUtils import *

invalid_labels_file_path = 'invalid-issue-labels.txt'
valid_labels_file_path = 'valid-issue-labels.txt'


class Blamer(BaseGitHubThreadedExtractor):
    logger = logging.getLogger('SZZ')

    def __init__(self, _tokens, t_queue, t_map):
        super().__init__(_tokens, t_queue, t_map)
        with open(invalid_labels_file_path) as f:
            self.invalid_labels = f.read().splitlines()
        with open(valid_labels_file_path) as f:
            self.valid_labels = f.read().splitlines()

    def get_blamed_commits(self, db_repo_id, slug, repos_folder='./repos'):
        
        session = SessionWrapper.new()
        basic_classifier = BasicFileTypeClassifier()
        folder_path = os.path.join(repos_folder, slugToFolderName(slug))
        
        try:
            git_repo = pygit2.Repository(folder_path)
            last = git_repo[git_repo.head.target]
        except Exception:
            logger.error("Git error opening repo %s" % slug)
            return

        try:
            contributors = self.get_contributors(session, db_repo_id)
            # TODO check start number
            counter = itertools.count(start=len(contributors))
        except exc.NoResultFound:
            logger.error(msg="No contributors found for repo {0}.".format(slug))
            traceback.print_exc()
            pass

        repo, pid, gh = self.get_gh_repo(slug)

        blamed_commits = {}

        # Fetch all commits as an iterator, and iterate it
        for c in git_repo.walk(last.id, pygit2.GIT_SORT_TIME):
            commit = CommitWrapper(c)
            sha = commit.getSha()

            closes_valid_issue = False
            issue_links = session.query(IssueLink).filter(and_(IssueLink.repo_id == db_repo_id, IssueLink.sha == sha,
                                                               IssueLink.is_pr == 0, IssueLink.delta_open > 0,
                                                               IssueLink.delta_closed <= 0))
            """
            Valid issues are those 
            1) for which the associated commit was registered *after* the issue was open (delta open > 0)
            2) for which the associated commit was registered *before or exactly when* the associated issue was closed
               (delta closed <= 0)
            3) are not pull requests (is_pr == 1), just issues (is_pr == 0)              
            """
            for issue_link in issue_links:
                # check for possible labels: if 'feature' or 'enhancement', ignore
                # if no labels or labels are 'fix', 'bug-fix', retain
                self.wait_if_depleted(pid, gh)
                issue = repo.get_issue(issue_link.issue_number)
                if issue:
                    if not issue.labels:  # no labels is fine
                        closes_valid_issue = True
                        break
                    else:
                        for label in issue.labels:
                            if label.name in self.invalid_labels:
                                break
                            elif label.name in self.valid_labels:
                                closes_valid_issue = True
                                break

            if not closes_valid_issue:
                continue

            logger.info("Blaming commit %s from repo %s" % (sha, slug))
            try:
                sha_parent = commit.getParents()[0].hex
            except IndexError:
                continue

            diff = commit.getDiff(git_repo)

            for patch in diff:
                # skip changes to binary files
                if patch.delta.is_binary:
                    continue

                old_file = patch.delta.old_file.path
                label = basic_classifier.labelFile(old_file)

                # Ignore changes to documentation files
                if label == basic_classifier.DOC:
                    continue

                line_labels = {}
                blame_counter = {}

                for hunk in patch.hunks:
                    if hunk.old_lines:
                        for hl in hunk.lines:
                            """
                            only changes to deleted lines can be tracked back to when they were first introduced
                            there is no parent commit that introduced a new line that it's being added in the current
                            commit for the first time (ie, lines marked with a '+' in the diffs)
                            
                            this is not a basic SZZ implementation, as we classify changes at line level (e.g., skip changes
                            to line of comments)
                            """
                            if hl.origin == '-':
                                line_labels[hl.old_lineno] = basic_classifier.labelDiffLine(
                                    hl.content.replace('\r', '').replace('\n', ''))

                        try:
                            for bh in git_repo.blame(old_file,
                                                     newest_commit=sha_parent,
                                                     min_line=hunk.old_start,
                                                     max_line=hunk.old_start + hunk.old_lines - 1):
                                blamed_sha = str(bh.final_commit_id)

                                # if sha of commit is not already in the list of blamed commit
                                if blamed_sha not in blamed_commits:
                                    try:
                                        blamed_commit = CommitWrapper(git_repo.revparse_single(blamed_sha))

                                        blamed_commits[blamed_sha] = blamed_commit

                                        blamed_parents = blamed_commit.getParents()
                                        blamed_num_parents = len(blamed_parents)

                                        if not blamed_num_parents:
                                            ins = None
                                            dels = None
                                            num_files = None
                                        else:
                                            blamed_diff = blamed_commit.getDiff(git_repo)
                                            ins = blamed_diff.stats.insertions
                                            dels = blamed_diff.stats.deletions
                                            num_files = blamed_diff.stats.files_changed

                                        # TODO fine-tune: Ignore commits that changed more than 100 files
                                        if num_files is None or num_files >= 50:
                                            continue

                                        # TODO fine-tune: filter number of new lines (ins)
                                        if ins and ins >= 200:
                                            continue

                                        try:
                                            blamed_db_commit = session.query(Commit).filter_by(
                                                sha=blamed_sha).one()
                                        except exc.MultipleResultsFound:
                                            logger.warning(
                                                msg="{0}: Multiple rows for blamed sha {1}.".format(slug,
                                                                                                    blamed_sha))
                                            traceback.print_exc()
                                        except exc.NoResultFound:
                                            # TODO does it ever happen?
                                            logger.warning("exc.NoResultFound at line 141 of blame")
                                            blamed_authored_datetime = blamed_commit.getAuthoredDate()

                                            (blamed_author_name,
                                             blamed_author_email) = blamed_commit.getAuthor()
                                            (blamed_author_name_l, blamed_author_email_l) = (
                                                blamed_author_name.lower(), blamed_author_email.lower())

                                            (blamed_committer_name,
                                             blamed_committer_email) = blamed_commit.getCommitter()
                                            (blamed_committer_name_l, blamed_committer_email_l) = (
                                                blamed_committer_name.lower(), blamed_committer_email.lower())

                                            if (blamed_author_name_l,
                                                blamed_author_email_l) not in contributors:
                                                logger.debug(
                                                    msg="Found a blamed author {0} - {1} not in the contributors list for repo {2}.".format(
                                                        blamed_author_name_l, blamed_author_email_l, slug))
                                                # TODO what to do with newly added contributors here? save to db???
                                                contributors[
                                                    (blamed_author_name_l, blamed_author_email_l)] = next(
                                                    counter)
                                            blamed_author_id = contributors[
                                                (blamed_author_name_l, blamed_author_email_l)]

                                            if (blamed_committer_name_l,
                                                blamed_committer_email_l) not in contributors:
                                                logger.debug(
                                                    msg="Found a blamed author {0} - {1} not in the contributors list for repo {2}.".format(
                                                        blamed_committer_name_l, blamed_committer_email_l, slug))
                                                # TODO what to do with newly added contributors here? save to db???
                                                contributors[
                                                    (blamed_committer_name_l, blamed_committer_email_l)] = next(
                                                    counter)
                                            blamed_committer_id = contributors[
                                                (blamed_committer_name_l, blamed_committer_email_l)]

                                            blamed_message = blamed_commit.getMessage()
                                            blamed_first_msg_line = blamed_message.split('\n')[0]

                                            # get info about changes to src files in the new blamed commit
                                            all_files, src_files, num_src_files_touched, src_loc_added, src_loc_deleted = \
                                                CommitWrapper.get_src_changes(basic_classifier,
                                                                              blamed_commit.getDiff(git_repo))

                                            blamed_db_commit = Commit(db_repo_id,
                                                                      blamed_sha,
                                                                      blamed_authored_datetime,
                                                                      blamed_author_id,
                                                                      blamed_committer_id,
                                                                      blamed_first_msg_line,
                                                                      blamed_num_parents,
                                                                      ins,
                                                                      dels,
                                                                      num_files,
                                                                      all_files,
                                                                      src_loc_added,
                                                                      src_loc_deleted,
                                                                      num_src_files_touched,
                                                                      src_files)
                                            session.add(blamed_db_commit)
                                            session.commit()
                                    except Exception as e:
                                        logger.error(
                                            msg="{0}: revparse error {1}:\t{2}".format(slug, blamed_sha, e))
                                        traceback.print_exc()

                                for line_num in range(bh.final_start_line_number,
                                                      bh.final_start_line_number + bh.lines_in_hunk):
                                    if line_labels[line_num] == basic_classifier.CG_CODE:
                                        blame_counter.setdefault(blamed_sha, 0)
                                        blame_counter[blamed_sha] += 1
                        except ValueError as ve:
                            logger.error(
                                msg="{0} blame error on commit {1} probably due to changes coming from a submodule: {2}".
                                    format(slug, sha, ve))
                        except Exception as e:
                            logger.error(msg="{0} Unknown blame error on commit {1}: {2}".format(slug, sha, e))
                            traceback.print_exc()

                for blamed_sha, num_lines in blame_counter.items():
                    b = Blame(db_repo_id,
                              sha,
                              old_file,
                              label,
                              blamed_sha,
                              num_lines)
                    session.add(b)
                session.commit()

    def get_gh_repo(self, slug):
        pid = threading.get_ident()
        _token = self.reserve_token(pid)
        g = Github(_token)
        # check rate limit before starting
        self.wait_if_depleted(pid, g)
        logger.debug(msg="Process not depleted, keep going.")
        repo = g.get_repo(slug)
        return repo, pid, g

    @staticmethod
    def get_contributors(session, repo_id):
        return session.query(User).filter_by(repo_id=repo_id).all()


def main():
    session = SessionWrapper.new(init=True)
    # only repos for which there are valid issue links
    repos = session.query(IssueLink.repo_id, Repo.slug).filter(
        and_(IssueLink.repo_id == Repo.id, IssueLink.is_pr == 0, IssueLink.delta_open > 0,
             IssueLink.delta_closed <= 0)).distinct().all()

    tokens = Tokens()
    tokens_iter = tokens.iterator()
    tokens_queue = Queue()
    for token in tokens_iter:
        tokens_queue.put(token)
    tokens_map = dict()

    for r in repos:
        b = Blamer(tokens, tokens_queue, tokens_map)
        b.get_blamed_commits(r.repo_id, r.slug)


if __name__ == '__main__':
    main()
