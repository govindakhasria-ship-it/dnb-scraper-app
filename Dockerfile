# Use Microsoft's official Playwright Python image which contains Chromium and Linux system dependencies
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Set the working directory inside the cloud container
WORKDIR /app

# Copy and install python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application source code into the container
COPY . .

# Expose the port Streamlit runs on
EXPOSE 8501

# Run the Streamlit web app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]