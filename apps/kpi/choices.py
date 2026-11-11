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
