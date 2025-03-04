FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
#EXPOSE 9000 # Add this line
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
