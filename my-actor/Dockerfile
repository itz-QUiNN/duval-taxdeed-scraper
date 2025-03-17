FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /src

# Install necessary dependencies
COPY requirements.txt /src/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your files into the container
COPY . /src/

# Set the entrypoint to run your Python script
ENTRYPOINT ["python", "src/main.py"]
