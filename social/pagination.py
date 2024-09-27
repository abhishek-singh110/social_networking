from rest_framework.pagination import PageNumberPagination

# This is used for pagination.
class UserPagination(PageNumberPagination):
    page_size = 10  
    page_size_query_param = 'page_size'
    max_page_size = 100