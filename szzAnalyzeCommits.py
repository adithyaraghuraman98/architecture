import itertools
import re
import traceback

import pygit2
from sqlalchemy import and_, func
from sqlalchemy.orm import exc

from activityclassifier import BasicFileTypeClassifier
from orm import Commit, User, Repo, GhIssue, IssueLink, CommitFiles
from orm.initdb import SessionWrapper
from szzUtils import *

logger = logging.getLogger('SZZ')


def get_commits(slug, repos_folder):
    contributors = {}
    counter = itertools.count(start=1)
    basic_classifier = BasicFileTypeClassifier()

    session = SessionWrapper.new()

    try:
        folder_name = slugToFolderName(slug)
        folder_path = os.path.join(repos_folder, folder_name)

        min_commit = datetime.now(timezone.utc)
        max_commit = min_commit - timedelta(days=100 * 365)
        total_commits = 0

        if not os.path.exists(folder_path):
            return slug

        try:
            db_repo = session.query(Repo).filter_by(slug=slug).one()
            # the reason why we return here is to skip analyzing
            # again a repo in case of crashing exception that forces
            # the script to be run again
            logger.info(msg="Skipping analysis of commits from %s, already in the db" % slug)
            #return slug
        except exc.NoResultFound:
            db_repo = Repo(slug,
                           min_commit,
                           max_commit,
                           total_commits)
            session.add(db_repo)
            session.commit()
        except exc.MultipleResultsFound:
            logger.warning(msg="Found multiple results querying for repo %s." % slug)
            pass

        git_repo = pygit2.Repository(folder_path)

        last = git_repo[git_repo.head.target]

        # Fetch all commits as an iterator, and iterate it
        for c in git_repo.walk(last.id, pygit2.GIT_SORT_TIME):
            commit = CommitWrapper(c)

            total_commits += 1

            sha = commit.getSha()

            authored_datetime = commit.getAuthoredDate()
            committed_datetime = commit.getCommittedDate()

            if authored_datetime < min_commit:
                min_commit = authored_datetime
            if authored_datetime > max_commit:
                max_commit = authored_datetime

            (author_name, author_email) = commit.getAuthor()
            (author_name_l, author_email_l) = (author_name.lower(), author_email.lower())
            (committer_name, committer_email) = commit.getCommitter()
            (committer_name_l, committer_email_l) = (committer_name.lower(), committer_email.lower())

            if (author_name_l, author_email_l) not in contributors:
                contributors[(author_name_l, author_email_l)] = next(counter)
            author_id = contributors[(author_name_l, author_email_l)]

            if (committer_name_l, committer_email_l) not in contributors:
                contributors[(committer_name_l, committer_email_l)] = next(counter)
            committer_id = contributors[(committer_name_l, committer_email_l)]

            parents = commit.getParents()
            num_parents = len(parents)
            if not num_parents:
                continue

            message = commit.getMessage().strip()

            try:
                db_commit = session.query(Commit).filter_by(repo_id = db_repo.id,sha=sha).one()
                continue  # if already present, stop and go on analyzing the next one
            except exc.NoResultFound:
                diff = commit.getDiff(git_repo)
                loc_added = diff.stats.insertions
                loc_deleted = diff.stats.deletions
                num_files_touched = diff.stats.files_changed

                # get info about changes to src files in the new  commit
                all_files, src_files, num_src_files_touched, src_loc_added, src_loc_deleted = \
                    CommitWrapper.get_src_changes(basic_classifier, diff)
                try:
                    db_commit = Commit(db_repo.id,
                                       sha,
                                       authored_datetime,
                                       author_id,
                                       committer_id,
                                       message,
                                       num_parents,
                                       loc_added,
                                       loc_deleted,
                                       num_files_touched,
                                       all_files,
                                       src_loc_added,
                                       src_loc_deleted,
                                       num_src_files_touched,
                                       src_files)
                    session.add(db_commit)
                # required to flush the pending data before adding to the CommitFiles table below
                    session.commit()
                
                except:
                    all_files = ""
                    src_files = ""
                    message = ""
                    db_commit = Commit(db_repo.id,
                                       sha,
                                       authored_datetime,
                                       author_id,
                                       committer_id,
                                       message,
                                       num_parents,
                                       loc_added,
                                       loc_deleted,
                                       num_files_touched,
                                       all_files,
                                       src_loc_added,
                                       src_loc_deleted,
                                       num_src_files_touched,
                                       src_files)
                    session.add(db_commit)
                # required to flush the pending data before adding to the CommitFiles table below
                    session.commit()

                # parse changed files per diff
                for patch in diff:
                    commit_file = os.path.basename(patch.delta.new_file.path)
                    try:
                        commit_file = session.query(CommitFiles).filter_by(commit_sha=sha, repo_slug=slug,
                                                                           file=commit_file).one()
                        continue  # if already present, stop and go on analyzing the next one
                    except exc.NoResultFound:
                        lang = basic_classifier.labelFile(commit_file)
                        loc_ins = 0
                        loc_del = 0
                        for hunk in patch.hunks:
                            for hl in hunk.lines:
                                if hl.origin == '-':
                                    loc_del -= 1
                                elif hl.origin == '+':
                                    loc_ins += 1
                        commit_file = CommitFiles(db_repo.id, db_repo.slug, sha, commit_file, loc_ins, loc_del, lang)
                        session.add(commit_file)

                session.commit()

            if message is not None:
                issue_id_results = commit.getIssueIds()

                if len(issue_id_results) >= 1:
                    num_valid_issues = 0

                    for (line_num, issue_ids) in issue_id_results:

                        for issue_id in issue_ids:
                            logger.info(msg="Analyzing {0} issue {1}.".format(slug, issue_id))
                            try:
                                gh_issue = session.query(GhIssue).filter(and_(GhIssue.slug == slug,
                                                                              GhIssue.issue_number == issue_id)).one()
                            except exc.MultipleResultsFound:
                                logger.warning(msg="{0}: Issue {1} has multiple entries.".format(slug, issue_id))
                                continue
                            except exc.NoResultFound:
                                logger.warning(
                                    msg="{0}: Issue {1} no entry found in the issue table.".format(slug, issue_id))
                                continue

                            try:
                                db_link = session.query(IssueLink).filter(and_(IssueLink.repo_id == db_repo.id,
                                                                               IssueLink.sha == sha,
                                                                               IssueLink.issue_number == issue_id)).one()
                                print(db_repo.id, "Touch")
                                continue
                            except exc.NoResultFound:
                                delta_open = (
                                        authored_datetime - gh_issue.created_at.replace(
                                    tzinfo=pytz.utc)).total_seconds()

                                if gh_issue.closed_at is not None:
                                    delta_closed = (
                                            authored_datetime - gh_issue.closed_at.replace(
                                        tzinfo=pytz.utc)).total_seconds()

                                    if delta_open > 0 and delta_closed <= 0 and gh_issue.pr_num is None:
                                        num_valid_issues += 1
                                else:
                                    delta_closed = None

                                db_link = IssueLink(db_repo.id,
                                                    sha,
                                                    line_num,
                                                    issue_id,
                                                    gh_issue.pr_num is not None,
                                                    delta_open,
                                                    delta_closed)
                                session.add(db_link)

        for (name, email), user_id in sorted(contributors.items(), key=lambda e: e[1]):
            try:
                db_user = session.query(User).filter(and_(User.name == func.binary(name),
                                                          User.email == func.binary(email),
                                                          User.repo_id == db_repo.id)).one()
            except exc.NoResultFound:
                db_user = User(db_repo.id, user_id, name, email)
                session.add(db_user)
            except exc.MultipleResultsFound:
                # Would this happens because we allow name aliases during mining?
                # Should we deal with it? And how?
                logger.warning(
                    msg="Multiple entries for user \'{0}\' <{1}> in repo {2}".format(name, email, db_repo.slug))

        db_repo.min_commit = min_commit
        db_repo.max_commit = max_commit
        db_repo.total_commits = total_commits
        session.add(db_repo)

        session.commit()

        return slug

    except Exception as e:
        logger.error(msg="{0}: unknown error:\t{1}".format(slug, e))
        traceback.print_exc()
    finally:
        return slug


def main():
    import sys
    # create a new session and init db tables
    session = SessionWrapper.new(init=True)
    repos = session.query(GhIssue.slug).distinct()

    for r in repos:
        get_commits(r.slug, sys.argv[1])


if __name__ == '__main__':
    main()

