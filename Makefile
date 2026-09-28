.PHONY: run test install docker-build docker-run docker-compose-up

# Local Development Commands
run:
	venv/Scripts/streamlit run app.py

test:
	venv/Scripts/python -m pytest tests/

install:
	venv/Scripts/pip install -r requirements.txt

# Docker Deployment Commands
docker-build:
	docker build -t urban-mobility-app .

docker-run:
	docker run -p 8501:8501 urban-mobility-app

docker-compose-up:
	docker-compose up --build
