# Django Payment App

This is a Django payment application that allows you to easily integrate with PayPal to accept payments. This app is
designed to be flexible, allowing you to collect payments for any type of service or product.

## Installation

1. Add the following code inside the `<head>` tag of your `base.html` template:

```html

<head>
    <!-- other tags -->
    <title>My title</title>
    {% block scriptHead %}{% endblock %} <!-- this line must be added -->
</head>
```

To use the application, a model must be created with at least the following field :

1. Create a model in your Django application that includes at least the following fields:

```python
from django.db import models
from payment.utils import get_timestamp, generate_random_id


class InfoToPassToPaymentApplication(models.Model):
    id_request = models.CharField(max_length=255, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, null=True, blank=True)

    # Add any other fields you want

    def save(self, *args, **kwargs):
        if self.id_request is None:
            self.id_request = f"{get_timestamp()}{generate_random_id()}"  # You must create this function or use another method to generate a unique id
        return super().save(*args, **kwargs)

    def get_id_request(self):
        return self.id_request

    def get_amount_to_pay(self):
        return self.amount

    def get_currency(self):
        return self.currency
    
    def set_paid_status(self, status: bool):
        self.is_paid = status

```

This model should represent the information that you want to pass to the payment application. This can include details
about the service or product you're selling, as well as any other necessary information.

## Usage

With your model created, you can now integrate the payment app with your existing application. Add the following
settings to your Django project's settings.py file, adjusting the values as needed:

```python
# settings.py

INSTALLED_APPS = [
    # other apps
    'payment',
]
```

```python
# settings.py

PAYMENT_ENVIRONMENT = 'sandbox'  # or 'production'
PAYMENT_CLIENT_ID = 'your_paypal_client_id'
PAYMENT_CLIENT_SECRET = 'your_paypal_client_secret'
PAYMENT_BASE_TEMPLATE = 'base_templates/base.html'  # or your own base template path
PAYMENT_WEBSITE_NAME = 'My Website'  # or your website name
PAYMENT_MODEL = 'your_app_name.InfoToPassToPaymentApplication'  # Replace with your app and model name
PAYMENT_REDIRECT_SUCCESS_URL = 'your_app_name:success_view_name'  # Replace with your app and success view name
```

Follow the instructions in the app's documentation to set up the required views.

Once everything is set up, you can start accepting payments through PayPal.