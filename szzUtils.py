# import fnmatch, glob
# import ctypes
import logging
import os
import re
from datetime import datetime, timezone, timedelta

import pytz

logger = logging.getLogger('SZZ')

RE_COMMENT = r'^([ \t]*(#|(\\\*)|(\*\*)|(//)|(/\*))|[ \t]*$)'
regex_comment = re.compile(RE_COMMENT)
# code change type in diff
CG_CODE = 0
CG_COMMENT = 1


def isComment(line):
    match = regex_comment.match(line)
    if match:
        return CG_COMMENT
    else:
        return CG_CODE


def slugToFolderName(slug):
    if slug is None:
        return None
    return '_____'.join(slug.split('/'))


def folderNameToSlug(folder_name):
    if folder_name is None:
        return None
    return '/'.join(folder_name.split("_____"))


RE_ISSUE_ID = re.compile(r'[^a-zA-Z0-9_#/](\#\d+)\b')
RE2_ISSUE_ID = re.compile(r'\b(GH-\d+)\b')


class CommitWrapper:
    def __init__(self,
                 commit):
        self.commit = commit

    def getSha(self):
        return self.commit.hex

    def getCommitter(self):
        return (self.commit.committer.name, self.commit.committer.email)

    def getAuthor(self):
        return (self.commit.author.name, self.commit.author.email)

    def _formatDate(self, dt):
        return dt.strftime('%Y-%m-%d %H:%M:%S')

    def getCommittedDate(self):
        tzinfo = timezone(timedelta(minutes=self.commit.committer.offset))
        dt = datetime.fromtimestamp(float(self.commit.committer.time), tzinfo).astimezone(pytz.utc)
        return dt

    def getAuthoredDate(self):
        tzinfo = timezone(timedelta(minutes=self.commit.author.offset))
        dt = datetime.fromtimestamp(float(self.commit.author.time), tzinfo).astimezone(pytz.utc)
        return dt

    def getMessage(self):
        return self.commit.message

    def getIssueIds(self):
        results = []
        for (line_num, line) in enumerate(self.getMessage().split('\n')):
            matches = set([int(m[1:]) for m in re.findall(RE_ISSUE_ID, line)])
            matches.update(set([int(m[3:]) for m in re.findall(RE2_ISSUE_ID, line)]))
            if matches:
                results.append((line_num + 1, sorted(matches)))
        return results

    def getParents(self):
        return self.commit.parents

    def getDiff(self, repo):
        return repo.diff(self.commit.parents[0], self.commit, context_lines=0)

    @staticmethod
    def get_src_changes(basic_classifier, diff):
        src_loc_added = 0
        src_loc_deleted = 0
        num_src_files_touched = 0
        src_files = []
        all_files = []
        for patch in diff:
            if not patch.delta.is_binary:
                """
                unlike the blame part, here we look at the new files of the patch
                as they contain both the old files that are being modified, plus
                the new ones, just created from scratch
                """
                f = patch.delta.new_file
                all_files.append(os.path.basename(f.path))
                if basic_classifier.labelFile(f.path) != basic_classifier.DOC:  # not a doc file
                    num_src_files_touched += 1
                    src_files.append(os.path.basename(f.path))
                    for hunk in patch.hunks:
                        for hl in hunk.lines:
                            if hl.origin == '-':
                                src_loc_deleted += 1
                            elif hl.origin == '+':
                                src_loc_added += 1
                else:
                    logger.debug("Skipped doc file %s" % f.path)
            else:
                logger.debug("Skipped binary delta.")
        if src_files:
            src_files = ','.join(src_files)
        else:
            src_files = ''
        if all_files:
            all_files = ','.join(all_files)
        else:
            all_files = ''
        return all_files, src_files, num_src_files_touched, src_loc_added, src_loc_deleted
