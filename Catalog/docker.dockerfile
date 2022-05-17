# Get the python image
FROM python:3.7.13-slim

# Switch to app directory
WORKDIR /Catalog

# Copy the requirements in to the app
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy everything else
COPY . .

#Run the python script
CMD [ "py", "./catalog_manager.py" ]

EXPOSE 80