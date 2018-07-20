import datetime
import logging
import os
import pickle
import sys
import time
from time import strftime
from szzUtils import slugToFolderName, folderNameToSlug

from sqlalchemy.orm import exc

import loggingcfg
from activityclassifier import BasicFileTypeClassifier
from csvmanager import CsvWriter
from orm import SessionWrapper, Blame, Commit, User, Repo, IssueLink, CommitFiles

logger = logging.getLogger('SZZ')


def replace_alias(aliases, author_id):
    return aliases[author_id]


def parse_timestamp(date, time_unit):
    gb = None
    date_d1 = time.strptime('1990-01-01', "%Y-%m-%d")
    date_d2 = time.strptime(str(date).split(' ')[0], "%Y-%m-%d")

    year_d1 = int((strftime("%Y", date_d1)))
    year_d2 = int((strftime("%Y", date_d2)))

    if time_unit == 'week':
        week_d2 = int((strftime("%U", date_d2)))
        gb = ((year_d2 - year_d1) * 52) + week_d2
    elif time_unit == 'month':
        month_d2 = int((strftime("%m", date_d2)))
        gb = ((year_d2 - year_d1) * 12) + month_d2
    return gb


def daily_data_per_language(commits, lang, basic_classifier):
    src_files_for_lang = []
    num_src_file_touches_for_lang = 0
    for commit in commits:
        for file in commit[3].split(','):  # src files in the commit
            gl = basic_classifier.guess_languages([file])
            if lang == gl[file]:
                src_files_for_lang.append(file)
                num_src_file_touches_for_lang += 1

    num_src_files_touched_for_lang = len(set(src_files_for_lang))

    return num_src_file_touches_for_lang, num_src_files_touched_for_lang


def daily_data_per_project(commits_set):
    all_files = []
    src_files = []
    num_files_touches_per_day = 0
    num_src_files_touches_per_day = 0
    # num_files_touched_per_day = 0
    # num_src_files_touched_per_day = 0
    for commit in commits_set:
        if commit[3] != '':
            commit_files = commit[3].split(',')  # any files touched in commit
            all_files = all_files + commit_files
            num_files_touches_per_day += len(commit_files)
        if commit[4] != '':
            src_commit_files = commit[4].split(',')  # src files touched in commit
            src_files = src_files + src_commit_files
            num_src_files_touches_per_day += len(src_commit_files)
            # beware!
            # num_files_touched_per_day += commit[9]  # num_files_touched in commit != from  num_files_touched_per_day
            # num_src_files_touched_per_day += commit[10]  # num_src_files_touched in commit != from num_src_files_touched_per_day

    num_files_touched_per_day = len(set(all_files))
    num_src_files_touched_per_day = len(set(src_files))

    return num_files_touches_per_day, num_src_files_touches_per_day, num_files_touched_per_day, \
           num_src_files_touched_per_day


def export(argv, aliases, basic_classifier):
    prj_outfile = argv[0]
    lang_outfile = argv[1]

    session = SessionWrapper.new(init=False)
    logger.info("Connected to db")

    logger.info("Retrieving blamed shas of bug-inducing commits (to src files only).")
    blamed_commits = session.query(Blame.sha, Blame.blamed_sha, Repo.slug, Blame.repo_id, Commit.author_id,
                                   IssueLink.issue_number, Blame.num_blamed_lines) \
        .filter(Commit.sha == Blame.blamed_sha,
                Blame.sha == IssueLink.sha,
                Blame.type != BasicFileTypeClassifier.DOC,
                Blame.repo_id == Repo.id).all()

    logger.info("Retrieving the list of distinct authors of blamed commits (taking care of aliases too).")
    bugs_induced_per_sha = dict()
    for bc in blamed_commits:
        logger.debug("Retrieving developer who created commit with sha: %s" % bc.blamed_sha)
        try:
            u = session.query(User.id, User.email, User.name).filter_by(user_id=bc.author_id, repo_id=bc.repo_id).one()
        except exc.NoResultFound:
            logging.error("No user with id {0} found for repo {1}".format(bc.author_id, bc.repo_id))
            continue
        except exc.MultipleResultsFound:
            logging.error("Multiple entries found for user id {0} in repo {1}".format(bc.author_id, bc.repo_id))
            continue
        if u.email == 'noreply@github.com' and u.name == 'github':
            logger.info("Skipped user %s whose name and email values are GitHub's defaults." % u.id)
            continue
        aliased_uid = replace_alias(aliases, u.id)
        repo = folderNameToSlug(bc.slug)

        if (aliased_uid, bc.blamed_sha, repo) in bugs_induced_per_sha:
            bug_fixing_commits = bugs_induced_per_sha[(aliased_uid, bc.blamed_sha, repo)]
        else:
            bug_fixing_commits = dict()
        if bc.issue_number in bug_fixing_commits:
            bug_fixes = bug_fixing_commits[bc.issue_number]
        else:
            bug_fixes = list()
        bug_fixes.append(bc.sha)
        bug_fixing_commits[bc.issue_number] = bug_fixes
        bugs_induced_per_sha[(aliased_uid, bc.blamed_sha, repo)] = bug_fixing_commits

    logger.info("Parsing commits.")
    commits = session.query(Commit).all()
    commits_per_user = dict()
    dates = set()  # set of all commit dates
    langs = set()  # set of all progr languages used in commits
    repos = set()  # set of all repos
    for commit in commits:
        logger.debug("Parsing user %s from repo %s." % (commit.author_id, commit.repo_id))
        aliased_uid = replace_alias(aliases, commit.author_id)
        logger.debug("Replaced %s with alias %s." % (commit.author_id, aliased_uid))
        if aliased_uid in commits_per_user:
            commits_per_user_project, commits_per_user_language = commits_per_user[aliased_uid]
        else:
            commits_per_user_project = list()
            commits_per_user_language = list()

        # per-project metadata
        repo = session.query(Repo.slug).filter_by(id=commit.repo_id).one()
        repo = slugToFolderName(repo.slug)  # slug_transform(repo.slug)
        repos.add(repo)
        y_m_d = str(commit.timestamp_utc).split(' ')[0]
        dates.add(y_m_d)

        loc_added = commit.num_additions
        loc_deleted = commit.num_deletions
        num_files_touched = commit.num_files_changed
        files = commit.files

        src_loc_added = commit.src_loc_added
        src_loc_deleted = commit.src_loc_deleted
        num_src_files_touched = commit.num_src_files_touched
        src_files = commit.src_files

        issues = set()
        bug_fixes_per_issue = list()  # duplicates issues, only for debugging purposes
        if (aliased_uid, commit.sha, repo) in bugs_induced_per_sha:  # if it's a blamed sha, how many times
            bug_fixing_commits = bugs_induced_per_sha[(aliased_uid, commit.sha, repo)]
            for issue_no in bug_fixing_commits.keys():
                issues.add(str(issue_no))
            for commits in bug_fixing_commits.values():
                bug_fixes_per_issue += [c for c in commits]
        issues = ','.join(list(issues))
        bug_fixes_per_issue = ','.join(bug_fixes_per_issue)

        c_metadata_project = (aliased_uid, repo, y_m_d, files, src_files, loc_added, src_loc_added, loc_deleted,
                              src_loc_deleted, num_files_touched, num_src_files_touched, commit.sha, issues,
                              bug_fixes_per_issue)
        commits_per_user_project.append(c_metadata_project)

        # per-language metadata
        if src_files:
            src_files = src_files.split(',')
            for file in src_files:
                try:
                    commit_file = session.query(CommitFiles).filter_by(repo_id=commit.repo_id,
                                                                       repo_slug=folderNameToSlug(repo), # slug_original(repo),
                                                                       commit_sha=commit.sha, file=file).one()
                except exc.NoResultFound:
                    logger.error("No file %s found in commit %s" % (file, commit.sha))
                    continue
                try:
                    assert (BasicFileTypeClassifier.DOC != commit_file.language), "Language mismatch error"
                except AssertionError:
                    logger.error("Non-source file %s, skipping." % file)
                    continue
                loc_added = commit_file.loc_added
                loc_deleted = commit_file.loc_deleted
                lang_info = basic_classifier.guess_languages([file])
                lang = list(lang_info.values())[0]
                langs.add(lang)
                c_metadata_language = (aliased_uid, lang, y_m_d, file, loc_added, loc_deleted, commit.sha)
                commits_per_user_language.append(c_metadata_language)

        commits_per_user[aliased_uid] = (commits_per_user_project, commits_per_user_language)

    logger.info("Sorting the list of distinct dates from blamed commits.")
    distinct_dates = sorted(dates, key=lambda x: datetime.datetime.strptime(x, '%Y-%m-%d'))

    logger.info("Sorting the list of distinct repo slugs from the commits.")
    distinct_projects = sorted(repos)

    logger.info("Sorting the list of distinct source languages used for commits.")
    distinct_languages = sorted(langs)

    prj_rows = []
    lang_rows = []
    logger.info("Performing project and language aggregation of blamed-commits daily metadata per user.")
    for y_m_d in distinct_dates:
        for aliased_uid, (user_commits_project, user_commits_languages) in commits_per_user.items():
            # project aggregation
            for project in distinct_projects:
                daily_commits_per_project = []
                loc_added = 0
                loc_deleted = 0
                src_loc_added = 0
                src_loc_deleted = 0
                bugs = []
                bug_inducing_commits = 0
                for ucp in user_commits_project:
                    if y_m_d == ucp[2] and project == ucp[1]:
                        daily_commits_per_project.append(ucp)
                if daily_commits_per_project:
                    d_num_file_touches, d_num_src_file_touches, d_num_files_touched, d_num_src_files_touched = \
                        daily_data_per_project(set(daily_commits_per_project))
                    for commit in daily_commits_per_project:
                        loc_added += commit[5]
                        src_loc_added += commit[6]
                        loc_deleted += commit[7]
                        src_loc_deleted += commit[8]
                        if commit[12] != '':
                            bugs += commit[12].split(',')
                            bug_inducing_commits += 1
                    bugs = len(set(bugs))
                    prj_rows.append((aliased_uid, project, y_m_d, len(daily_commits_per_project), d_num_file_touches,
                                     d_num_src_file_touches, d_num_files_touched, d_num_src_files_touched, loc_added,
                                     src_loc_added, loc_deleted, src_loc_deleted, bugs, bug_inducing_commits))

            # language aggregation
            for lang in distinct_languages:
                daily_commits_per_language = []
                src_loc_added = 0
                src_loc_deleted = 0

                for ucl in user_commits_languages:
                    if y_m_d == ucl[2] and lang == ucl[1]:
                        daily_commits_per_language.append(ucl)
                if daily_commits_per_language:
                    num_src_file_touches, num_src_files_touched = daily_data_per_language(daily_commits_per_language,
                                                                                          lang, basic_classifier)
                    for commit in daily_commits_per_language:
                        src_loc_added += int(commit[4])
                        src_loc_deleted += int(commit[5])
                    lang_rows.append(
                        (aliased_uid, lang, y_m_d, len(daily_commits_per_language), num_src_file_touches,
                         num_src_files_touched, src_loc_added, src_loc_deleted))

    logger.info("Writing to files.")
    prj_writer = CsvWriter(csv_file=prj_outfile, mode='w')
    """
    - user_project_date_totalcommits.csv
        user_id;project;date;num_commits;num_file_touches;num_src_file_touches;num_files_touched;num_src_files_touched;loc_added;src_loc_added;loc_deleted;src_loc_deleted
        2;bbatsov_ruby-style-guide;2011-09-27;1;1;0;1;0;2;;2;

    """
    prj_header = ['user_id', 'project', 'day', 'num_commits', 'num_file_touches', 'num_src_file_touches',
                  'num_files_touched', 'num_src_files_touched', 'loc_added', 'src_loc_added', 'loc_deleted',
                  'src_loc_deleted', 'num_bugs_induced', 'num_bug_inducing_commits']
    prj_writer.writerow(prj_header)
    for row in prj_rows:
        prj_writer.writerow(row)
    prj_writer.close()
    logger.info("Done writing %s." % prj_outfile)

    lang_writer = CsvWriter(csv_file=lang_outfile, mode='w')
    """
    - user_language_date_totalcommits.csv
    #user_id;language;date;num_commits;num_file_touches;num_files_touched;loc_added;loc_deleted
    #2;c;2013-09-29;1;1;1;8;0
    """
    lang_header = ['user_id', 'language', 'day', 'num_commits', 'num_src_file_touches', 'num_src_files_touched',
                   'src_loc_added', 'src_loc_deleted']
    lang_writer.writerow(lang_header)
    for row in lang_rows:
        lang_writer.writerow(row)
    lang_writer.close()
    logger.info("Done writing %s." % lang_outfile)


if __name__ == '__main__':
    loggingcfg.initialize_logger()
    target = os.path.abspath(sys.argv[1] + os.path.sep + 'idm' + os.path.sep + 'dict' + os.path.sep + 'aliasMap.dict')
    if os.path.getsize(target) > 0:
        with open(target, "rb") as f:
            unpickler = pickle.Unpickler(f)
            alias_map = unpickler.load()

        bc = BasicFileTypeClassifier()

        export(sys.argv[2:], alias_map, bc)
