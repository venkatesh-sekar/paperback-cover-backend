FROM docker.io/postgres:16

# Copy the custom entry point script into the image
ADD ./compose/postgres/custom-entrypoint.sh /usr/local/bin/

# Make the custom entry point script executable
RUN chmod +x /usr/local/bin/custom-entrypoint.sh

# Set the custom script as the new entry point
ENTRYPOINT ["custom-entrypoint.sh"]