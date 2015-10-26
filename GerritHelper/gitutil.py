import gitapi
import os
import tempfile
from subprocess import call

class GitRepoAdapter:

    GULL_STAT_PUSHED = 1 # already pushed to gerrit for review

    def __init__(self,working_branch,orig_branch,repo_path):
        self.__repo_path = repo_path
        self.__gull_root = os.path.join(repo_path,'.gull')
        if not os.path.exists(self.__gull_root):
            os.makedirs(self.__gull_root)
        self.__working_branch = working_branch
        self.__orig_branch = orig_branch
        self.__repo = gitapi.Repo(repo_path)

    def __get_commits(self,branch_name):
        return self.__repo.git_command('rev-list','-n','100',branch_name).strip().split('\n')

    def __get_review_commit(self):
        if os.path.exists(os.path.join(self.__gull_root,self.__working_branch)):
            with open(os.path.join(self.__gull_root,self.__working_branch)) as fp:
                return fp.readline().strip()

    def get_gull_status(self):
        review_commit = self.__get_review_commit()
        head = self.__get_commits(self.__working_branch)[0]
        if head==review_commit:
            return GitRepoAdapter.GULL_STAT_PUSHED
        return -1

    def push_to_gerrit(self):
        self.__repo.git_checkout(self.__working_branch)
        # TODO: push
        head = self.__get_commits(self.__working_branch)[0]
        with open(os.path.join(self.__gull_root,self.__working_branch),'w') as fp:
            fp.write(head)




def squash_commits(repo, working_branch, orig_branch, max_commit_history=100):
    '''
    working branch has already rebased to orig branch, so the HEAD of orig branch should be the commit to squash
    :param repo:
    :param working_branch:
    :param orig_branch:
    :param max_commit_history:
    :return:
    '''
    orig_branch_commits = repo.git_command('rev-list','-n',str(max_commit_history),orig_branch).strip().split('\n')
    working_branch_commits = repo.git_command('rev-list','-n',str(max_commit_history),working_branch).strip().split('\n')
    common_commit = None
    for commit in orig_branch_commits:
        if commit in working_branch_commits:
            common_commit = commit
            break
    if common_commit is None:
        raise Exception("Branch %s and %s have no common commit in nearest %d commits" % (working_branch,orig_branch,max_commit_history))

    commit_count = working_branch_commits.index(common_commit)
    if commit_count==0:
        raise Exception("HEAD of branch %s and %s are at the same point" % (working_branch,orig_branch))
    commit_history = repo.git_command('rev-list','--format=full','--max-count='+str(commit_count),working_branch_commits[0]).strip().split('\n')

    repo.git_command('reset','--soft',common_commit)
    if working_branch.startswith('B_'):
        commit_message = open_editor('BUGFIX',commit_history)
    else:
        commit_message = open_editor('FEATURE',commit_history)
    repo.git_commit(commit_message)


def open_editor(branch_type, msg):
    '''
    :param branch_type
    :param the old commit history
    '''
    EDITOR = os.environ.get('EDITOR','vim') #that easy!

    initial_message = '''[%s:GROUP] The Commit title

The detailed message

''' % (branch_type)
    for line in msg:
        initial_message = initial_message+"# "+line+"\n"
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


if __name__ == '__main__':
    g = GitRepoAdapter('BUGFIX_master_1234','master','/Users/susuxixi/Documents/projects/test/Fusion')
    print g.get_gull_status()
