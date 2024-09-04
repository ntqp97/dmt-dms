from rest_framework.pagination import PageNumberPagination

STANDARD_PAGESIZE = 10
LARGE_PAGESIZE = 100


class LargeResultsSetPagination(PageNumberPagination):
    page_size = int(LARGE_PAGESIZE)
    page_size_query_param = "page_size"
    max_page_size = 1000


class StandardResultsSetPagination(PageNumberPagination):
    page_size = int(STANDARD_PAGESIZE)
    page_size_query_param = "page_size"
    max_page_size = 100


class CustomPaginationLeaderboard(StandardResultsSetPagination):
    def get_paginated_response(self, data, *args, **kwargs):
        sort_by = self.request.query_params.get("sort_by", None)
        if sort_by in ["num_exam_completed", "sum_overall", "average_overall"]:
            sort_data = sorted(data, key=lambda x: x[sort_by], reverse=True)
            return super().get_paginated_response(sort_data)
        return super().get_paginated_response(data)
