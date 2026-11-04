from rest_framework import serializers

from apps.core.choices import DatabaseType
class DatabaseColumnSerializer(serializers.Serializer):
    database_name = serializers.CharField(allow_blank=True, required=False, allow_null=True)
    schema_name = serializers.CharField(allow_blank=True, required=False, allow_null=True)
    table_name = serializers.CharField(allow_blank=True, required=False, allow_null=True)
    column_name = serializers.CharField(allow_blank=True, required=False, allow_null=True)
    data_type = serializers.CharField(allow_blank=True, required=False, allow_null=True)
    max_length = serializers.IntegerField(required=False, allow_null=True)
    numeric_precision = serializers.IntegerField(required=False, allow_null=True)
    numeric_scale = serializers.IntegerField(required=False, allow_null=True)


class DatabaseMetadataSerializer(serializers.Serializer):
    databases = serializers.ListField(child=serializers.CharField(), required=False)
    database = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    columns = DatabaseColumnSerializer(many=True, required=False)
    error = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class DatabaseListResponseSerializer(serializers.Serializer):
    databases = serializers.ListField(child=serializers.CharField())


class DatabaseErrorSerializer(serializers.Serializer):
    error = serializers.CharField()


class DatabaseConnectionQuerySerializer(serializers.Serializer):
    db_type = serializers.ChoiceField(
        choices=DatabaseType.choices,
        help_text="Database type. Only PostgreSQL connection testing is currently implemented.",
    )
    host = serializers.CharField(max_length=255)
    port = serializers.IntegerField(min_value=1, max_value=65535)
    database = serializers.CharField(max_length=255)
    username = serializers.CharField(max_length=255)
    password = serializers.CharField(write_only=True, trim_whitespace=False, allow_blank=True)


class DatabaseTableSerializer(serializers.Serializer):
    schema_name = serializers.CharField()
    table_name = serializers.CharField()


class DatabaseColumnsQuerySerializer(DatabaseConnectionQuerySerializer):
    table = serializers.CharField(help_text="Schema-qualified table name, for example public.orders.")

    def validate_table(self, value):
        schema, separator, table = value.partition(".")
        if not separator or not schema.strip() or not table.strip():
            raise serializers.ValidationError("Expected schema.table.")
        return value


class TableColumnSerializer(serializers.Serializer):
    name = serializers.CharField()
    type = serializers.CharField()
    nullable = serializers.BooleanField()
    default = serializers.CharField(allow_null=True)
    max_length = serializers.IntegerField(allow_null=True)
    precision = serializers.IntegerField(allow_null=True)
    scale = serializers.IntegerField(allow_null=True)


class DatabaseColumnsResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    database = serializers.CharField(required=False)
    table = serializers.CharField(required=False)
    columns = TableColumnSerializer(many=True)
    message = serializers.CharField(required=False)


class DatabaseConnectionResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()


class DatabaseTableColumnsSerializer(DatabaseTableSerializer):
    columns = DatabaseColumnSerializer(many=True)


class DatabaseTablesResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    database = serializers.CharField()
    tables = DatabaseTableColumnsSerializer(many=True)
    message = serializers.CharField(required=False)
