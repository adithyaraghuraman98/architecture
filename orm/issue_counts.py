'''
Created on Apr 21, 2017

@author: Bogdan Vasilescu
'''

import sqlalchemy as sa
from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy import Integer, String, Boolean, BigInteger, DateTime, Text
from sqlalchemy.dialects.mysql import TIMESTAMP
from sqlalchemy.orm import relationship, backref
#from sqlalchemy.ext.associationproxy import association_proxy
import datetime
from .base import Base
from dateutil import parser
from unidecode import unidecode


class IssueCounts(Base):
    __tablename__ = 'issueCounts'
    
    id = Column(Integer, primary_key=True)
    travis_id = Column(BigInteger)
    ght_id = Column(Text)
    slug = Column(String(255))
    language = Column(String(255))
    num_issues = Column(Integer)
    num_issues_labeled = Column(Integer)
    num_prs = Column(Integer)
            
    def __init__(self, 
                 travis_id,
                 ght_id,
                 slug,
                 language,
                 num_issues,
                 num_issues_labeled,
                 num_prs):
        
        self.travis_id = travis_id
        self.ght_id = ght_id
        self.slug = slug
        self.language = language
        self.num_issues = num_issues
        self.num_issues_labeled = num_issues_labeled
        self.num_prs = num_prs
