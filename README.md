## Prerequisites
- Python 3.11+
- pip

## Setup Instructions

1. Clone repo:
```
git clone https://github.com/Aryan-a-498/cs2340project1.git
```

2. Setup virtual environment (for all dependencies)
- Might have to use python instead of python3 depending on computer
```
python3 -m venv .venv
source .venv/bin/activate
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

## Working on project

When working on user story, first pull changes into your main branch (incase someone made changes):
```
git checkout main; git pull
```

Then create a branch to work on:

```
git checkout -b <branch_name_goes_here>
```

Then make your changes and commit them, and when you're feeling good push to main
```
git commit -m "<commit_message_here>"

git push
```