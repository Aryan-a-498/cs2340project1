## Prerequisites
- Python 3.11+
- pip

## Setup Instructions

1. Clone repo:
```
git clone https://github.com/Aryan-a-498/cs2340project1.git
cd cs2340project1
```

2. Setup virtual environment (for all dependencies)
- Might have to use python instead of python3 depending on computer
```
# Mac/Linux
python3 -m venv .venv
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# Windows (cmd)
.venv\Scripts\activate.bat
```

3. Install dependencies:
- Might have to use pip instead of pip3 depending on computer
```
pip3 install -r requirements.txt
```

4. Create .env file from template (.env.example)
```
cp .env.example .env
```
- After doing this add the SECRET_KEY

## Working on project

When working on user story, first pull changes into your main branch (in case someone made changes):
```
git checkout main
git pull origin main
```

Then create a branch to work on:

```
git checkout -b <branch_name_goes_here>
```

Then make your changes and commit them, and when you're done and have tested your changes merge into main and push
```
#From your branch
git add .
git commit -m "<commit_message_here>"

#Then go to main
git checkout main
git pull origin main

git merge <your-branch>

git push origin main
```

## Database Migrations

Django tracks database changes as "migrations" - in order for us to stay in sync, there are some important commands to know:

**`python manage.py makemigrations`**

Generates migration files based on any changes you've made to a model (new field, new model, etc.). Run this after you edit `models.py`.
- If you work on changes to  `models.py`, this will actually make a migrations file which you should commit. When we want to use those changes as long as we have your migration file locally we can then run the following command: 

**`python manage.py migrate`**

Applies migration files to your actual local database. Run this after running `makemigrations` yourself, and after pulling new commits from someone on the team that include migration files, so your local database reflects their model changes too.