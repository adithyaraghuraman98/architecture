import os
import sys
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
from orm.tables import Commit, Blame, Repo, Bug_Commit_Timeline, Design_Doc_Timeline, Project, User
from orm.lindholmen import Repo_Lindholmen, UMLFile_Lindholmen, Commit_Lindholmen
from orm.ght import Repo_GHT, PR_GHT

session = SessionWrapper.new(init = True)

# out_path = '/data2/adithya/szz/repos'
# with open('project-list-lindholmen.txt','w') as f:
#     for repo in session.query(Repo_Lindholmen):
#         slug = repo.url.split("https://www.github.com/")[-1]
#         f.write(slug+'\n')

count = 0
out_path = '/data2/adithya/szz/repos/'
avail_issues = session.query(GhIssue.slug).distinct().all()
avail_issues = [elem[0] for elem in avail_issues]
with open('project-list_577.txt','w') as f:

	for slug in avail_issues:
		folder_path = '_____'.join(slug.split('/'))
		folder_path = out_path+folder_path
		if(os.path.exists(folder_path)):
			f.write(slug+'\n')
			count+=1
			print(slug)

print(count)
print(len(avail_issues))
# with open('project-list.txt','r') as f:
# 	for url in f.readlines():
# 		slug = url.split("https://www.github.com/")[-1].strip()
# 		if(slug not in avail_issues):
# 			print(slug)
# 			count+=1
# print(count)