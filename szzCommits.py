import itertools
import logging
import os
import traceback

import pygit2
from sqlalchemy import and_, func
from sqlalchemy.orm import exc

from activityclassifier import BasicFileTypeClassifier
from orm import Commit, User, Repo, GhIssue, IssueLink, Blame
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

            message = commit.getMessage()

            if message is not None:
                issue_ids = commit.getIssueIds()

                if len(issue_ids) >= 1:
                    num_valid_issues = 0
                    for issue_id in issue_ids:
                        try:
                            # was session_travis
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
                        except exc.NoResultFound:
                            # why authored_datetime and not commited_datetime ???????? ## TODO
                            delta_open = (
                                authored_datetime - gh_issue.created_at.replace(tzinfo=pytz.utc)).total_seconds()
                            ### closed at is important!!!!!!!! ## TODO
                            if gh_issue.closed_at is not None:
                                delta_closed = (
                                    authored_datetime - gh_issue.closed_at.replace(tzinfo=pytz.utc)).total_seconds()

                                if delta_open > 0 and delta_closed <= 0 and gh_issue.pr_num is None:
                                    num_valid_issues += 1
                            else:
                                delta_closed = None

                            db_link = IssueLink(db_repo.id,
                                                sha,
                                                issue_id,
                                                gh_issue.pr_num is not None,
                                                delta_open,
                                                delta_closed)

                            session.add(db_link)

                    if not num_valid_issues:
                        continue

                    first_msg_line = message.split('\n')[0]

                    parents = commit.getParents()
                    num_parents = len(parents)

                    if not num_parents:
                        continue

                    sha_parent = parents[0].hex

                    diff = commit.getDiff(git_repo)

                    try:
                        db_commit = session.query(Commit).filter_by(sha=sha).one()
                    except exc.NoResultFound:
                        db_commit = Commit(db_repo.id,
                                           sha,
                                           authored_datetime,
                                           author_id,
                                           committer_id,
                                           first_msg_line,
                                           num_parents,
                                           diff.stats.insertions,
                                           diff.stats.deletions,
                                           diff.stats.files_changed)
                        session.add(db_commit)
                        session.commit()

                    # TODO parte da estrarre in un altro script
                    blamed_commits = {}

                    for patch in diff:
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
                                    if hl.origin == '-':
                                        line_labels[hl.old_lineno] = basic_classifier.labelDiffLine(
                                            hl.content.replace('\r', '').replace('\n', ''))

                                try:
                                    for bh in git_repo.blame(old_file,
                                                             newest_commit=sha_parent,
                                                             min_line=hunk.old_start,
                                                             max_line=hunk.old_start + hunk.old_lines - 1):
                                        blamed_sha = str(bh.final_commit_id)

                                        if blamed_sha in blamed_commits:
                                            blamed_commit = blamed_commits[blamed_sha]
                                        else:
                                            try:
                                                blamed_commit = CommitWrapper(git_repo.revparse_single(blamed_sha))

                                                blamed_commits[blamed_sha] = blamed_commit

                                                blamed_parents = blamed_commit.getParents()
                                                blamed_num_parents = len(blamed_parents)

                                                if not blamed_num_parents:
                                                    ins = None
                                                    dels = None
                                                    files = None
                                                else:
                                                    blamed_diff = blamed_commit.getDiff(git_repo)
                                                    ins = blamed_diff.stats.insertions
                                                    dels = blamed_diff.stats.deletions
                                                    files = blamed_diff.stats.files_changed

                                                # Ignore commits that changed more than 100 files
                                                if files >= 100:
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
                                                        contributors[
                                                            (blamed_author_name_l, blamed_author_email_l)] = next(
                                                            counter)
                                                    blamed_author_id = contributors[
                                                        (blamed_author_name_l, blamed_author_email_l)]

                                                    if (blamed_committer_name_l,
                                                        blamed_committer_email_l) not in contributors:
                                                        contributors[
                                                            (blamed_committer_name_l, blamed_committer_email_l)] = next(
                                                            counter)
                                                    blamed_committer_id = contributors[
                                                        (blamed_committer_name_l, blamed_committer_email_l)]

                                                    blamed_message = blamed_commit.getMessage()
                                                    blamed_first_msg_line = blamed_message.split('\n')[0]

                                                    blamed_db_commit = Commit(db_repo.id,
                                                                              blamed_sha,
                                                                              blamed_authored_datetime,
                                                                              blamed_author_id,
                                                                              blamed_committer_id,
                                                                              blamed_first_msg_line,
                                                                              blamed_num_parents,
                                                                              ins,
                                                                              dels,
                                                                              files)
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
                                except Exception as e:
                                    logger.error(msg="{0} blame error {1}:\t{2}".format(slug, sha, e))

                        for blamed_sha, num_lines in blame_counter.items():
                            b = Blame(db_repo.id,
                                      sha,
                                      old_file,
                                      label,
                                      blamed_sha,
                                      num_lines)
                            session.add(b)
                        session.commit()

        for (name, email), user_id in sorted(contributors.items(), key=lambda e: e[1]):
            try:
                db_user = session.query(User).filter(and_(User.name == func.binary(name),
                                                          User.email == func.binary(email),
                                                          User.repo_id == db_repo.id)).one()
            except exc.NoResultFound:
                db_user = User(db_repo.id, user_id, name, email)
                session.add(db_user)
            except exc.MultipleResultsFound:
                # FIXME this should'nt be happening
                # is it because we allow name aliases during mining?
                # How do we deal with it now?
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

# for repo in session.query(IssueCounts).filter(and_(IssueCounts.num_issues >= 10,
#                                         IssueCounts.num_issues_labeled >= 1)):
#
#     if repo.slug in ["yui/yui3", "xetorthio/jedis", "wet-boew/wet-boew", "Webconverger/webc", "twitter/scalding",
#                      "twitter/finagle", "symfony/symfony", "sunpy/sunpy", "stig/json-framework",
# "stevenbenner/jquery-powertip", "statsmodels/statsmodels", "sproutcore/sproutcore", "spesmilo/electrum",
# "smathot/OpenSesame", "seajs/seajs", "scrapy/scrapy", "scieloorg/scielo-manager", "scalaz/scalaz",
# "saltstack/salt", "saghul/pyuv", "ryanb/cancan", "ruby-grape/grape", "rspec/rspec-rails", "rspec/rspec-mocks",
# "ros/rosdistro", "RestKit/RestKit", "redaxmedia/redaxscript", "rbrito/tunesviewer", "rapid7/metasploit-framework",
# "randym/axlsx", "rails/rails", "pyrocms/pyrocms", "Pylons/pyramid", "propelorm/propelorm.github.com",
# "pockethub/PocketHub", "pallet/pallet", "openzipkin/zipkin", "OP2/PyOP2", "oddbird/susy", "norman/friendly_id",
# "nodejs/node-v0.x-archive", "nodeca/js-yaml", "netty/netty", "Netflix/SimianArmy", "nesquena/backburner",
# "mozilla/bedrock", "mislav/will_paginate", "middleman/middleman", "michaelklishin/monger", "meteor/meteor",
# "magnars/multiple-cursors.el", "madrobby/zepto", "lml/quadbase", "leon/play-salat", "kraih/mojo",
# "KnpLabs/KnpMenuBundle", "kmalakoff/knockback", "kennethreitz/requests", "joyent/libuv",
# "jonasundderwolf/django-image-cropping", "javan/whenever", "jaredhanson/passport", "janl/mustache.js",
# "JakeWharton/ActionBarSherlock", "ipython/ipython", "icy/pacapt", "heroku/heroku-buildpack-ruby", "harvesthq/chosen",
# "hakimel/reveal.js", "h5bp/html5please", "gwu-libraries/launchpad", "Graylog2/graylog2-server", "grails/grails-core",
# "github/markup", "github/hubot", "GeoNode/geonode", "genemu/GenemuFormBundle", "gabrielfalcao/lettuce",
# "fullcalendar/fullcalendar", "fnando/i18n-js", "errbit/errbit", "emberjs/ember.js", "emberjs/ember-rails",
# "emberjs/data", "ducksboard/gridster.js", "duckduckgo/zeroclickinfo-spice", "duckduckgo/p5-app-duckpan",
# "ded/bowser", "dalehenrich/filetree", "crowdcode-de/KissMDA", "concrete5/concrete5", "CoNarrative/glujs",
# "collective/Solgema.fullcalendar", "cocos2d/cocos2d-x", "chef-cookbooks/cron", "chaplinjs/chaplin",
# "celluloid/celluloid", "celery/django-celery", "CakeDC/recaptcha", "brianmario/mysql2", "brianc/jade-mode",
# "brandonwamboldt/utilphp", "bitcoin/bitcoin", "basho/leveldb", "avoidwork/abaaso", "asciidisco/grunt-requirejs",
# "arsduo/koala", "antirez/redis-doc", "ansible/ansible", "angular/angular.js", "alexrj/Slic3r",
# "alchemy-fr/Phraseanet", "adobe/brackets", "activemerchant/active_merchant"]:
#         continue
#
#     print(repo.slug, repo.num_issues, repo.num_issues_labeled)
#
#     result = get_commits(repo.slug)
#     #(slug, data, err) = result
