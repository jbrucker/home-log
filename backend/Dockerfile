# Recommendation: specify slim-bullseye or slim-bookworm explicitly for reproducibility.
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code. The actual target dir is /app/app
COPY ./app ./app

# Run the FastAPI application with Uvicorn.
# Remove "--reload" arg for production use.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
