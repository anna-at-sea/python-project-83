#!/usr/bin/env bash

if [ -f .env ]; then
    source .env
else
    echo ".env file not found. For proper application functionality, please refer to the installation instructions in the repository: https://github.com/anna-at-sea/python-project-83."
fi

make install && psql -a -d $DATABASE_URL -f database.sql
