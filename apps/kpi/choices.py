from django.db import models


class Aggregation(models.TextChoices):
    SUM = "sum", "Sum"
    AVG = "avg", "Average"
    MIN = "min", "Minimum"
    MAX = "max", "Maximum"
    COUNT = "count", "Count"
    UNIQ_EXACT = "uniqExact", "Distinct count"


class JoinType(models.TextChoices):
    INNER = "INNER", "Inner join"
    LEFT = "LEFT", "Left join"


class ChartType(models.TextChoices):
    BAR = 'bar', 'Bar'
    LINE = 'line', 'Line'
    PIE = 'pie', 'Pie'
    TABLE = 'table', 'Table'
    NUMBER = 'number', 'Number'


class FilterOperator(models.TextChoices):
    EQ = 'eq', 'Equal'
    NE = 'ne', 'Not equal'
    GT = 'gt', 'Greater than'
    GTE = 'gte', 'Greater than or equal'
    LT = 'lt', 'Less than'
    LTE = 'lte', 'Less than or equal'
    IN = 'in', 'In'
    NOT_IN = 'not_in', 'Not in'
    LIKE = 'like', 'Like'
    IS_NULL = 'is_null', 'Is null'
    IS_NOT_NULL = 'is_not_null', 'Is not null'
