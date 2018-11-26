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

from orm.initdb import SessionWrapper
from orm.initdb import SessionWrapper_GHT

from orm import GhIssue, BGhIssue, GHIssueClassification
from orm.tables import Commit, Blame, Repo, Bug_Commit_Timeline, Design_Doc_Timeline, Project, User, IssueLink
from orm.lindholmen import Repo_Lindholmen, UMLFile_Lindholmen, Commit_Lindholmen, Lindholmen_Issues
from orm.ght import Repo_GHT, PR_GHT, User_GHT

from langdetect import detect

# bug_signals = ["fail","fails","error","errors", "fix", "fixed", "fixes",
# "not", "doesn't", "problem", "problems"]

# enhancement_signals = ["version", "update", "delete", "improve", "use", "add", "remove", "test", "refactor",
# "support", "licence"]

import sys
import math

trainIssues = []
with open('issue-bug.txt', 'r') as f:
	for line in f.readlines():
		trainIssues.append((line,1))

with open('issue-enh.txt', 'r') as f:
	for line in f.readlines():
		trainIssues.append((line,0))

testissues = trainIssues[50:100] + trainIssues[150:]
trainIssues = trainIssues[0:50] +trainIssues[100:150]

print(len(testissues), len(trainIssues))


 #TODO

vocabulary = set()
bugWordList = [] 
enhWordList = []
textBug = []
textEnh = []
pmapBug = dict()
pmapEnh = dict()

for (trainIssue, label) in trainIssues:
	for word in trainIssue.split(" "):
		word = word.lower().strip()
		vocabulary.add(word)
		if(not word in pmapBug):
			pmapBug[word] = 0
		if(not word in pmapEnh):
			pmapEnh[word] = 0

		if(label == 1):
			textBug.append(word)
			pmapBug[word]+=1
		elif(label ==0):
			textEnh.append(word)
			pmapEnh[word]+=1

pBug = float(sys.argv[1])
pEnh = 1-pBug

for word in vocabulary:
	pmapBug[word] = (pmapBug[word]+1)*1.0/(len(textBug)+len(vocabulary))
	pmapEnh[word] = (pmapEnh[word]+1)*1.0/(len(textEnh)+len(vocabulary))


def classify(title):
	logpBug = math.log(pBug)
	logpEnh = math.log(pEnh)
	words = title.split(" ")
	for word in words:
		word = word.lower().strip()
		if(word in vocabulary):
			logpBug += math.log(pmapBug[word])
			logpEnh += math.log(pmapEnh[word])
	return 1 if logpBug>logpEnh else 0


# count = 0
# for (title,label) in testissues:
# 	out = classify(title)
# 	print(title.strip(),label,out)
# 	if(label != out):
# 		print("touch")
# 		count+=1

# print(count/len(testissues))

session = SessionWrapper.new(init = True)
session_GHT = SessionWrapper_GHT.new()

session.execute("Truncate TABLE issues2classes")

for slug in session.query(GhIssue.slug).distinct().all():
	issues = session.query(GhIssue).filter_by(slug = slug).all()
	issueList = []
	foreign_lang = False
	for issue in issues:
		'''try:
			if(detect(issue.title) != "en"):
				foreign_lang = True
		except:
			foreign_lang = False'''
		classification = 1 if classify(issue.title) else 0
		issueList.append(GHIssueClassification(slug = issue.slug, issue_id = issue.issue_id,
			issue_number=  issue.issue_number, title = issue.title, 
			is_bug = classification))
	if(not foreign_lang):
		session.bulk_save_objects(issueList)
		session.commit()


