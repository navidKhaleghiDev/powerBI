"""Shared validation helpers for client-defined CDC mappings."""

RESERVED_COLUMNS = {'__deleted', '__op', '__lsn', 'version', 'is_deleted'}
SIMPLE_COLUMN_TYPES = {
    'String', 'Bool', 'UUID', 'Date', 'Date32', 'DateTime', 'Float32', 'Float64',
    *(f'{prefix}Int{bits}' for prefix in ('', 'U') for bits in (8, 16, 32, 64, 128, 256)),
}


def quote_identifier(value: str) -> str:
    """Quote a ClickHouse identifier without restricting its spelling."""
    return '`' + value.replace('\\', '\\\\').replace('`', '\\`') + '`'


# def validate_column_type(value: str) -> str:
#     """Validate supported SQL type expressions without regular expressions."""
#     inner = value
#     if inner.startswith('Nullable(') and inner.endswith(')'):
#         inner = inner[9:-1]
#     if inner in SIMPLE_COLUMN_TYPES:
#         return value
#     if inner.startswith('DateTime64(') and inner.endswith(')'):
#         precision = inner[11:-1]
#         if len(precision) == 1 and precision in '0123456789':
#             return value
#     if inner.startswith('Decimal(') and inner.endswith(')'):
#         parts = [part.strip() for part in inner[8:-1].split(',')]
#         if len(parts) == 2 and all(part.isascii() and part.isdecimal() for part in parts):
#             precision, scale = map(int, parts)
#             if 1 <= precision <= 76 and 0 <= scale <= precision:
#                 return value
#     raise ValueError('Unsupported ClickHouse column type.')


# def parse_table_include_list(value: str) -> list[str]:
#     """Parse a bounded list of schema-qualified table names without regex."""
#     sources = [source.strip() for source in value.split(',')]
#     if not 1 <= len(sources) <= 100 or any(
#         '.' not in source or not all(part.strip() for part in source.split('.', 1))
#         for source in sources
#     ):
#         raise ValueError('Supply up to 100 comma-separated schema.table names.')
#     if len(sources) != len(set(sources)):
#         raise ValueError('Source tables must be unique.')
#     return sources
