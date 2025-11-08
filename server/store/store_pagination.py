from rest_framework.pagination import PageNumberPagination

class StorePagination(PageNumberPagination):
    page_size = 50


# from rest_framework.pagination import PageNumberPagination
# from rest_framework.utils.urls import replace_query_param

# class StorePagination(PageNumberPagination):
#     page_size = 50

#     def get_next_link(self):
#         if not self.page.has_next():
#             return None
#         url = replace_query_param(self.request.build_absolute_uri(), self.page_query_param, self.page.next_page_number())
#         return url.replace('http://', 'https://')

#     def get_previous_link(self):
#         if not self.page.has_previous():
#             return None
#         url = replace_query_param(self.request.build_absolute_uri(), self.page_query_param, self.page.previous_page_number())
#         return url.replace('http://', 'https://')

# from rest_framework.pagination import PageNumberPagination
# from rest_framework.utils.urls import replace_query_param

from rest_framework.pagination import PageNumberPagination
from rest_framework.utils.urls import replace_query_param

class StorePagination(PageNumberPagination):
    page_size = 50  # default for desktop

    def get_page_size(self, request):
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
            return 10  # smaller page size for mobile
        return self.page_size

    def _force_https_if_needed(self, url):
        host = self.request.get_host()
        if 'localhost' in host or '127.0.0.1' in host:
            return url  # Keep http for local development
        return url.replace('http://', 'https://')

    def get_next_link(self):
        if not self.page.has_next():
            return None
        url = replace_query_param(
            self.request.build_absolute_uri(),
            self.page_query_param,
            self.page.next_page_number()
        )
        return self._force_https_if_needed(url)

    def get_previous_link(self):
        if not self.page.has_previous():
            return None
        url = replace_query_param(
            self.request.build_absolute_uri(),
            self.page_query_param,
            self.page.previous_page_number()
        )
        return self._force_https_if_needed(url)
