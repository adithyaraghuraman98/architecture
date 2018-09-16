import os
import sys
import math
from multiprocessing import Pool, Queue, current_process
from multiprocessing.pool import ThreadPool
import csv
import pygit2
from datetime import datetime, timezone, timedelta
import pytz
import unicodedata
from sqlalchemy import create_engine
from sqlalchemy import and_, func
from sqlalchemy.orm import sessionmaker
import subprocess
from unidecode import unidecode
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from orm.initdb import SessionWrapper
from orm import GhIssue
from orm.tables import Commit, Blame, Repo, Bug_Commit_Timeline, Design_Doc_Timeline, Project, User, Lindholmen_Issues
from orm.lindholmen import Repo_Lindholmen, UMLFile_Lindholmen, Commit_Lindholmen
from orm.ght import Repo_GHT, PR_GHT, Issue_GHT

session = SessionWrapper.new(init = True)

counter  = 0
index = 0
        

engine_ght = create_engine('mysql+pymysql://adithya:zY1PzfI1uS9cz8Q@localhost/ghtorrent-2018-03?charset=utf8mb4')
Session_GHT = sessionmaker(engine_ght)
session_GHT = Session_GHT()

count = 0
with open('treatment-group.txt','w') as f:
    for repo in session.query(Lindholmen_Issues):
        if(repo.num_issues>=30 and repo.is_fork==0):
            slug = repo.url.split("https://www.github.com/")[-1]
            f.write(slug+'\n')

# for repo in session.query(Repo_Lindholmen):
#     try:
#         repo = session.query(Lindholmen_Issues).filter_by(url=repo.url).one()
#         print(repo.url, "Already in db")
#         continue
#     except:
#         slug = repo.url.split("https://www.github.com/")[-1]
#         url_ght = "https://api.github.com/repos/"+slug
#         repo_GHT_list = session_GHT.query(Repo_GHT).filter_by(url = url_ght)
#         #num_issues_self = session.query(GhIssue).filter_by(slug = slug, pr_num = None).count()
#         num_issues_GHT = 0
#         if(repo_GHT_list != None):
#             for repo_GHT in repo_GHT_list:
#                 num_issues_GHT += session_GHT.query(Issue_GHT).filter_by(repo_id = repo_GHT.id, 
#                     pull_request = 0).count()

#             db_issues = Lindholmen_Issues(url = repo.url, num_issues = num_issues_GHT, is_fork = repo_GHT.forked_from != None)
#             session.add(db_issues)
#             session.commit()
#         print(url_ght, num_issues_GHT)
#         print("---------")