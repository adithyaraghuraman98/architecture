import os
import sys
sys.path.append('ghd')
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

from orm.initdb import SessionWrapper
from orm.initdb import SessionWrapper_GHT
from orm import GhIssue, BGhIssue
from orm.tables import Commit, Blame, Repo, Bug_Commit_Timeline, Design_Doc_Timeline, Project, User
from orm.lindholmen import Repo_Lindholmen, UMLFile_Lindholmen, Commit_Lindholmen, Lindholmen_Issues
from orm.ght import Repo_GHT, PR_GHT, User_GHT
import pandas as pd



from stutils import decorators as d
from stutils import email_utils as email
from stutils import mapreduce
from stutils import sysutils
from stutils import versions


def get_num_contributors(repo):
    users = session.query(User).filter_by(repo_id = repo.id)
    total = users.count()
    for user in users:
        if(user.id not in alias_dict):
            continue
        else:
            orig_id = alias_dict[user.id]
            orig_user = session.query(User).filter_by(id = orig_id).one()
            if(orig_user.repo_id==repo.id):
                total-=1
    return total

def get_num_bugs(repo):
    blame_list = session.query(Blame).filter_by(repo_id = repo.id)
    blamed_sha_list = set([elem.blamed_sha for elem in blame_list])
    return len(blamed_sha_list)

def get_is_valid(repo, url_Lind):
    if(repo.id>577 and repo.id<1227):
        return False
    if(session.query(Lindholmen_Issues).filter_by(url = url_Lind).count()>0 and 
        session.query(Lindholmen_Issues).filter_by(url = url_Lind).one().num_issues<50):
        return False
    return True


session = SessionWrapper.new(init = True)
session_GHT = SessionWrapper_GHT.new()

alias_dict = dict()
with open('idm/idm_map.csv', 'r') as f:
    for line in f.readlines():
        alias = int(line.split(';')[0].strip())
        orig = int(line.split(';')[1].strip())
        alias_dict[alias] = orig

with open('control-group.txt','r') as f:       
    for line in f.readlines():
        slug = line.strip()
        num_issues = session.query(GhIssue).filter_by(slug = slug).count()
        print(slug, num_issues)



# for repo in session.query(Repo):
#     print(repo.slug)
#     url_Lind = "https://www.github.com/"+repo.slug
    
#     num_desdocs = 0
#     try:
#         repo_Lind = session.query(Repo_Lindholmen).filter_by(url = url_Lind).first()
#         repo_id_Lind = repo_Lind.id
#         num_desdocs = session.query(UMLFile_Lindholmen).filter_by(repo_id = repo_id_Lind).count()
#     except:
#         repo_id_Lind = None
#     is_valid = get_is_valid(repo, url_Lind)
#     url_ght = "https://api.github.com/repos/"+repo.slug
#     repo_GHT = session_GHT.query(Repo_GHT).filter_by(url = url_ght).first()
#     repo_id_GHT = repo_GHT.id
#     language = repo_GHT.language
#     is_treatment = repo_id_Lind != None
#     age = (repo.max_commit - repo.min_commit).days
#     # if(not is_treatment):
#     #     num_issues = session.query(BGhIssue).filter_by(slug = repo.slug).count()
#     # else:
#     num_issues = 0
#     if(is_valid):
#         num_issues = session.query(GhIssue).filter_by(slug = repo.slug).count()
#     num_PRs = session_GHT.query(PR_GHT).filter_by(base_repo_id = repo_id_GHT).count()
#     num_forks = session_GHT.query(Repo_GHT).filter_by(forked_from = repo_id_GHT).count()
#     num_contributors = get_num_contributors(repo)
#     num_commits = repo.total_commits
#     num_bugs = get_num_bugs(repo)
#     es = pd.Series([user.email for user in session.query(User).filter_by(repo_id = repo.id)])
#     es = email.is_commercial_bulk(es).tolist()
#     commercial_involvement = 0 if len(es)==0 else (es.count(True)/len(es))
#     user_type = session_GHT.query(User_GHT).filter_by(login = repo.slug.split('/')[0]).first().type


#     db_proj = Project(name = repo.slug, age = age, repo_id_lind = repo_id_Lind, 
#         num_desdocs = num_desdocs, num_commits = num_commits, is_valid = is_valid, language = language, 
#         commercial_involvement = commercial_involvement, num_contributors = num_contributors,
#         user_type = user_type, repo_id_GHT = repo_id_GHT, url = url_Lind, num_bugs = num_bugs, 
#         is_treatment=  is_treatment, num_issues = num_issues, num_PRs = num_PRs, 
#         num_forks = num_forks)
#     session.add(db_proj)
#     session.commit()




