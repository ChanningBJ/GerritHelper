import click
import gitapi
import sys
import tabulate

import tempfile
import os
from subprocess import call
from gitapi.gitapi import GitException
import time


@click.group()
def main():
    pass


@main.command()
@click.argument('branch', required=True)
@click.argument('task', required=True)
@click.option('--bug', '-b', is_flag=True, help='The task is a bug fix ')
@click.option('--feature', '-f', is_flag=True, help='The task is a new feature')
def start(branch, task, bug, feature):
    if feature :
        branch_name = "F_%s_%s" % (branch,task)
    else:
        branch_name = "B_%s_%s" % (branch,task)
    try:
        repo = gitapi.Repo("./")
        repo.git_checkout(branch)
        repo.git_pull()
        repo.git_branch(branch_name)
        repo.git_checkout(branch_name)
    except GitException,e:
        print e.message
    else:
        print "New branch %s created from %s" % (branch_name, branch)


@main.command()
def review():
    try:
        repo = gitapi.Repo("./")
        branches = [ k for k in repo.git_command('branch').split('\n') if k.startswith('*')]
        if len(branches) != 1 :
            print "Not in any branch ?"
            return
        working_branch = branches[0].replace('* ','')
        items = working_branch.split('_')
        if len(items)!=3:
            print working_branch,'not created using gh tool, should not send to review using gh tool'
            return
        orig_branch = items[1]

        repo.git_checkout(orig_branch)
        # repo.git_pull() #FIXME: pull may fail
        repo.git_checkout(working_branch)
        print repo.git_command('rebase', orig_branch) # may fail
        repo.git_checkout(orig_branch)
        repo.git_branch('gerrit_tmp')
        repo.git_checkout('gerrit_tmp')
        print repo.git_command('merge', '--squash', working_branch)
        if working_branch.startswith('B_'):
            commit_message = open_editor('BUGFIX')
        else:
            commit_message = open_editor('FEATURE')
        repo.git_commit(commit_message)
        print repo.git_command('branch','-M',working_branch)
        print repo.git_command('push','gerrit','HEAD:refs/publish/%s/%s%%r=%s' % (orig_branch, working_branch,'wangchengming')) # FIXME: change reviewer
    except GitException,e:
        print e.message


@main.command()
@click.argument('filename', required=True)
def add(filename):
    try:
        repo = gitapi.Repo("./")
        print repo.git_add(filename)
    except GitException,e:
        print e.message




def open_editor(title):
    EDITOR = os.environ.get('EDITOR','vim') #that easy!

    initial_message = '''[%s:GROUP] The Commit title

The detailed message
    ''' % (title)
    # temp_fp = tempfile.NamedTemporaryFile()
    # temp_file_name = temp_fp.name
    # print temp_file_name
    # temp_fp.write(initial_message)
    # temp_fp.flush()
    # temp_fp.close()
    # call([EDITOR, temp_fp.name])
    #
    # fp = open(temp_file_name)
    # print fp.readlines();
    #
    with tempfile.NamedTemporaryFile(suffix=".tmp",mode='w+') as temp_fp:
        temp_fp.write(initial_message)
        temp_fp.flush()
        # print call([EDITOR, temp_fp.name])
        call(EDITOR + ' ' +temp_fp.name, shell=True)
        with open(temp_fp.name) as fp:
            content = fp.readlines()
            return ''.join(content)
        # call('cat '+temp_fp.name, shell=True)
        # temp_fp.flush()
        # temp_fp.seek(0,0)
        # print temp_fp.read()

    # do the parsing with `tempfile` using regular File operations
if __name__ == '__main__':
    print open_editor('BUGFIX')