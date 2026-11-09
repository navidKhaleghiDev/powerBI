from rest_framework import serializers

from apps.core.choices import DatabaseType

from utils.consumers import (
    RESERVED_COLUMNS,
    # validate_column_type,
)

class ConsumerColumnSerializer(serializers.Serializer):
    source = serializers.CharField(max_length=63)
    target = serializers.CharField(max_length=63)
    type = serializers.CharField(max_length=64)

    def validate(self, attrs):
        if attrs['source'] in RESERVED_COLUMNS or attrs['target'] in RESERVED_COLUMNS:
            raise serializers.ValidationError('Source and target names must not use reserved CDC metadata names.')
        return attrs


class ConsumerTableSerializer(serializers.Serializer):
    source_table = serializers.CharField(max_length=127)
    target_table = serializers.CharField(max_length=63)
    columns = ConsumerColumnSerializer(many=True, allow_empty=False, max_length=500)
    order_by = serializers.ListField(
        child=serializers.CharField(max_length=63), allow_empty=False, max_length=500,
    )

    def validate(self, attrs):
        columns = {column['target']: column['type'] for column in attrs['columns']}
        if len(columns) != len(attrs['columns']):
            raise serializers.ValidationError('Target column names must be unique.')
        sources = [column['source'] for column in attrs['columns']]
        if len(sources) != len(set(sources)):
            raise serializers.ValidationError('Source column names must be unique.')
        keys = attrs['order_by']
        if len(keys) != len(set(keys)) or any(key not in columns for key in keys):
            raise serializers.ValidationError('order_by must contain unique target column names.')
        if any(columns[key].startswith('Nullable(') for key in keys):
            raise serializers.ValidationError('order_by columns must not be nullable.')
        return attrs


class ConsumerSerializer(serializers.Serializer):
    db_type = serializers.ChoiceField(
        choices=DatabaseType.choices, default=DatabaseType.CLICKHOUSE,
        help_text='Consumer destination backend. Only ClickHouse is implemented.',
    )
    tables = ConsumerTableSerializer(many=True, allow_empty=False, max_length=100)

    def get_fields(self):
        fields = super().get_fields()
        fields['topic.prefix'] = serializers.CharField(
            max_length=100,
            help_text='Kafka topic prefix, for example bi. Topics use prefix.schema.table.',
        )
        return fields

    @property
    def validated_data(self):
        data = super().validated_data.copy()
        return {
            'db_type': data['db_type'],
            'tables': data['tables'],
            'topic': data['topic']['prefix'],
        }


class ConsumerResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    database = serializers.CharField()
    tables = serializers.ListField(child=serializers.CharField())
    message = serializers.CharField(required=False)
