from ..utils.statistic import get_light_client_info
from ..tasks import enrich_and_log_client_info

class ClientLoggerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Optional: skip logging for static/admin
        excluded_paths = ['/admin/', '/static/', '/favicon.ico']
        if any(request.path.startswith(p) for p in excluded_paths):
            return self.get_response(request)

        try:
            client_data = get_light_client_info(request)
            enrich_and_log_client_info.delay(client_data)
        except Exception as e:
            print(f" **************** Client logging failed **************** : {e}")

        return self.get_response(request)  # ✅ Always return this

