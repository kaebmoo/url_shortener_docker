#!/bin/bash
set -e
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE shortener;
    CREATE DATABASE apikey;
    CREATE DATABASE blacklist;
    CREATE DATABASE "user";
EOSQL