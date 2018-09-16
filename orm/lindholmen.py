from sqlalchemy import Column
from sqlalchemy import Integer, String, Boolean, BigInteger, DateTime, Text, ForeignKey
from unidecode import unidecode

from .base import Base

class Repo_Lindholmen(Base):
    __tablename__ = 'lindholmen_repos'
    id = Column(BigInteger, primary_key=True)
    url = Column(String(255))

class UMLFile_Lindholmen(Base):
    __tablename__ = 'lindholmen_umlfiles'
    id = Column(BigInteger, primary_key =True)
    name = Column(String(255))
    repo_id = Column(BigInteger)
    commits_id =  Column(BigInteger)
    uml_type =  Column(String(255))

class Commit_Lindholmen(Base):
    __tablename__ = 'lindholmen_commits'
    id = Column(BigInteger, primary_key =True)
    gh_id = Column(String(255))
    commit_date = Column(DateTime(timezone=True))

class Lindholmen_Issues(Base):
    __tablename__ = 'lindholmen_issues'
    id = Column(BigInteger, primary_key=True)
    url = Column(String(255))
    num_issues = Column(BigInteger)
    is_fork = Column(Boolean)
