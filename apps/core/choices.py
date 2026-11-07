from django.db import models


class DatabaseType(models.TextChoices):
    POSTGRESQL = "postgresql", "PostgreSQL"
    MYSQL = "mysql", "MySQL"
    MSSQL = "mssql", "Microsoft SQL Server"
    MARIADB = "mariadb", "MariaDB"
    ORACLE = "oracle", "Oracle Database"
    SQLITE = "sqlite", "SQLite"

    CLICKHOUSE = "clickhouse", "ClickHouse"
    SNOWFLAKE = "snowflake", "Snowflake"
    BIGQUERY = "bigquery", "Google BigQuery"
    REDSHIFT = "redshift", "Amazon Redshift"
    DUCKDB = "duckdb", "DuckDB"
    DRUID = "druid", "Apache Druid"

    MONGODB = "mongodb", "MongoDB"
    REDIS = "redis", "Redis"
    CASSANDRA = "cassandra", "Apache Cassandra"
    DYNAMODB = "dynamodb", "Amazon DynamoDB"
    COUCHDB = "couchdb", "Apache CouchDB"
    COUCHBASE = "couchbase", "Couchbase"
    NEO4J = "neo4j", "Neo4j"


class DatabaseCategory(models.TextChoices):
    SQL = "sql", "SQL"
    ANALYTIC = "analytic", "Analytic"
    NOSQL = "nosql", "NoSQL"
