"""Shared validation helpers for client-defined CDC mappings."""

RESERVED_COLUMNS = {'__deleted', '__op', '__lsn', 'version', 'is_deleted'}
SIMPLE_COLUMN_TYPES = {
    'String', 'Bool', 'UUID', 'Date', 'Date32', 'DateTime', 'Float32', 'Float64',
    *(f'{prefix}Int{bits}' for prefix in ('', 'U') for bits in (8, 16, 32, 64, 128, 256)),
}


def quote_identifier(value: str) -> str:
    """Quote a ClickHouse identifier without restricting its spelling."""
    return '`' + value.replace('\\', '\\\\').replace('`', '\\`') + '`'
