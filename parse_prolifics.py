import getopt
import math
import os
import random
import socket
import sys
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor
from queue import Queue

import requests
from github import Github
from github.GithubException import GithubException, RateLimitExceededException

import loggingcfg
from csvmanager import CsvWriter
from gitutils.BaseGitHubThreadedExtractor import BaseGitHubThreadedExtractor
from gitutils.api_tokens import Tokens


class ProjectExtractor(BaseGitHubThreadedExtractor):
    def __init__(self, _tokens, t_queue, t_map):
        super().__init__(_tokens, t_queue, t_map)

    def replace_with_parent(self, repo, pid, g):
        parent = None
        try:
            parent = repo.parent
            # get the ancestor repo that is not a fork
            while parent is not None and parent.fork:
                parent = parent.parent
                self.wait_if_depleted(pid, g)
        except GithubException as ghe:
            logger.error(str(ghe))
        return parent

    def fetch_projects(self, dev_id):
        # pid = current_process().pid
        pid = threading.get_ident()
        projects = list()

        if dev_id in self.seen.keys():
            logger.info('[pid: {0}] Skipping {1}'.format(pid, dev_id))
            return dev_id, projects, pid, None, 'Skipped'
        else:
            self.seen[dev_id] = True

        logger.info('[pid: {0}] Processing {1}'.format(pid, dev_id))
        _token = self.reserve_token(pid)

        try:
            g = Github(_token)
            # check rate limit before starting
            self.wait_if_depleted(pid, g)
            logger.debug(msg="[pid: %s] Process not depleted, keep going." % pid)

            header = 'token ' + _token
            r = requests.get('https://api.github.com/user/%s' % dev_id, headers={'Authorization': header})
            try:
                login = r.json()['login']
            except KeyError as e:
                logger.warning("No login found for developer id %s" % dev_id)
                return dev_id, projects, pid, _token, str(e).strip().replace("\n", " ").replace("\r", " ")

            self.wait_if_depleted(pid, g)
            dev = g.get_user(login)
            self.wait_if_depleted(pid, g)
            repos = dev.get_repos()
            for r in repos:
                # we need to replace forks with their parent repository
                # there might be forks of forks, so we need to make the procedure "transitive"
                if r.fork:
                    r = self.replace_with_parent(r, pid, g)
                if r is not None and r.full_name.count('/') == 1:  # sanity check, some invalid slugs have multiple '/'
                    projects.append(r.full_name)
        except socket.timeout as e:
            traceback.print_exc(e)
            return dev_id, projects, pid, _token, str(e).strip().replace("\n", " ").replace("\r", " ")
        except RateLimitExceededException as e:  # safety check, shouldn't happen
            traceback.print_exc(e)
            return dev_id, projects, pid, _token, str(e).strip().replace("\n", " ").replace("\r", " ")
        except Exception as e:
            traceback.print_exc(e)
            return dev_id, projects, pid, _token, str(e).strip().replace("\n", " ").replace("\r", " ")

        # logger.debug((_token, ProjectExtractor.get_rate_limit(g)))
        self.release_token(pid, _token)
        return dev_id, projects, pid, _token, None

    def start(self, dev_ids, seen_ids, processed_ids_filename, processed_prj_filename):
        if seen_ids:
            logger.info("Restoring status from previous interrupted execution")
            dev_ids = [x for x in dev_ids if x not in seen_ids]
            processed_ids_f = open(file=processed_ids_filename, mode='a')
            processed_prj_f = open(file=processed_prj_filename, mode='a')
        else:
            processed_ids_f = open(file=processed_ids_filename, mode='w')
            processed_prj_f = open(file=processed_prj_filename, mode='w')

        log_writer = CsvWriter(os.path.join(os.curdir, 'extracted-projects-error.log'), 'a')

        _len = len(dev_ids)
        max_workers = 1#self.tokens.length()
        # get list of dev_ids split into chucks of size max_workers

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            _counter = 0
            try:
                results = executor.map(self.fetch_projects, sorted(dev_ids))
                for result in results:
                    (dev_id, user_projects, pid, _token, error) = result
                    if error is not None:
                        logger.error(msg=[dev_id, error])
                        log_writer.writerow([dev_id, error])
                        log_writer.flush()

                    for up in user_projects:
                        processed_prj_f.write(up + "\n")
                    processed_ids_f.flush()
                    processed_ids_f.write("%s\n" % dev_id)
                    processed_ids_f.flush()
                    _counter += 1
                    logger.info(
                        'Done processing projects for user {0} ({1}/{2}).'.format(dev_id, _counter, _len))
            except Exception as e:
                logger.error("Error processing dev_ids\n\n")
                traceback.print_exc()
                logger.error(str(e))

        log_writer.close()
        processed_ids_f.close()
        processed_prj_f.close()


def sample_size(population_size, confidence_level=.99, confidence_interval=.05):
    """
    Calculate the minimal sample size to use to achieve a certain margin of error and confidence level for a sample
    estimate of the population mean.

    :param population_size: Total size (int) of the population that the sample is to be drawn from.
    :param confidence_interval: Maximum expected difference between the true population parameter, such as the mean, and the
                         sample estimate.
    :param confidence_level: number in the interval (0, 1). If we were to draw a large number of equal-size samples from
                             the population, the true population parameter should lie within this percentage
                             of the intervals (sample_parameter - e, sample_parameter + e) where e is the margin_error.
    :param sigma: The standard deviation of the population. For the case of estimating a parameter in the interval
                  [0, 1], sigma=1/2 should be sufficient.
    :returns s_size: The sample size
    """
    alpha = 1 - confidence_level
    # dictionary of confidence levels and corresponding z-scores
    # computed via norm.ppf(1 - (alpha/2)), where norm is
    # a normal distribution object in scipy.stats.
    # Here, ppf is the percentile point function.
    z_dict = {
        .90: 1.645,
        .91: 1.695,
        .92: 1.751,
        .93: 1.812,
        .94: 1.881,
        .95: 1.960,
        .96: 2.054,
        .97: 2.170,
        .98: 2.326,
        .99: 2.576
    }
    if confidence_level in z_dict:
        z = z_dict[confidence_level]
    else:
        from scipy.stats import norm
        z = norm.ppf(1 - (alpha / 2))
        if z == 0.0:
            raise ValueError("Sample size calculation error z = 0.0")

    n = population_size
    p = 0.5
    e = confidence_interval / 100.0

    n_0 = ((z ** 2) * p * (1 - p)) / (e ** 2)
    n = n_0 / (1 + ((n_0 - 1) / float(n)))

    return int(math.ceil(n))


def random_selection(population, conf, seed):
    random.seed(seed)
    random.shuffle(population)
    k = sample_size(population_size=len(population), confidence_level=conf, confidence_interval=1.0)
    if len(population) < k:
        k = len(population)
    selection = random.sample(population, k)
    return selection


if __name__ == '__main__':
    import logging

    logger = loggingcfg.initialize_logger(name='SZZ:PROLIFICS', console_level=logging.INFO)

    prolific_infile = "prolifics.txt"
    #prolific_ids = None
    prolific_prj = None
    projects_outfile = "project-list"
    seed = 895
    conf_level = .95
    subsample = False

    processed_ids_filename = "tmp/prolific/temp.ids"
    processed_prj_filename = "tmp/prolific/temp.projects"
    seen_ids = set()

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:o:c:s:r", ["in=", "out=", "conflev=", "seed=", "random", "help"])
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print('Usage:\n parse_prolifics.py -i|--in <file> -o|--out <file> -s|--seed N [-c|--conflev M]')
                sys.exit(0)
            elif opt in ("-i", "--in"):
                prolific_infile = arg
                assert os.path.exists(os.path.join(os.path.curdir, prolific_infile)), "Input file does not exist"
            elif opt in ("-o", "--out"):
                projects_outfile = arg
            elif opt in ("-c", "--conflev"):
                conf_level = float(arg)
                assert conf_level in {.95, .99}, "Confidence level must be either .95 or .99"
            elif opt in ("-s", "--seed"):
                seed = int(arg)
            elif opt in ("-r", "--random"):
                subsample = True
            else:
                assert False, "unhandled option"
    except getopt.GetoptError as err:
        # print help information and exit:
        logger.error(err)  # will print something like "option -a not recognized"
        print('Usage:\n parse_prolifics.py -i|--in <file> -o|--out <file> -s|--seed N [-c|--conflev M]')
        sys.exit(1)

    if subsample:
        logger.info("Generating a random subsample of prolific developers.")

        with open(file=prolific_infile, mode='r') as _f:
            dev_ids = _f.readlines()
        assert dev_ids is not None
        dev_ids = dev_ids[1:]  # removes header
        assert len(dev_ids) > 0
        dev_ids = [int(i.strip()) for i in dev_ids]  # removes trailing \n

        logger.info("Selecting random subsample of developers to achieve confidence level of %s." % conf_level)
        select_prolific = random_selection(dev_ids, conf_level, seed)
        with(open(file="prolifics-%s.txt" % seed, mode='w')) as f:
            for sp in select_prolific:
                f.write(str(sp) + "\n")
        logger.info("The selected random subsample is saved to file prolifics-%s.txt" % seed)

    else:
        logger.info("Retrieving the set of projects that prolific developers work on.")

        tokens = Tokens()
        tokens_iter = tokens.iterator()
        tokens_queue = Queue()
        for token in tokens_iter:
            tokens_queue.put(token)
        tokens_map = dict()

        # load processed ids to avoid duplicates
        try:
            with(open(file=processed_ids_filename, mode='r')) as f:
                seen_ids = f.readlines()
                seen_ids = sorted([int(i.strip()) for i in seen_ids])
        except:
            pass

        # load ids of dev to process
        with open(file=prolific_infile, mode='r') as _f:
            dev_ids = _f.readlines()
        assert dev_ids is not None
        dev_ids = [int(i.strip()) for i in dev_ids]  # removes trailing \n
        assert len(dev_ids) > 0

        logger.info("Beginning data extraction.")
        extractor = ProjectExtractor(tokens, tokens_queue, tokens_map)
        extractor.start(dev_ids, seen_ids, processed_ids_filename, processed_prj_filename)

        logger.info("Saving list of projects worked on by sampled prolific developers")
        with(open(file=processed_prj_filename, mode='r')) as f:
            prolific_prj = f.readlines()
            prolific_prj = sorted(set([x.strip() for x in prolific_prj]))
            with open(file="{0}-{1}.txt".format(projects_outfile.split('.')[0], seed), mode='w') as f:
                for p in prolific_prj:
                    f.write(p + "\n")

        logger.debug("Removing temp files")
        os.remove(processed_ids_filename)
        os.remove(processed_prj_filename)

    logger.info("Done.")
