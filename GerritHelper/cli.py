import click
import gitapi
from gitapi.gitapi import GitException


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

if __name__ == '__main__':
    main()