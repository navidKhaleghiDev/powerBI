from rest_framework.pagination import PageNumberPagination


class DatabaseTypePagination(PageNumberPagination):
    page_size = 20
