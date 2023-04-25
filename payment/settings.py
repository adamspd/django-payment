from django.conf import settings

PAYMENT_ENVIRONMENT = getattr(settings, 'PAYMENT_ENVIRONMENT')
PAYMENT_CLIENT_ID = getattr(settings, 'PAYMENT_CLIENT_ID')
PAYMENT_CLIENT_SECRET = getattr(settings, 'PAYMENT_CLIENT_SECRET')
PAYMENT_BASE_TEMPLATE = getattr(settings, 'PAYMENT_BASE_TEMPLATE', 'base_templates/base.html')
PAYMENT_WEBSITE_NAME = getattr(settings, 'PAYMENT_WEBSITE_NAME', 'Website')
PAYMENT_MODEL = getattr(settings, 'PAYMENT_MODEL')
PAYMENT_REDIRECT_SUCCESS_URL = getattr(settings, 'PAYMENT_REDIRECT_SUCCESS_URL')