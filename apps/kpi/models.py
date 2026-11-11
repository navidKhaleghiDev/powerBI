from django.db import models
from apps.kpi.choices import Aggregation, JoinType


class DataSet(models.Model):
    title = models.CharField(max_length=100)
    table_name = models.CharField(max_length=255)
    dimension = models.CharField(max_length=100)
    join_table_name = models.CharField(max_length=255,
        blank=True,
        null=True
    )
    measure = models.CharField(max_length=100, blank=True,)
    join_type = models.CharField(max_length=10, 
                                 choices=JoinType.choices,
                                 null=True, 
                                 blank=True)
    join_left_column = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    join_right_column = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    aggregation = models.CharField(max_length=20, choices=Aggregation.choices)

    class Meta:
        db_table = "data_set"
        verbose_name = "Data set"
        verbose_name_plural = "Data sets"

    def __str__(self):
        return self.title