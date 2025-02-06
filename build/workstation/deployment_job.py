"""
Deployment job script that checks if there are new commits on `feld-m-ragkb-main` branch.
In case there are, they are fetch to local branch and deployment is triggered.

Run `uv pip install GitPython` before running the script.
"""

import subprocess
import sys

import git

REPOSITORY_PATH = "/home/feld/repos/ragkb/"
BRANCH_NAME = "feld-m-ragkb-main"
DEPLOYMENT_SCRIPT_PATH = REPOSITORY_PATH + "build/workstation/deploy.sh"


def get_local_repo() -> git.Repo:
    try:
        return git.Repo(REPOSITORY_PATH)
    except git.exc.InvalidGitRepositoryError:
        print("Error: Current directory is not a git repository.")
        sys.exit(1)


def get_local_branch(repo: git.Repo) -> git.Head:
    try:
        return repo.heads[BRANCH_NAME]
    except IndexError:
        print(f"Error: Local branch '{BRANCH_NAME}' does not exist.")
        sys.exit(2)


def get_origin_remote(repo: git.Repo) -> git.Remote:
    try:
        return repo.remotes.origin
    except AttributeError:
        print("Error: Remote 'origin' not found.")
        sys.exit(3)


def get_remote_branch(remote: git.Remote) -> git.RemoteReference:
    try:
        return remote.refs[BRANCH_NAME]
    except IndexError:
        print(
            f"Error: Remote branch '{BRANCH_NAME}' not found on remote 'origin'."
        )
        sys.exit(4)


def get_merge_base(
    repo: git.Repo, local_commit: git.Commit, remote_commit: git.Commit
) -> git.Commit:
    merge_bases = repo.merge_base(local_commit, remote_commit)
    if not merge_bases:
        print("Error: No merge base found between local and remote branches.")
        sys.exit(1)
    return merge_bases[0]


def is_remote_ahead(
    merge_base: git.Commit, local_commit: git.Commit, remote_commit: git.Commit
) -> bool:
    return (
        merge_base == local_commit
        and local_commit.hexsha != remote_commit.hexsha
    )


def deploy():
    deploy_command = [DEPLOYMENT_SCRIPT_PATH]
    try:
        subprocess.run(deploy_command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing deployment command: {e}")
        sys.exit(5)


def main():
    repo = get_local_repo()
    local_branch = get_local_branch(repo)
    origin = get_origin_remote(repo)

    print("Fetching remote changes...")
    origin.fetch()

    remote_branch = get_remote_branch(origin)
    local_commit = local_branch.commit
    remote_commit = remote_branch.commit
    merge_base = get_merge_base(repo, local_commit, remote_commit)

    if is_remote_ahead(merge_base, local_commit, remote_commit):
        print("Remote branch is ahead of the local branch.")
        print("Pulling changes into local branch...")
        try:
            repo.git.pull("origin", BRANCH_NAME)
            print("Local branch updated successfully.")
            print("Starting deployment.")
            deploy()
            print("Deployment command executed successfully.")
        except Exception as e:
            print(f"Error while pulling changes: {e}")
            sys.exit(1)
    else:
        print("Local branch is up-to-date with the remote branch.")


if __name__ == "__main__":
    main()
