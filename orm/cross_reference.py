from sqlalchemy import Column
from sqlalchemy import String, BigInteger

from .base import Base


class CrossReference(Base):
    """
    refs to issues/PRs or commit SHAs
    e.g., rails/rails#123, bateman/dynkaas#70460b4b4aece5915caf5c68d12f560a9fe3e4

    """
    __tablename__ = 'cross_refs'

    id = Column(BigInteger, primary_key=True)
    from_slug = Column(String(255), index=True)
    ref = Column(String(255))
    comment_type = Column(String(10))  # issue/pr, commit

    def __init__(self,
                 from_slug,
                 ref,
                 comment_type
                 ):
        self.from_slug = from_slug
        self.ref = ref
        self.comment_type = comment_type
