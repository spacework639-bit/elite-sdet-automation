IF DB_ID('TravelXDB') IS NULL
BEGIN
    CREATE DATABASE TravelXDB;
END
GO

USE TravelXDB;
GO

-- Create login if not exists
IF NOT EXISTS (SELECT * FROM sys.server_principals WHERE name = 'sai')
BEGIN
    CREATE LOGIN sai WITH PASSWORD = 'StrongPass@123';
END
GO

-- Create user if not exists
IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = 'sai')
BEGIN
    CREATE USER sai FOR LOGIN sai;
    ALTER ROLE db_owner ADD MEMBER sai;
END
GO