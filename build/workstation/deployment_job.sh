#!/bin/sh

# ===============================================================
# RAG Blueprint Deployment Job Script
# ===============================================================
# Purpose: Automates branch deployment by checking for updates
#          and running deployment only when new changes exist
# Usage: ./deployment_job.sh -b <branch> -d <repo_path>
# Example: ./deployment_job.sh -b main -d /path/to/repo
# ===============================================================

# ===== VARIABLES SETUP =====
# Initialize variables to hold command line parameters
branch=""
repo_path=""

# ===== ARGUMENT PARSING =====
# Parse command-line arguments using getopts
while getopts "b:d:h" opt; do
  case $opt in
    b) branch="$OPTARG" ;;
    d) repo_path="$OPTARG" ;;
    h)
       echo "Usage: $0 [-b branch] [-d repo_path]"
       echo "  -b  Git branch to deploy (default: $branch)"
       echo "  -d  Repository directory path (default: $repo_path)"
       echo "  -h  Show this help message"
       exit 0
       ;;
    \?) echo "Invalid option: -$OPTARG" >&2; exit 1 ;;
  esac
done

# ===== PARAMETER VALIDATION =====
# Check if required parameters are provided
if [ -z "$branch" ]; then
  echo "Error: Branch (-b) parameter is required"
  echo "Use -h for help"
  exit 1
fi

if [ -z "$repo_path" ]; then
  echo "Error: Repository path (-d) parameter is required"
  echo "Use -h for help"
  exit 1
fi

# ===== DEPLOYMENT PROCESS =====
# Log the start of the deployment process
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Deployment job started for branch $branch."

# Navigate to the repository directory
cd $repo_path || { echo "Error: Unable to change directory to $repo_path"; exit 1; }

# Checkout the specified branch
git checkout $branch

# Pull latest changes and check if updates are available
if git pull --rebase | grep -q 'Already up to date.'; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Everything is up to date for branch $branch."
else
    # Run deployment procedure when updates are detected
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] New changes were pulled for branch $branch. Starting deployment."
    . .venv/bin/activate
    build/workstation/deploy.sh --env prod
fi

# Log completion of deployment job
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Deployment job finished for branch $branch."
exit 0
