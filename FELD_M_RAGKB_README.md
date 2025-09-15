# FELD M RAG Knowledge Base

RAG System for FELD M Sales Documents written on top of [RAG Blueprint](https://github.com/feld-m/rag_blueprint).

## Automatic Deployment

Public Github repository doesn't have access to this machine, so it cannot triggered deployment (e.g. via ssh) through Github Actions. Instead, we create a script `deployment_job.sh` that pulls `feld-m-ragsd-main` branch every hour and in case there are changes deployment script `deploy.sh` is invoked. To enable this process make `deployment_job.sh` and `deploy.sh` executable:

```bash
chmod +x deployment_job.sh
chmod +x deploy.sh
```

Then add the following line to crontab to schedule the job:

```bash
0 * * * * /bin/bash -l -c "/home/feld/repos/ragsd/build/workstation/deployment_job.sh -b feld-m-ragsd-main -d /home/feld/repos/ragsd/ >> /home/feld/repos/ragsd/build/workstation/logs/deployment_job.log 2>&1"
```
