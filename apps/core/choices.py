from django.db import models


class SqlDatabaseType(models.TextChoices):
    POSTGRESQL = "postgresql", "PostgreSQL"
    MYSQL = "mysql", "MySQL"
    MSSQL = "mssql", "Microsoft SQL Server"
    MARIADB = "mariadb", "MariaDB"
    ORACLE = "oracle", "Oracle Database"
    SQLITE = "sqlite", "SQLite"


class AnalyticDatabaseType(models.TextChoices):
    CLICKHOUSE = "clickhouse", "ClickHouse"
    SNOWFLAKE = "snowflake", "Snowflake"
    BIGQUERY = "bigquery", "Google BigQuery"
    REDSHIFT = "redshift", "Amazon Redshift"
    DUCKDB = "duckdb", "DuckDB"
    DRUID = "druid", "Apache Druid"


class NoSqlDatabaseType(models.TextChoices):
    MONGODB = "mongodb", "MongoDB"
    REDIS = "redis", "Redis"
    CASSANDRA = "cassandra", "Apache Cassandra"
    DYNAMODB = "dynamodb", "Amazon DynamoDB"
    COUCHDB = "couchdb", "Apache CouchDB"
    COUCHBASE = "couchbase", "Couchbase"
    NEO4J = "neo4j", "Neo4j"
