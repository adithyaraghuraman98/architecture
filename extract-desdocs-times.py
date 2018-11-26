from orm.tables import Commit, Blame, Repo, Bug_Commit_Timeline, Design_Doc_Timeline
from orm.lindholmen import Repo_Lindholmen, UMLFile_Lindholmen, Commit_Lindholmen

from orm.initdb import SessionWrapper

session = SessionWrapper.new(init= True)
session.execute("Truncate table design_doc_timeline")


def create_dict():
    out = dict()
    for year in range(2012,2019):
        innedDict = dict()
        for quart in range(0,4):
            innedDict[quart] = 0
        out[year] = innedDict
    return out 

for repo in session.query(Repo).filter(Repo.total_commits >= 0):
    url_Lind = "https://www.github.com/"+ repo.slug
    is_treatment = False
    num_des_docs = 0
    try:
        repo_Lind = session.query(Repo_Lindholmen).filter_by(url = url_Lind).one()
        is_treatment = True
    except:
        is_treatment = False
    docs_dict = create_dict()
    if(is_treatment):
        design_docs = session.query(UMLFile_Lindholmen).filter_by(repo_id = repo_Lind.id)
        num_des_docs = design_docs.count()
        for doc in design_docs:
            committed_at = session.query(Commit_Lindholmen).filter_by(id = doc.commits_id).one().commit_date
            year = committed_at.year
            quarter = (committed_at.month-1)//3
            if(year not in docs_dict):
                docs_dict[year] = dict()
            if(quarter not in docs_dict[year]):
                docs_dict[year][quarter] = 0
            docs_dict[year][quarter] =1

    db_desdoc = Design_Doc_Timeline(repo_id = repo.id, slug = repo.slug, total = num_des_docs, 
        Q1_2012 = docs_dict[2012][0], Q2_2012 = docs_dict[2012][1], 
        Q3_2012 = docs_dict[2012][2], Q4_2012 = docs_dict[2012][3],
        Q1_2013 = docs_dict[2013][0], Q2_2013 = docs_dict[2013][1], 
        Q3_2013 = docs_dict[2013][2], Q4_2013 = docs_dict[2013][3],
        Q1_2014 = docs_dict[2014][0], Q2_2014 = docs_dict[2014][1], 
        Q3_2014 = docs_dict[2014][2], Q4_2014 = docs_dict[2014][3],
        Q1_2015 = docs_dict[2015][0], Q2_2015 = docs_dict[2015][1], 
        Q3_2015 = docs_dict[2015][2], Q4_2015 = docs_dict[2015][3],
        Q1_2016 = docs_dict[2016][0], Q2_2016 = docs_dict[2016][1], 
        Q3_2016 = docs_dict[2016][2], Q4_2016 = docs_dict[2016][3],
        Q1_2017 = docs_dict[2017][0], Q2_2017 = docs_dict[2017][1], 
        Q3_2017 = docs_dict[2017][2], Q4_2017 = docs_dict[2017][3],
        Q1_2018 = docs_dict[2018][0], Q2_2018 = docs_dict[2018][1],
        Q3_2018 = docs_dict[2018][2], Q4_2018 = docs_dict[2018][3])  


    session.add(db_desdoc)
    session.commit()
    print(repo.slug)


    