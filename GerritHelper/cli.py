import click
import gitapi
import webbrowser
import sys
import tabulate
import gitutil
import tempfile
import os
from subprocess import call
from gitapi.gitapi import GitException
import time
import diff2html


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


def squash_commits(orig_branch, repo, working_branch):
    repo.git_checkout(orig_branch)
    repo.git_branch('gerrit_tmp')
    repo.git_checkout('gerrit_tmp')
    print repo.git_command('merge', '--squash', working_branch)
    if working_branch.startswith('B_'):
        commit_message = open_editor('BUGFIX')
    else:
        commit_message = open_editor('FEATURE')
    repo.git_commit(commit_message)
    print repo.git_command('branch', '-M', working_branch)


@main.command()
def review():
    repo = gitapi.Repo("./")
    working_branch, orig_branch = extract_branch_name(repo)

    try:
        if 'rebasing' in repo.git_command('status'):
            print 'Current repo is in rebase progress'
            try:
                print repo.git_command('status')
                repo.git_command('add','-u')
                print repo.git_command('status')
                repo.git_command('rebase','--continue')
                # working_branch, orig_branch = extract_branch_name(repo)
                # gitutil.squash_commits(repo,working_branch,orig_branch)
                # print repo.git_command('push','gerrit','HEAD:refs/publish/%s/%s%%r=%s' % (orig_branch, working_branch,'wangchengming')) # FIXME: comment out for test
            except GitException,e:
                print e.message
            return

        try:
            # working_branch, orig_branch = extract_branch_name(repo)
            print_status_start('Update %s branch' % (orig_branch))
            repo.git_checkout(orig_branch)
            # try:   # FIXME: comment out for test
            #     repo.git_pull()
            # except Exception: # pull failure, rollback
            #     print 'Failed update '+orig_branch+' from remote repo'
            #     repo.git_checkout(working_branch)
            #     return
            print_status_end('Update %s branch' % (orig_branch),True)
            repo.git_checkout(working_branch)
            print_status_start('Squash commits')
            result = gitutil.squash_commits(repo,working_branch,orig_branch)
            if result is not None:
                print result
                print_status_end('Squash commits',False)
                return
            else:
                print_status_end('Squash commits',True)
            try:
                print_status_start('Rebasing')
                repo.git_command('rebase', orig_branch) # may fail
                print_status_end('Rebasing',True)
            except Exception:
                print "Failed rebasing %s from %s" % (working_branch,orig_branch)
                print ""
                stat = repo.git_command('status')
                for line in stat.split('\n'):
                    if line.startswith('You') or \
                            line.startswith('  (') or \
                            line.startswith('Unmerged') or \
                            line.startswith('no changes') or \
                            line.startswith('rebase in progress'):
                        continue
                    print line
                print 'Fix conflicts and run "gh review" again'
                return
            # gitutil.squash_commits(repo,working_branch,orig_branch)
            # print repo.git_command('push','gerrit','HEAD:refs/publish/%s/%s%%r=%s' % (orig_branch, working_branch,'wangchengming')) # FIXME: comment out for test
        except GitException,e:
            print e.message
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


@main.command()
def diff():
    # try:
    repo = gitapi.Repo("./")
    tmp_html_file = os.path.join(tempfile.gettempdir(),'gell.html')
    tmp_diff_file = os.path.join(tempfile.gettempdir(),'gell.diff')
    os.system('git diff -U50 B_master_fix5 master > '+tmp_diff_file)
    # result = repo.git_command('diff','-U99999999','B_master_fix5','master')
    # with tempfile.NamedTemporaryFile(suffix=".tmp",mode='w+') as temp_fp:
    #     temp_fp.write(result)
    #     temp_fp.flush()
    #     tmp_html_file = os.path.join(tempfile.gettempdir(),'gell.html')
    diff2html.make_diff_html(tmp_diff_file,tmp_html_file)
    webbrowser.open('file://'+tmp_html_file)
    # except Exception,e:
    #     print e.message


def extract_branch_name(repo):
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
    return working_branch, orig_branch

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


def print_status_start(message):
    print '%-30s' % (message),


def print_status_end(message,success):
    if success:
        print '%10s' % '[OK]'
    else:
        print '\n%-30s%10s' % (message,'[FAILURE]')

if __name__ == '__main__':
    print open_editor('BUGFIX')