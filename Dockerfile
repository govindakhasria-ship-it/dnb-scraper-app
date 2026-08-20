# Use Microsoft's official Playwright Python image matching version 1.62.0
FROM mcr.microsoft.com/playwright/python:v1.62.0-jammy

# Set the working directory inside the cloud container
WORKDIR /app

# Copy and install python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application source code into the container
COPY . .

# Expose the port
EXPOSE 8501

# Run the Streamlit web app with dynamic port mapping
CMD streamlit run app.py --server.port=${PORT:-8501} --server.address=0.0.0.0 --server.enableCORS=false --server.enableXsrfProtection=false
