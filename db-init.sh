#!/bin/bash

echo "Waiting for SQL Server to start..."

sleep 30

/opt/mssql-tools18/bin/sqlcmd \
-S localhost \
-U sa \
-P $DB_PASSWORD \
-C \
-i /app/init.sql

echo "Database initialized."