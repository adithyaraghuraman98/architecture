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
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from orm.initdb import SessionWrapper
from orm import GhIssue
from orm.issue_comments import IssueComment
from orm.tables import Commit, Blame, Repo, Bug_Commit_Timeline, Design_Doc_Timeline, Project, User
from orm.lindholmen import Repo_Lindholmen, UMLFile_Lindholmen, Commit_Lindholmen
from orm.ght import Repo_GHT, PR_GHT

session = SessionWrapper.new(init = True)

slug_list = [elem for elem in session.query(GhIssue.slug).distinct().all()]
slug_list = [elem[0] for elem in slug_list]

random_sample = random.sample(range(1449),20)
i = 1
for index in random_sample:
	slug = slug_list[index]
	issues = session.query(GhIssue).filter_by(slug = slug, labels = "", pr_num = None).all()
	if(len(issues)>10):
		sub_issues= random.sample(issues,10)
		for issue in sub_issues:
			print(i,slug, issue)
			i+=1
	