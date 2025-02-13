# Use the official base image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the working directory
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# Expose the application port
EXPOSE 5000

# Run the application
CMD ["python", "ai_model_server.py", "-r", "--port", "5000"]