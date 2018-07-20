import datetime

from dateutil import parser
from sqlalchemy import Column
from sqlalchemy import Integer, String, BigInteger, DateTime, ForeignKey
from sqlalchemy.dialects.mysql import LONGTEXT

from orm.ghissue import GhIssue
from .base import Base


class IssueComment(Base):
    __tablename__ = 'issue_comments'

    comment_id = Column(BigInteger, primary_key=True)
    issue_id = Column(BigInteger, nullable=False)
    issue_number = Column(Integer)
    slug = Column(String(255))
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    user_github_id = Column(BigInteger)
    user_login = Column(String(255))
    body = Column(LONGTEXT)

    def __init__(self,
                 comment_id,
                 slug,
                 issue_id,
                 issue_number,
                 created_at,
                 updated_at,
                 user_github_id,
                 user_login,
                 body):
        self.comment_id = int(comment_id)
        self.issue_id = int(issue_id)
        self.issue_number = int(issue_number)
        self.slug = slug
        self.user_github_id = user_github_id
        self.user_login = user_login
        self.body = body
        if created_at is not None and created_at != 'None':
            st = parser.parse(created_at)
            self.created_at = datetime.datetime(st.year, st.month, st.day, st.hour, st.minute, st.second)
        else:
            self.created_at = None
        if updated_at is not None and updated_at != 'None':
            st = parser.parse(updated_at)
            self.updated_at = datetime.datetime(st.year, st.month, st.day, st.hour, st.minute, st.second)
        else:
            self.updated_at = None
