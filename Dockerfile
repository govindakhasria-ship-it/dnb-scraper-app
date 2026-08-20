# Use Microsoft's official Playwright Python image
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Set the working directory inside the cloud container
WORKDIR /app

# Copy and install python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application source code into the container
COPY . .

# Expose the port
EXPOSE 8501

# Use shell form (no square brackets) so Render's dynamic $PORT environment variable is evaluated correctly
CMD streamlit run app.py --server.port=${PORT:-8501} --server.address=0.0.0.0 --server.enableCORS=false --server.enableXsrfProtection=false
