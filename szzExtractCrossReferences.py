import re

from sqlalchemy.exc import DataError

from loggingcfg import initialize_logger
from orm.cross_reference import CrossReference
from orm.initdb import SessionWrapper
from orm.tables import Commit, Repo
from orm.issue_comments import IssueComment

regex = r'(\S+\/\S+)(#\d+|@\d+)'


def replace(_str):
    _ref = _str.replace("(", "")
    _ref = _ref.replace(")", "")
    _ref = _ref.replace("[", "")
    _ref = _ref.replace("]", "")
    return _ref


if __name__ == '__main__':
    logger = initialize_logger()

    session = SessionWrapper.new(init=True)
    logger.info("Connected to db")

    logger.info("Retrieving comments from commits")
    commit_messages = session.query(Repo.slug, Commit.message).filter(Repo.id == Commit.repo_id).all()
    logger.info("Extracting cross refs from commit messages")
    idx = 0
    for cm in commit_messages:
        cross_refs = re.finditer(regex, cm.message, re.MULTILINE)
        for ref in cross_refs:
            if cm.slug not in ref.group(0):
                _ref = replace(ref.group(0))
                cref = CrossReference(from_slug=cm.slug, ref=_ref, comment_type='commit')
                session.add(cref)
                idx += 1
                if not idx % 10:
                    try:
                        logger.info("Cross-references extracted so far: %s" % idx)
                        session.commit()
                    except DataError as de:
                        logger.error(de)
    session.commit()

    logger.info("Retrieving comments from issues and pull-requests")
    issuepr_messages = session.query(IssueComment.slug, IssueComment.body).all()
    logger.info("Extracting cross refs from issue/PR messages")
    idx = 0
    for ipr in issuepr_messages:
        cross_refs = re.finditer(regex, ipr.body, re.MULTILINE)
        for ref in cross_refs:
            if ipr.slug not in ref.group(0):
                _ref = replace(ref.group(0))
                cref = CrossReference(from_slug=ipr.slug, ref=_ref, comment_type='issue/pr')
                session.add(cref)
                idx += 1
                if not idx % 10:
                    try:
                        logger.info("Cross-references extracted so far: %s" % idx)
                        session.commit()
                    except DataError as de:
                        logger.error(de)
    session.commit()

    logger.info("Done")
