from sqlalchemy import Column
from sqlalchemy import Integer, String, Boolean, BigInteger, DateTime, Text, ForeignKey
from unidecode import unidecode

from .base import Base


class Repo(Base):
    __tablename__ = 'repos'
    
    id = Column(BigInteger, primary_key=True)
    slug = Column(String(255), index=True)
    min_commit = Column(DateTime(timezone=True))
    max_commit = Column(DateTime(timezone=True))
    total_commits = Column(Integer)

    def __init__(self,
                 slug,
                 min_commit,
                 max_commit,
                 total_commits):
        self.slug = slug
        self.min_commit = min_commit
        self.max_commit = max_commit
        self.total_commits = total_commits


class User(Base):
    __tablename__ = 'users'
    
    id = Column(BigInteger, primary_key=True)
    repo_id = Column(BigInteger, index=True, nullable=False)  # ForeignKey("repos.id")
    user_id = Column(BigInteger, nullable=False)
    name = Column(Text)
    email = Column(Text, nullable=False)

    def __init__(self,
                 repo_id,
                 user_id,
                 name,
                 email):
        self.repo_id = repo_id
        self.user_id = user_id
        self.name = unidecode(name[:255]).strip()
        self.email = email


class Commit(Base):
    __tablename__ = 'commits'
    
    id = Column(BigInteger, primary_key=True)
    repo_id = Column(BigInteger, nullable=False)  # ForeignKey("repos.id")
    sha = Column(String(255), index=True, nullable=False)
    timestamp_utc = Column(DateTime(timezone=True))
    author_id = Column(BigInteger, nullable=False)  # ForeignKey("users.id")
    committer_id = Column(BigInteger, nullable=False)  # ForeignKey("users.id")
    message = Column(Text)
    num_parents = Column(Integer)
    num_additions = Column(Integer)
    num_deletions = Column(Integer)
    num_files_changed = Column(Integer)
    files = Column(Text)  # comma-separated list of file names
    src_loc_added = Column(Integer)
    src_loc_deleted = Column(Integer)
    num_src_files_touched = Column(Integer)
    src_files = Column(Text)  # comma-separated list of file names

    def __init__(self,
                 repo_id,
                 sha,
                 timestamp_utc,
                 author_id,
                 committer_id,
                 message,
                 num_parents,
                 num_additions,
                 num_deletions,
                 num_files_changed,
                 files,
                 src_loc_added,
                 src_loc_deleted,
                 num_src_files_touched,
                 src_files
                 ):
        self.repo_id = repo_id
        self.sha = sha
        self.timestamp_utc = timestamp_utc
        self.author_id = author_id
        self.committer_id = committer_id
        self.message = message
        self.num_parents = num_parents
        self.num_additions = num_additions
        self.num_deletions = num_deletions
        self.num_files_changed = num_files_changed
        self.src_loc_added = src_loc_added
        self.src_loc_deleted = src_loc_deleted
        self.num_src_files_touched = num_src_files_touched
        self.src_files = src_files
        self.files = files


class IssueLink(Base):
    __tablename__ = 'issue_links'
    
    id = Column(BigInteger, primary_key=True)
    repo_id = Column(BigInteger, index=True, nullable=False)  # ForeignKey("repos.id")
    sha = Column(String(255), index=True, nullable=False)
    line = Column(Integer)
    issue_number = Column(Integer)
    is_pr = Column(Boolean)
    delta_open = Column(BigInteger)
    delta_closed = Column(BigInteger)

    def __init__(self,
                 repo_id,
                 sha,
                 line,
                 issue_number,
                 is_pr,
                 delta_open,
                 delta_closed):
        self.repo_id = repo_id
        self.sha = sha
        self.line = line
        self.issue_number = issue_number
        self.is_pr = is_pr
        self.delta_open = delta_open
        self.delta_closed = delta_closed


class Blame(Base):
    __tablename__ = 'blame'
    
    id = Column(BigInteger, primary_key=True)
    repo_id = Column(BigInteger, index=True, nullable=False)  # ForeignKey("repos.id")
    sha = Column(String(255), index=True, nullable=False)
    path = Column(Text)
    type = Column(Integer)
    blamed_sha = Column(String(255), index=True, nullable=False)
    num_blamed_lines = Column(Integer)

    def __init__(self,
                 repo_id,
                 sha,
                 path,
                 type,
                 blamed_sha,
                 num_blamed_lines):
        self.repo_id = repo_id
        self.sha = sha
        self.path = path
        self.type = type
        self.blamed_sha = blamed_sha
        self.num_blamed_lines = num_blamed_lines

class Bug_Commit_Timeline(Base):
    __tablename__ = 'bug_commit_timeline'
    
    id = Column(BigInteger, primary_key=True)
    repo_id = Column(BigInteger, index=True, nullable=False)  # ForeignKey("repos.id")
    slug = Column(String(255), index=True)
    total = Column(Integer)
    Q1_2012 = Column(Integer)
    Q2_2012 = Column(Integer) 
    Q3_2012 = Column(Integer)
    Q4_2012 = Column(Integer)
    Q1_2013 = Column(Integer)
    Q2_2013 = Column(Integer)
    Q3_2013 = Column(Integer)
    Q4_2013 = Column(Integer)
    Q1_2014 = Column(Integer)
    Q2_2014 = Column(Integer)
    Q3_2014 = Column(Integer)
    Q4_2014 = Column(Integer)
    Q1_2015 = Column(Integer)
    Q2_2015 = Column(Integer)
    Q3_2015 = Column(Integer)
    Q4_2015 = Column(Integer)
    Q1_2016 = Column(Integer)
    Q2_2016 = Column(Integer)
    Q3_2016 = Column(Integer)
    Q4_2016 = Column(Integer)
    Q1_2017 = Column(Integer)
    Q2_2017 = Column(Integer)
    Q3_2017 = Column(Integer)
    Q4_2017 = Column(Integer)
    Q1_2018 = Column(Integer)
    Q2_2018 = Column(Integer)


    def __init__(self,
                repo_id,
                slug,
                total,
                Q1_2012,
                Q2_2012,
                Q3_2012,
                Q4_2012,
                Q1_2013,
                Q2_2013,
                Q3_2013,
                Q4_2013,
                Q1_2014,
                Q2_2014,
                Q3_2014,
                Q4_2014,
                Q1_2015,
                Q2_2015,
                Q3_2015,
                Q4_2015,
                Q1_2016,
                Q2_2016,
                Q3_2016,
                Q4_2016,
                Q1_2017,
                Q2_2017,
                Q3_2017,
                Q4_2017,
                Q1_2018,
                Q2_2018) :
        self.repo_id = repo_id
        self.slug = slug
        self.total = total
        self.Q1_2012 = Q1_2012
        self.Q2_2012 = Q2_2012
        self.Q3_2012 = Q3_2012
        self.Q4_2012 = Q4_2012
        self.Q1_2013 = Q1_2013
        self.Q2_2013 = Q2_2013
        self.Q3_2013 = Q3_2013
        self.Q4_2013 = Q4_2013
        self.Q1_2014 = Q1_2014
        self.Q2_2014 = Q2_2014
        self.Q3_2014 = Q3_2014
        self.Q4_2014 = Q4_2014
        self.Q1_2015 = Q1_2015
        self.Q2_2015 = Q2_2015
        self.Q3_2015 = Q3_2015
        self.Q4_2015 = Q4_2015
        self.Q1_2016 = Q1_2016
        self.Q2_2016 = Q2_2016
        self.Q3_2016 = Q3_2016
        self.Q4_2016 = Q4_2016
        self.Q1_2017 = Q1_2017
        self.Q2_2017 = Q2_2017
        self.Q3_2017 = Q3_2017
        self.Q4_2017 = Q4_2017
        self.Q1_2018 = Q1_2018
        self.Q2_2018 = Q2_2018

