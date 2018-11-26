from orm.initdb import SessionWrapper
from orm.tables import Project, Commit, Blame, Repo, Bug_Commit_Timeline, Bug_Issue_Timeline, Issue_Timeline
from orm.ghissue import GhIssue, GHIssueClassification

session = SessionWrapper.new(init= True)
#session.execute("Truncate table bug_commit_timeline")

def create_dict():
    out = dict()
    for year in range(2012,2019):
        innedDict = dict()
        for quart in range(0,4):
            innedDict[quart] = 0
        out[year] = innedDict
    return out 

def extract_blame():

    for project in session.query(Project).filter(Project.num_commits >= 0):
        # if not (project.language =="C++" or project.language=="Java"):
        #     continue
        repo = session.query(Repo).filter_by(slug=project.name).first()
        blame_dict = create_dict()
        blamed_entries = session.query(Blame).filter_by(repo_id = repo.id)
        num_blamed_entries = blamed_entries.count()
        for entry in blamed_entries:
            blamed_commit_sha = entry.blamed_sha
            try:
                blamed_commit = session.query(Commit).filter_by(repo_id = repo.id, sha = blamed_commit_sha).one()
            except:
                continue
            year = blamed_commit.timestamp_utc.year
            quarter = (blamed_commit.timestamp_utc.month-1)//3
            if(year not in blame_dict):
                blame_dict[year] = dict()
            if(quarter not in blame_dict[year]):
                blame_dict[year][quarter] = 0
            blame_dict[year][quarter] +=1

        db_buggycommits = Bug_Commit_Timeline(repo_id = repo.id, slug = repo.slug, total = num_blamed_entries, 
            Q1_2012 = blame_dict[2012][0], Q2_2012 = blame_dict[2012][1], 
            Q3_2012 = blame_dict[2012][2], Q4_2012 = blame_dict[2012][3],
            Q1_2013 = blame_dict[2013][0], Q2_2013 = blame_dict[2013][1], 
            Q3_2013 = blame_dict[2013][2], Q4_2013 = blame_dict[2013][3],
            Q1_2014 = blame_dict[2014][0], Q2_2014 = blame_dict[2014][1], 
            Q3_2014 = blame_dict[2014][2], Q4_2014 = blame_dict[2014][3],
            Q1_2015 = blame_dict[2015][0], Q2_2015 = blame_dict[2015][1], 
            Q3_2015 = blame_dict[2015][2], Q4_2015 = blame_dict[2015][3],
            Q1_2016 = blame_dict[2016][0], Q2_2016 = blame_dict[2016][1], 
            Q3_2016 = blame_dict[2016][2], Q4_2016 = blame_dict[2016][3],
            Q1_2017 = blame_dict[2017][0], Q2_2017 = blame_dict[2017][1], 
            Q3_2017 = blame_dict[2017][2], Q4_2017 = blame_dict[2017][3],
            Q1_2018 = blame_dict[2018][0], Q2_2018 = blame_dict[2018][1],
            Q3_2018 = blame_dict[2018][2], Q4_2018 = blame_dict[2018][3])

        session.add(db_buggycommits)
        session.commit()

def extract_issue():
    for project in session.query(Project).filter(Project.num_commits >= 0):
        repo = session.query(Repo).filter_by(slug=project.name).first()
        issue_dict = create_dict()
        issues = session.query(GhIssue).filter_by(slug = repo.slug)
        for issue in issues:
            year = issue.created_at.year
            quarter = (issue.created_at.month-1)//3
            if(year not in issue_dict):
                issue_dict[year] = dict()
            if(quarter not in issue_dict[year]):
                issue_dict[year][quarter] = 0
            issue_dict[year][quarter] +=1
        db_issues = Issue_Timeline(repo_id = repo.id, slug = repo.slug, total = issues.count(), 
            Q1_2012 = issue_dict[2012][0], Q2_2012 = issue_dict[2012][1], 
            Q3_2012 = issue_dict[2012][2], Q4_2012 = issue_dict[2012][3],
            Q1_2013 = issue_dict[2013][0], Q2_2013 = issue_dict[2013][1], 
            Q3_2013 = issue_dict[2013][2], Q4_2013 = issue_dict[2013][3],
            Q1_2014 = issue_dict[2014][0], Q2_2014 = issue_dict[2014][1], 
            Q3_2014 = issue_dict[2014][2], Q4_2014 = issue_dict[2014][3],
            Q1_2015 = issue_dict[2015][0], Q2_2015 = issue_dict[2015][1], 
            Q3_2015 = issue_dict[2015][2], Q4_2015 = issue_dict[2015][3],
            Q1_2016 = issue_dict[2016][0], Q2_2016 = issue_dict[2016][1], 
            Q3_2016 = issue_dict[2016][2], Q4_2016 = issue_dict[2016][3],
            Q1_2017 = issue_dict[2017][0], Q2_2017 = issue_dict[2017][1], 
            Q3_2017 = issue_dict[2017][2], Q4_2017 = issue_dict[2017][3],
            Q1_2018 = issue_dict[2018][0], Q2_2018 = issue_dict[2018][1],
            Q3_2018 = issue_dict[2018][2], Q4_2018 = issue_dict[2018][3])
        session.add(db_issues)
        session.commit()

def extract_bug_issue():
    for project in session.query(Project).filter(Project.num_commits >= 0):
        repo = session.query(Repo).filter_by(slug=project.name).first()
        issue_dict = create_dict()
        issues = session.query(GHIssueClassification).filter_by(slug= repo.slug)
        for issue in issues:
            db_issue = session.query(GhIssue).filter_by(slug = repo.slug, issue_id = issue.issue_id).one()
            year = db_issue.created_at.year
            quarter = (db_issue.created_at.month-1)//3
            if(year not in issue_dict):
                issue_dict[year] = dict()
            if(quarter not in issue_dict[year]):
                issue_dict[year][quarter] = 0
            issue_dict[year][quarter] +=1

        db_issues = Bug_Issue_Timeline(repo_id = repo.id, slug = repo.slug, total = issues.count(), 
            Q1_2012 = issue_dict[2012][0], Q2_2012 = issue_dict[2012][1], 
            Q3_2012 = issue_dict[2012][2], Q4_2012 = issue_dict[2012][3],
            Q1_2013 = issue_dict[2013][0], Q2_2013 = issue_dict[2013][1], 
            Q3_2013 = issue_dict[2013][2], Q4_2013 = issue_dict[2013][3],
            Q1_2014 = issue_dict[2014][0], Q2_2014 = issue_dict[2014][1], 
            Q3_2014 = issue_dict[2014][2], Q4_2014 = issue_dict[2014][3],
            Q1_2015 = issue_dict[2015][0], Q2_2015 = issue_dict[2015][1], 
            Q3_2015 = issue_dict[2015][2], Q4_2015 = issue_dict[2015][3],
            Q1_2016 = issue_dict[2016][0], Q2_2016 = issue_dict[2016][1], 
            Q3_2016 = issue_dict[2016][2], Q4_2016 = issue_dict[2016][3],
            Q1_2017 = issue_dict[2017][0], Q2_2017 = issue_dict[2017][1], 
            Q3_2017 = issue_dict[2017][2], Q4_2017 = issue_dict[2017][3],
            Q1_2018 = issue_dict[2018][0], Q2_2018 = issue_dict[2018][1],
            Q3_2018 = issue_dict[2018][2], Q4_2018 = issue_dict[2018][3])

        session.add(db_issues)
        session.commit()
#extract_blame()
extract_issue()
extract_bug_issue()

