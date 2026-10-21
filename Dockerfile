FROM python:3.12-slim
WORKDIR /app
COPY matchmind matchmind
COPY web web
ENV PORT=8000
EXPOSE 8000
CMD ["python", "-m", "matchmind.server"]
