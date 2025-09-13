#!/bin/bash
# custom-entrypoint.sh

# Set the standard environment variables from custom ones
export POSTGRES_USER=${POSTGRES__USER:-postgres}
export POSTGRES_PASSWORD=${POSTGRES__PASSWORD:-password}
export POSTGRES_DB=${POSTGRES__DATABASE:-postgres}

# Print credentials
echo "POSTGRES_USER: $POSTGRES_USER"
echo "POSTGRES_PASSWORD: $POSTGRES_PASSWORD"
echo "POSTGRES_DB: $POSTGRES_DB"

# Execute the original entrypoint script
exec docker-entrypoint.sh postgres
