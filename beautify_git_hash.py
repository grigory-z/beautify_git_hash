#!/usr/bin/env python

"""Beautify the Git commit hash!

This is a little useless toy inspired by BitCoin's "proof of work"
concept. It allows you to modify your Git commit to enforce a
certain prefix on the Git commit hash.

Start this script from within your Git repository, and specify
the prefix you want your last commit to have:

    ./beautify_git_hash.py 0001a

It proposes a Git command that adjusts the committer timestamp
and author timestamp accordingly:

    Proposal:
    GIT_COMMITTER_DATE='1317498969 +0200' git commit --amend -C HEAD --date='1317498857 +0200'

The timestamps will only be increased, i.e. they change to the
future and never to the past. Also, they won't be increased by
more than 30 minutes, and the author timestamp will never be
increased more than the committer timestamp. This should keep
the timestamps sane.

Note that there is always a small risk of failure in this kind
of algorithm. So if you are unlucky, you will get an error
message:

    Traceback (most recent call last):
      ...
    Exception: Unable to find beautiful hash!

In that case you can either chosse a different prefix (maybe a
shorter one), or you can modify your commit slightly (maybe just
the commit message). Then try again.

Have fun!



Copyright (C) 2011 by Volker Grabsch <vog@notjusthosting.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import hashlib
import subprocess
import sys

def subprocess_check_output(cmd):
    if hasattr(subprocess, 'check_output'):
        # Python >= 2.7
        return subprocess.check_output(cmd)
    else:
        # Python < 2.7
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        output, error = process.communicate()
        retcode = process.poll()
        if retcode:
            raise subprocess.CalledProcessError(retcode, cmd)
        return output

def load_git_commit(commit_id):
    return subprocess_check_output(['git', 'cat-file', 'commit', commit_id])

def git_commit_hash(commit):
    object = 'commit %i\x00%s' % (len(commit), commit)
    return hashlib.sha1(object).hexdigest()

def commit_line_to_format(line, aggregate_values):
    format_words = line.replace('%', '%%').split(' ')
    if format_words[0] == 'author':
        aggregate_values['author_date_timestamp'] = int(format_words[-2])
        aggregate_values['author_date_tz'] = format_words[-1]
        format_words[-2] = '%(author_date_timestamp)i'
    elif format_words[0] == 'committer':
        aggregate_values['committer_date_timestamp'] = int(format_words[-2])
        aggregate_values['committer_date_tz'] = format_words[-1]
        format_words[-2] = '%(committer_date_timestamp)i'
    return ' '.join(format_words)

def commit_to_format(commit):
    aggregate_values = {}
    commit_format = '\n'.join(commit_line_to_format(line, aggregate_values)
                              for line in commit.split('\n'))
    return commit_format, aggregate_values

def find_beautiful_git_hash(old_commit, prefix, max_minutes=30):
    commit_format, old_values = commit_to_format(old_commit)
    for committer_date_offset in xrange(max_minutes * 60 + 1):
        for author_date_offset in xrange(committer_date_offset + 1):
            new_values = {
                'author_date_timestamp': old_values['author_date_timestamp'] + author_date_offset,
                'committer_date_timestamp': old_values['committer_date_timestamp'] + committer_date_offset,
            }
            commit = commit_format % new_values
            if git_commit_hash(commit).startswith(prefix):
                if author_date_offset == committer_date_offset == 0:
                    return None
                else:
                    return "GIT_COMMITTER_DATE='%i %s' git commit --amend -C HEAD --date='%i %s'" % (
                        new_values['committer_date_timestamp'],
                        old_values['committer_date_tz'],
                        new_values['author_date_timestamp'],
                        old_values['author_date_tz'],
                    )
    raise Exception('Unable to find beautiful hash!')

def main():
    try:
        _, prefix = sys.argv
    except:
        print >>sys.stderr, 'Usage: %s PREFIX' % (sys.argv[0],)
        sys.exit(1)
    proposal = find_beautiful_git_hash(load_git_commit('HEAD'), prefix)
    if proposal is None:
        print 'Nothing to do'
    else:
        print 'Proposal:'
        print proposal

if __name__ == '__main__':
    main()
