from rest_framework.routers import DefaultRouter

from apps.api.viewset.database_viewset import DatabaseViewSet
from apps.api.viewset.database_type_viewset import AnalyticDatabaseViewSet, NoSqlDatabaseViewSet, SqlDatabaseViewSet

router = DefaultRouter()
router.register(r"database", DatabaseViewSet, basename="database")

router.register(r"sql-databases", SqlDatabaseViewSet, basename="sql-database")
router.register(r"analytic-databases", AnalyticDatabaseViewSet, basename="analytic-database")

router.register(r"nosql-databases", NoSqlDatabaseViewSet, basename="nosql-database")

urlpatterns = router.urls
