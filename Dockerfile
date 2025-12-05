FROM python:3.9-slim

WORKDIR /app
COPY game_node.py .

CMD ["python", "game_node.py"]