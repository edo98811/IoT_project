# Get the python image
FROM python:3.7.13-slim

# Switch to app directory
WORKDIR /device_connector

# Copy the requirements in to the app
COPY requirements.txt ./

# Install dependencies
RUN pip install -r requirements.txt

# Copy everything else
COPY . .

#Run the python script
ENTRYPOINT [ "python", "device_connector.py" ]

EXPOSE 80