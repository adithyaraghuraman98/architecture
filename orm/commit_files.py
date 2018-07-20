from sqlalchemy import Column, ForeignKey, String, BigInteger, Integer, Index, SmallInteger

from .base import Base


class CommitFiles(Base):
    __tablename__ = 'commit_files'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    repo_id = Column(BigInteger, index=True, nullable=False)  # ForeignKey("repos.id"),
    repo_slug = Column(String(255), nullable=False)
    commit_sha = Column(String(255), nullable=False)
    # commit_id = Column(BigInteger, ForeignKey("commits.id"), index=True, nullable=False)
    file = Column(String(255), nullable=False)
    loc_added = Column(Integer)
    loc_deleted = Column(Integer)
    language = Column(SmallInteger)

    __table_args__ = (Index('ix_commitfiles', "commit_sha", "repo_slug", "file", unique=True),)

    def __init__(self,
                 repo_id,
                 repo_slug,
                 commit_sha,
                 #commit_id,
                 file,
                 loc_add,
                 loc_del,
                 lang
                 ):
        self.repo_id = repo_id
        self.repo_slug = repo_slug
        self.commit_sha = commit_sha
        #self.commit_id = commit_id
        self.file = file
        self.loc_added = loc_add
        self.loc_deleted = loc_del
        self.language = lang
