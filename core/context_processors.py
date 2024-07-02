from django.conf import settings

def sentry_dsn(request):
    return {
        "SENTRY_DSN": settings.SENTRY_DSN,
    }
    
def posthog_config(request):
    return {
        "POSTHOG_KEY": settings.POSTHOG_KEY,
        "POSTHOG_HOST": settings.POSTHOG_HOST,
    }