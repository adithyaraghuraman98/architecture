from sqlalchemy import Column
from sqlalchemy import Integer, String, Boolean, BigInteger, DateTime, Text, ForeignKey
from unidecode import unidecode
from sqlalchemy.dialects.mysql import LONGTEXT

from .base import Base


class Repo_GHT(Base):
    __tablename__ = 'projects'
    id = Column(BigInteger, primary_key=True)
    url = Column(String(255))
    name = Column(String(255))
    language = Column(String(255))
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    forked_from = Column(BigInteger)

class PR_GHT(Base):
    __tablename__ = 'pull_requests'
    id = Column(BigInteger, primary_key=True)
    head_repo_id = Column(BigInteger)
    base_repo_id = Column(BigInteger)
    
class Issue_GHT(Base):
    __tablename__='issues'
    id = Column(BigInteger, primary_key=True)
    repo_id = Column(BigInteger)
    issue_id = Column(Text)
    pull_request = Column(Integer)
    created_at = Column(DateTime(timezone=True))

class User_GHT(Base):
    __tablename__='users'
    id = Column(BigInteger, primary_key=True)
    login = Column(String(255))
    type = Column(String(255))


