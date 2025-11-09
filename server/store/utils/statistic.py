def get_light_client_info(request):
    return {
        'ip': request.META.get('HTTP_CF_CONNECTING_IP') or
              request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0] or
              request.META.get('REMOTE_ADDR'),
        'user': request.user if request.user.is_authenticated else None,
        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        'language': request.META.get('HTTP_ACCEPT_LANGUAGE', ''),
        'referer': request.META.get('HTTP_REFERER', ''),
        'cookies': request.META.get('HTTP_COOKIE', ''),
    }
