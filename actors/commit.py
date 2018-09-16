import logging
import os
from datetime import timedelta
from time import clock

import szzAnalyzeCommits as RepoAnalyzer
from gitutils.repo import RepoCloner
from szzUtils import folderNameToSlug

logger = logging.getLogger('SZZ')
projects = []
with open ('/data2/adithya/szz/control-group.txt','r') as f:
    for line in f.readlines():
        projects.append(line.strip())



class CommitAnalyzer:
    @staticmethod
    def run_analysis(slug_and_folder):
        folder_name, repos_folder = slug_and_folder
        folder_name = folder_name[1:]
        slug = folderNameToSlug(folder_name)
        folder_path = os.path.join(repos_folder, folder_name)

        if(slug not in projects):
            return
        
        logger.info(msg='Starting analysis of commits from repo {0}.'.format(folder_name))
        if not os.path.exists(folder_path):
            logger.info(msg='Repo {0} not found in {1}.'.format(slug, repos_folder))
            # repo not found on filesystem
            RepoCloner.clone(slug, repos_folder)

        start = clock()
        RepoAnalyzer.get_commits(slug, repos_folder)
        end = clock()
        logger.info(msg='Analysis of repo {0} completed in {1}.'.format(slug, timedelta(seconds=end - start)))
