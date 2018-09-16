import os
import sys
import random
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
from orm import GhIssue, BGhIssue
from orm.tables import Commit, Blame, Repo, Bug_Commit_Timeline, Design_Doc_Timeline, Project, User, Control_Repo
from orm.lindholmen import Repo_Lindholmen, UMLFile_Lindholmen, Commit_Lindholmen
from orm.ght import Repo_GHT, PR_GHT, Issue_GHT

session = SessionWrapper.new(init = True)

session_GHT = SessionWrapper_GHT.new()


NUM_CONTROL_REPOS = 600

old_repos = []

# with open('control-group-new.txt','r') as g:  
#     for index in indices:
#         repo = session.query(Control_Repo).filter_by(id = index).one()
#         slug = repo.url.split("https://api.github.com/repos/")[-1].strip()
#         g.write(slug+'\n')
#         if(slug in old_repos):
#             count+=1
#             print(slug)


# print(count)

projects = []
with open('control-group-new.txt','r') as g: 
    for line in g.readlines():
        if(line.strip() in old_repos):
            print(line.strip())
        projects.append(line.strip())




# BELOW IS THE CODE USED TO MINE GHT
def analyze_repo(repo):
    slug = repo.url.split("//api.github.com/repos/")[-1]
    lind_url = "https://www.github.com/"+ slug
    if(session.query(Repo_Lindholmen).filter_by(url = lind_url).count()!=0):
        return False
    if(repo.forked_from != None):
        return False
    
    num_issues = session_GHT.query(Issue_GHT).filter_by(repo_id = repo.id,pull_request = 0).count()
    if(num_issues<30):
        return False
    
    if(session.query(Control_Repo).filter_by(url = repo.url).count()!=0):
        return False
    # control_repo = Control_Repo(url = repo.url, name = repo.name,
    #    language = repo.language, created_at = repo.created_at, repo_id_GHT = repo.id,
    #     num_issues=  num_issues)
    # session.add(control_repo)
    # session.commit()
    print(num_issues)
    return True




sample = random.sample(range(1,89176716), 1000000)
with open('control-group.txt','w') as f:
	for index in sample:
	    try:
	        repo = session_GHT.query(Repo_GHT).filter_by(id = index).one()
	    except: 
	        continue
	    if(analyze_repo(repo)):
	    	print(repo.url)
	    	f.write(repo.url.split("//api.github.com/repos/")[-1]+'\n')

	    


