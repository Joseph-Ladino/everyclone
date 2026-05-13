@echo off

docker build -t dioswneddev/ep-frontend:latest ./frontend
docker built -t dioswneddev/ep-backend:latest ./backend

docker push dioswneddev/ep-frontend:latest
docker push dioswneddev/ep-backend:latest