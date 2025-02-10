#!/bin/sh
branch="feld-m-ragkb-main"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Deployment job started for branch $branch."

cd /home/feld/repos/ragkb/
git checkout $branch

if git pull | grep -q 'Already up to date.'; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Everything is up to date for branch $branch."
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] New changes were pulled for branch $branch. Starting deployment."
    . .venv/bin/activate
    build/workstation/deploy.sh
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Deployment job finished for branch $branch."
exit 0
