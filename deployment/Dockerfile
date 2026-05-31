FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y gcc

# Install Python deps
COPY requirements.txt requirements_ml.txt ./
RUN pip install -r requirements.txt
RUN pip install -r requirements_ml.txt

# Copy code
COPY . .

# Download NLTK data
RUN python -c "import nltk; nltk.download('stopwords'); nltk.download('wordnet')"

# Expose port
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]