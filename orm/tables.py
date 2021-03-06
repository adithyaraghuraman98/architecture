from sqlalchemy import Column
from sqlalchemy import Integer, String, Boolean, BigInteger, DateTime, Text, ForeignKey, Float
from unidecode import unidecode
from sqlalchemy.dialects.mysql import LONGTEXT

from .base import Base

class Control_Repo(Base):
    __tablename__ = 'Control_Repos'
    id = Column(BigInteger, primary_key=True)
    url = Column(String(255))
    name = Column(String(255))
    language = Column(String(255))
    created_at = Column(DateTime(timezone=True))
    repo_id_GHT = Column(BigInteger)
    num_issues = Column(BigInteger)

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

class BRepo(Base):
    __tablename__ = 'backup_repos'
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
    __tablename__ = 'user'
    
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

class BUser(Base):
    __tablename__ = 'backup_users'
    
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
    message = Column(LONGTEXT)
    num_parents = Column(Integer)
    num_additions = Column(Integer)
    num_deletions = Column(Integer)
    num_files_changed = Column(Integer)
    files = Column(LONGTEXT)  # comma-separated list of file names
    src_loc_added = Column(Integer)
    src_loc_deleted = Column(Integer)
    num_src_files_touched = Column(Integer)
    src_files = Column(LONGTEXT)  # comma-separated list of file names

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

class Project(Base):
    __tablename__ = 'projects_master'
    id = Column(BigInteger,primary_key = True)
    name = Column(String(255))
    url = Column(String(255))
    age = Column(Integer)
    repo_id_lind = Column(Integer)
    repo_id_GHT = Column(BigInteger)
    is_valid = Column(Boolean)
    is_treatment = Column(Boolean)
    language = Column(String(255))
    user_type = Column(String(255))
    commercial_involvement = Column(Float)
    num_bugs = Column (BigInteger)
    num_contributors = Column(Integer)
    num_commits = Column (Integer)
    num_desdocs = Column(Integer)
    num_issues = Column(Integer)
    num_raw_issues = Column(Integer)
    num_PRs = Column(Integer)
    num_forks = Column(Integer)
    num_issuelinks = Column(Integer)

    def __init__(self, name, age, repo_id_lind, repo_id_GHT, is_valid, language, num_bugs, is_treatment, user_type, commercial_involvement, url, num_contributors, num_commits, 
        num_desdocs, num_issues, num_raw_issues, num_PRs, num_forks, num_issuelinks):
        self.name = name
        self.age = age
        self.repo_id_lind = repo_id_lind
        self.repo_id_GHT = repo_id_GHT
        self.is_valid = is_valid
        self.url = url
        self.user_type = user_type 
        self.language = language
        self.commercial_involvement = commercial_involvement
        self.is_treatment = is_treatment
        self.num_bugs = num_bugs
        self.num_issuelinks = num_issuelinks
        self.num_contributors = num_contributors
        self.num_commits = num_commits
        self.num_desdocs = num_desdocs
        self.num_issues = num_issues
        self.num_raw_issues = num_raw_issues
        self.num_PRs = num_PRs
        self.num_forks = num_forks




class BBlame(Base):
    __tablename__ = 'backup_blame'
    
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
    Q3_2018 = Column(Integer)
    Q4_2018 = Column(Integer)


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
                Q2_2018,
                Q3_2018,
                Q4_2018) :
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
        self.Q3_2018 = Q3_2018
        self.Q4_2018 = Q4_2018

class Issue_Timeline(Base):
    __tablename__ = 'issue_timeline'
    
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
    Q3_2018 = Column(Integer)
    Q4_2018 = Column(Integer)


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
                Q2_2018,
                Q3_2018,
                Q4_2018) :
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
        self.Q3_2018 = Q3_2018
        self.Q4_2018 = Q4_2018

class Bug_Issue_Timeline(Base):
    __tablename__ = 'bug_issue_timeline'
    
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
    Q3_2018 = Column(Integer)
    Q4_2018 = Column(Integer)


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
                Q2_2018,
                Q3_2018,
                Q4_2018) :
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
        self.Q3_2018 = Q3_2018
        self.Q4_2018 = Q4_2018

class Design_Doc_Timeline(Base):
    __tablename__ = 'design_doc_timeline'
    
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
    Q3_2018 = Column(Integer)
    Q4_2018 = Column(Integer)

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
                Q2_2018,
                Q3_2018,
                Q4_2018) :
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
        self.Q3_2018 = Q3_2018
        self.Q4_2018 = Q4_2018  
