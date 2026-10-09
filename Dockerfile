FROM python:3.12-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements-live.txt
ENV PYTHONUNBUFFERED=1
EXPOSE 8501
CMD ["streamlit","run","streamlit_app.py","--server.address=0.0.0.0","--server.port=8501"]
