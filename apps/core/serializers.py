from django.core.checks import database
from rest_framework import serializers

from apps.core.choices import DatabaseType
from apps.core.models import DatabaseCatalog
from apps.core.service.connect_service import ConnectService
from utils.helper_funcs import get_connector_class, get_plugin_name


class DatabaseColumnSerializer(serializers.Serializer):
    database_name = serializers.CharField(allow_blank=True, required=False, allow_null=True)
    schema_name = serializers.CharField(allow_blank=True, required=False, allow_null=True)
    table_name = serializers.CharField(allow_blank=True, required=False, allow_null=True)
    column_name = serializers.CharField(allow_blank=True, required=False, allow_null=True)
    data_type = serializers.CharField(allow_blank=True, required=False, allow_null=True)
    max_length = serializers.IntegerField(required=False, allow_null=True)
    numeric_precision = serializers.IntegerField(required=False, allow_null=True)
    numeric_scale = serializers.IntegerField(required=False, allow_null=True)


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


class DatabaseCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatabaseCatalog
        fields = ("id", "db_type", "category", "image")
        read_only_fields = fields



class ConnectorFieldMixin:
    """Treat dotted connector property names as literal dictionary keys."""

    def bind(self, field_name, parent):
        super().bind(field_name, parent)
        self.source_attrs = [field_name]


class ConnectorCharField(ConnectorFieldMixin, serializers.CharField):
    pass


class ConnectorIntegerField(ConnectorFieldMixin, serializers.IntegerField):
    pass


class ConnectConfigSerializer(serializers.Serializer):
    def get_fields(self):
        fields = super().get_fields()
        fields.update({
            "database.hostname": ConnectorCharField(max_length=255),
            "database.port": ConnectorIntegerField(min_value=1, max_value=65535, default=5432),
            "database.user": ConnectorCharField(max_length=100),
            "database.password": ConnectorCharField(write_only=True, trim_whitespace=False, allow_blank=True),
            "database.dbname": ConnectorCharField(max_length=100),
            "topic.prefix": ConnectorCharField(max_length=100),
            "slot.name": ConnectorCharField(max_length=63),
            "publication.name": ConnectorCharField(max_length=63),
            "table.include.list": ConnectorCharField(),
        })
        return fields


class CreateConnectorSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    db_type = serializers.ChoiceField(choices=DatabaseType.choices)
    config = ConnectConfigSerializer()

    def validate_db_type(self, value):
        if get_connector_class(value) is None or get_plugin_name(value) is None:
            raise serializers.ValidationError("Connector creation is not implemented for this database type.")
        return value

    @property
    def validated_data(self):
        """Build Kafka Connect properties without mutating DRF's validated data."""
        data = super().validated_data.copy()
        if not data:
            return data
        config = data["config"]
        config.update({
            "connector.class": get_connector_class(data["db_type"]),
            "plugin.name": get_plugin_name(data["db_type"]),
            "tasks.max": "1",
            "decimal.handling.mode": "string",
            "transforms": "unwrap",
            "transforms.unwrap.type": "io.debezium.transforms.ExtractNewRecordState",
            "transforms.unwrap.delete.handling.mode": "rewrite",
            "transforms.unwrap.drop.tombstones": "true",
            "transforms.unwrap.add.fields": "op,lsn",
            "transforms.unwrap.add.fields.prefix": "__",
            "value.converter": "org.apache.kafka.connect.json.JsonConverter",
            "value.converter.schemas.enable": "false",
            "key.converter": "org.apache.kafka.connect.json.JsonConverter",
            "key.converter.schemas.enable": "false",
            "snapshot.mode": "always",
        })
        return data
