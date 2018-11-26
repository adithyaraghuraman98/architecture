'''
Created on Apr 21, 2017

@author: Bogdan Vasilescu
'''

import datetime

from dateutil import parser
from sqlalchemy import Column
from sqlalchemy import Integer, String, Boolean, BigInteger, DateTime, Index
from unidecode import unidecode

from .base import Base

class BGhIssue(Base):
    __tablename__ = 'backup_issues'
    
    id = Column(Integer, primary_key=True)
    slug = Column(String(255), index=True)
    issue_id = Column(BigInteger, index=True)
    issue_number = Column(Integer)
    state = Column(String(20))
    created_at = Column(DateTime(timezone=True))
    closed_at = Column(DateTime(timezone=True))
    created_by_login = Column(String(255))
    closed_by_login = Column(String(255))
    assignee_login = Column(String(255))
    title = Column(String(1024))
    num_comments = Column(Integer)
    labels = Column(String(1024))
    pr_num = Column(Integer)
            
    def __init__(self, 
                 slug,
                 issue_id, 
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
                 pr_num):
        
        self.slug = slug
        self.issue_id = issue_id
        self.issue_number = issue_number
        self.state = state
        
        if created_at is not None and created_at != 'None':
            st = parser.parse(created_at)
            self.created_at = datetime.datetime(st.year, st.month, st.day, st.hour, st.minute, st.second)
        else:
            self.created_at = None
            
        if closed_at is not None and closed_at != 'None':
            st = parser.parse(closed_at)
            self.closed_at = datetime.datetime(st.year, st.month, st.day, st.hour, st.minute, st.second)
        else:
            self.closed_at = None
            
        self.created_by_login = created_by_login
        self.closed_by_login = closed_by_login
        self.assignee_login = assignee_login
        self.title = unidecode(title[:1024]).strip()
        self.num_comments = num_comments
        self.labels = labels
        self.pr_num = pr_num

    def __repr__(self):
        return 'Issue: %s' % self.title

class GHIssueClassification(Base):
    __tablename__ = 'issues2classes'
    id = Column(Integer, primary_key=True)
    slug = Column(String(255), index=True)
    issue_id = Column(BigInteger, index=True)
    issue_number = Column(Integer)
    title = Column(String(1024))
    is_bug = Column(Boolean)

    def __init__(self, 
                 slug,
                 issue_id, 
                 issue_number,
                 title,
                 is_bug):
        self.slug = slug
        self.issue_id = issue_id
        self.issue_number = issue_number
        self.title = title
        self.is_bug = is_bug

class GhIssue(Base):
    __tablename__ = 'issues2'
    
    id = Column(Integer, primary_key=True)
    slug = Column(String(255), index=True)
    issue_id = Column(BigInteger, index=True)
    issue_number = Column(Integer)
    state = Column(String(20))
    created_at = Column(DateTime(timezone=True))
    closed_at = Column(DateTime(timezone=True))
    created_by_login = Column(String(255))
    closed_by_login = Column(String(255))
    assignee_login = Column(String(255))
    title = Column(String(1024))
    num_comments = Column(Integer)
    labels = Column(String(1024))
    pr_num = Column(Integer)
            
    def __init__(self, 
                 slug,
                 issue_id, 
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
                 pr_num):
        
        self.slug = slug
        self.issue_id = issue_id
        self.issue_number = issue_number
        self.state = state
        
        if created_at is not None and created_at != 'None':
            st = parser.parse(created_at)
            self.created_at = datetime.datetime(st.year, st.month, st.day, st.hour, st.minute, st.second)
        else:
            self.created_at = None
            
        if closed_at is not None and closed_at != 'None':
            st = parser.parse(closed_at)
            self.closed_at = datetime.datetime(st.year, st.month, st.day, st.hour, st.minute, st.second)
        else:
            self.closed_at = None
            
        self.created_by_login = created_by_login
        self.closed_by_login = closed_by_login
        self.assignee_login = assignee_login
        self.title = unidecode(title[:1024]).strip()
        self.num_comments = num_comments
        self.labels = labels
        self.pr_num = pr_num

    def __repr__(self):
        return 'Issue: %s' % self.title

