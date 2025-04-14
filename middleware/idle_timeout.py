import datetime
from django.conf import settings
from django.contrib.auth import logout


class IdleSessionTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            current_datetime = datetime.datetime.now()
            last_activity = request.session.get('last_activity')

            if last_activity:
                elapsed = (
                    current_datetime - datetime.datetime.fromisoformat(last_activity)).seconds
                if elapsed > getattr(settings, 'IDLE_TIMEOUT', 900):  # 15 minutes default
                    logout(request)
                    request.session.flush()  # clear session data

            request.session['last_activity'] = current_datetime.isoformat()

        return self.get_response(request)
