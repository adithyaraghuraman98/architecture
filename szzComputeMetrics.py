import sys
import time
from datetime import datetime
from time import strftime

import networkx as nx
import numpy

import loggingcfg
from csvmanager import CsvReader, CsvWriter
from szzUtils import slugToFolderName


def project_conceptualization_login(repos):
    # list with repository with unique user_login
    other = []
    aggregate_repos = dict()
    # list with repository positions to aggregate
    pos = []
    i = 0
    while i < len(repos):
        pos.append(0)
        # split repository (user_login_repository_name)
        login_i, repo_i = repos[i].split("_", 1)
        j = 1
        while j < len(repos):
            login_j, repo_j = repos[j].split("_", 1)
            if login_i == login_j:
                # save position
                pos.append(j)
            j = j + 1
        if len(pos) == 1:
            # unique user_login, add repository to other
            other.append(repos[i])
            # delete repository to repo
            del repos[i]
        else:
            # aggregate repository through the positions
            for elem in pos:
                login_p, repo_p = repos[elem].split("_", 1)
                aggregate_repos[repos[elem]] = login_p + "_*"
                repos[elem] = "nil_nil"
            k = 0
            # delete already aggregated repo
            while k < len(repos):
                if repos[k] == "nil_nil":
                    del repos[k]
                    k = 0
                else:
                    k = k + 1
        # clear pos
        del pos[:]
    return aggregate_repos, other


def project_conceptualization_repo(aggregate_repos, other):
    pos = []
    i = 0
    while i < len(other):
        pos.append(0)
        login_i, repo_i = other[i].split("_", 1)
        j = 1
        while j < len(other):
            login_j, repo_j = other[j].split("_", 1)
            if repo_i == repo_j:
                pos.append(j)
            j = j + 1
        if len(pos) == 1:
            aggregate_repos[other[i]] = other[i]
            del other[i]
        else:
            for elem in pos:
                login_p, repo_p = other[elem].split("_", 1)
                aggregate_repos[other[elem]] = "*_" + repo_p
                other[elem] = "nil_nil"
            k = 0
            while k < len(other):
                if other[k] == "nil_nil":
                    del other[k]
                    k = 0
                else:
                    k = k + 1
        del pos[:]
    return aggregate_repos


def find_projects(commits):
    projects = []
    for elem in commits:
        projects.append(elem[1])
    return projects


def find_day(commits):
    day = []
    for elem in commits:
        day.append(elem[2])
    return day


def global_time(date):
    gb = None
    period = sys.argv[2]
    date_d1 = time.strptime('1990-01-01', "%Y-%m-%d")
    date_d2 = time.strptime(date, "%Y-%m-%d")

    year_d1 = int((strftime("%Y", date_d1)))
    year_d2 = int((strftime("%Y", date_d2)))

    if period == 'week':
        week_d2 = int((strftime("%U", date_d2)))
        gb = ((year_d2 - year_d1) * 52) + week_d2
    if period == 'month':
        month_d2 = int((strftime("%m", date_d2)))
        gb = ((year_d2 - year_d1) * 12) + month_d2
    return gb


def projects_at_period(commits):
    projects = find_projects(commits)
    distinct_projects = set(projects)
    return len(distinct_projects)


def avg_projects_per_day(commits):
    day = find_day(commits)
    distinct_days = set(day)
    projects = find_projects(commits)
    return (len(distinct_days), round((len(projects) / (len(distinct_days) * 1.0)), 3))


def sfocus(commits):
    projects = find_projects(commits)
    s = set(projects)
    distinct_projects = list(s)
    total_commits = 0
    for elem in commits:
        total_commits += int(elem[4])
    i = 0
    focus = 0
    while i < len(distinct_projects):
        num_commits = 0
        for elem in commits:
            if distinct_projects[i] == elem[1]:
                num_commits += int(elem[4])
        focus += (num_commits / (total_commits * 1.0)) * numpy.log2(num_commits / (total_commits * 1.0))
        i += 1
    focus = round(focus, 3)
    if focus == 0:
        return focus
    else:
        return -focus


def fsn(commits):
    projects = find_projects(commits)
    s = set(projects)
    distinct_projects = list(s)

    day = find_day(commits)
    s = set(day)
    distinct_day = list(s)
    distinct_day.sort()

    g = nx.DiGraph()
    for project in distinct_projects:
        g.add_node(project)

    i = 0
    while i < len(distinct_day) - 1:
        daily = []
        daily_next = []
        j = 0
        while j < len(commits):
            if distinct_day[i] == commits[j][2]:
                daily.append(commits[j])
            else:
                if distinct_day[i + 1] == commits[j][2]:
                    daily_next.append(commits[j])
            j += 1
        p_day = find_projects(daily)
        p_day_next = find_projects(daily_next)

        for project_d in p_day:
            for project_next in p_day_next:
                if g.number_of_edges() == 0:
                    g.add_edge(project_d, project_next, weight=1)
                else:
                    add = False
                    for (u, v, d) in g.edges(data='weight'):
                        if u == project_d and v == project_next:
                            g.add_edge(project_d, project_next, weight=d + 1)
                            add = True
                    if not add:
                        g.add_edge(project_d, project_next, weight=1)
        i += 1
    return g


def sswitch(commits):
    g = fsn(commits)
    projects = find_projects(commits)
    s = set(projects)
    distinct_projects = list(s)

    total_commits = 0
    for elem in commits:
        total_commits += int(elem[4])

    i = 0
    ss = 0
    while i < len(distinct_projects):
        num_commits = 0
        for elem in commits:
            if distinct_projects[i] == elem[1]:
                num_commits += int(elem[4])
        pi = (num_commits / (total_commits * 1.0))

        neighbors = list(g.neighbors(distinct_projects[i]))
        total_weight = 0
        pji_log = 0
        for node in neighbors:
            total_weight += (g[distinct_projects[i]][node]['weight'])

        for node in neighbors:
            pji = (g[distinct_projects[i]][node]['weight']) / (total_weight * 1.0)
            pji_log += pji * (numpy.log2(pji))
        ss += pi * pji_log
        i += 1
    ss = round(ss, 3)
    if ss == 0:
        return ss
    else:
        return -ss


def other_metrics(commits):
    total_commits = 0
    total_file_touches = 0
    total_files_touched = 0
    total_loc_added = 0
    total_loc_deleted = 0
    total_src_file_touches = 0
    total_src_files_touched = 0
    total_src_loc_added = 0
    total_src_loc_deleted = 0
    total_bugs = 0
    total_bug_inducing_commits = 0

    for elem in commits:
        total_commits += int(elem[idx_num_commits])
        total_file_touches += int(elem[idx_num_file_touches])
        total_files_touched += int(elem[idx_num_files_touched])
        total_loc_added += int(elem[idx_loc_added])
        total_loc_deleted += int(elem[idx_loc_deleted])
        total_src_file_touches += int(elem[idx_num_src_file_touches])
        total_src_files_touched += int(elem[idx_num_src_files_touched])
        total_src_loc_added += int(elem[idx_src_loc_added])
        total_src_loc_deleted += int(elem[idx_src_loc_deleted])
        total_bugs += int(elem[idx_num_bugs_induced])
        total_bug_inducing_commits += int(elem[idx_num_bugs_induced])

    return total_commits, total_file_touches, total_files_touched, total_loc_added, total_loc_deleted, total_bugs, \
           total_file_touches, total_files_touched, total_src_loc_added, total_src_loc_deleted, \
           total_bug_inducing_commits


def switches(commits):
    projects = find_projects(commits)
    i = 0
    switch = 0
    while i < len(projects) - 1:
        if projects[i] != projects[i + 1]:
            switch += 1
        i += 1
    return switch


"""
user_id;project;date;period(weeknumber/monthnumber);#commits;#num_file_touches;num_files_touched; #loc_added;#loc_deleted;#buildspassed;#buildsnotpassed;#travisprojects;#nontravisprojects;travisperiod
"""


def compute(data, aggregate_repos):
    results = []
    i = 0
    user = 0
    pos = []
    while i < len(data):
        # convert day to period
        day_i_period = convert_day_to_period(data[i][idx_day])
        # replace project with conceptualization
        data[i][idx_project] = aggregate_repos[data[i][idx_project]]
        commits = [data[i]]
        pos.append(0)
        j = 1
        while j < len(data):
            if data[i][idx_user_id] == data[j][idx_user_id] and \
                            day_i_period == convert_day_to_period(data[j][idx_day]):
                commits.append(data[j])
                pos.append(j)
            else:
                break
            j += 1

        if user != data[i][idx_user_id]:
            first_gtime = global_time(commits[0][idx_day])
            user = data[i][idx_user_id]

        gtime = global_time(commits[0][idx_day])
        user_time = gtime - first_gtime  # FIXME
        p_period = projects_at_period(commits)
        active_day, avg = avg_projects_per_day(commits)
        focus = sfocus(commits)
        ss = sswitch(commits)
        switch = switches(commits)
        n_commits, file_touches, files_touched, loc_added, loc_deleted, src_file_touches, src_files_touched, \
        src_loc_added, src_loc_deleted, bugs, bug_inducing_commits = other_metrics(commits)

        results.append((data[i][idx_user_id], day_i_period, gtime, user_time, p_period, avg, focus, ss, n_commits,
                        file_touches, files_touched, src_file_touches, src_files_touched, loc_added, loc_deleted,
                        src_loc_added, src_loc_deleted, active_day, switch, bugs, bug_inducing_commits))

        for elem in pos:
            data[elem] = "nil_nil"
        k = 0
        while k < len(data):
            if data[k] == "nil_nil":
                del data[k]
                k = 0
            else:
                k += 1
        # clear pos
        del pos[:]

    return results


def convert_day_to_period(day):
    _d = datetime.strptime(day, '%Y-%m-%d')
    day_as_period = datetime.strftime(_d, '%m-%Y')
    return day_as_period


if __name__ == '__main__':
    logger = loggingcfg.initialize_logger('SZZ')

    header = ["user_id", "project", "day", "num_commits", "num_file_touches", "num_src_file_touches",
              "num_files_touched", "num_src_files_touched", "loc_added", "src_loc_added", "loc_deleted",
              "src_loc_deleted", "num_bugs_induced", "num_bug_inducing_commits"]

    idx_user_id = header.index("user_id")
    idx_project = header.index("project")
    idx_day = header.index("day")
    idx_num_commits = header.index("num_commits")
    idx_num_file_touches = header.index("num_file_touches")
    idx_num_files_touched = header.index("num_files_touched")
    idx_loc_added = header.index("loc_added")
    idx_loc_deleted = header.index("loc_deleted")
    idx_num_src_file_touches = header.index("num_src_file_touches")
    idx_num_src_files_touched = header.index("num_src_files_touched")
    idx_src_loc_added = header.index("src_loc_added")
    idx_src_loc_deleted = header.index("src_loc_deleted")
    idx_num_bugs_induced = header.index("num_bugs_induced")
    idx_num_bug_inducing_commits = header.index("num_bug_inducing_commits")

    reader = CsvReader(csv_file=sys.argv[1], mode='r')
    rows = reader.readrows()
    data = []
    for r in rows:
        data.append(r)
    reader.close()
    del data[0]  # removes header from data

    projects = set()
    for d in data:
        projects.add(slugToFolderName(d[idx_project]))
    aggregate_repos, other = project_conceptualization_login(list(projects))
    aggregate_repos = project_conceptualization_repo(aggregate_repos, other)

    res = compute(data, aggregate_repos)

    writer = CsvWriter(csv_file='user_' + sys.argv[2] + '_aggr.csv', mode='w')
    # write field names in csv file
    writer.writerow(('UserID', 'Period', 'GlobalTime', 'UserTime', 'Projects', 'AvgProjectsPerDay', 'SFocus', 'SSwitch',
                     'Commits', 'FileTouches', 'FilesTouched', 'LocAdded', 'LocDeleted', 'DaysActive', 'Switches',
                     'Bugs', 'BugInducingCommits'))
    writer.writerows(res)
    writer.close()

    logger.info('Done.')
