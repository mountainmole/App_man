# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.8-slim

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8050 available to the world outside this container
EXPOSE 8050

# Define environment variable
ENV NAME app_map_3

# Run app_map_3.py when the container launches
CMD ["python", "app_map_3.py"]
