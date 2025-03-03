![image](https://github.com/user-attachments/assets/93e51be7-67b9-4625-82c4-91a7a937616b)

# Kanely

Self-Hosted Kanban app! Keep track of tasks without any data leaving your servers.

Supports multiple users, sharing boards to other users, and self-service onboarding.

# To Use

## Docker

```
git clone
cd kanely
sudo docker built -t kanely .
sudo docker run -p 5000:5000 kanely
```

## Python

```
git clone
cd kanely
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python src/run.py
```

Note - this uses the WSGI server that ships with Flask. Do not use in outward-facing deployments.

