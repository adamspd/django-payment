import datetime

import requests
import json

from django.apps import apps
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from payment.email_sender import send_email
from payment import settings
from payment.models import Payment
from payment.settings import PAYMENT_MODEL, PAYMENT_BASE_TEMPLATE, PAYMENT_WEBSITE_NAME, PAYMENT_REDIRECT_SUCCESS_URL
from payment.utils import get_paypal_access_token, generate_client_token

PAYMENT_OBJECT = apps.get_model(PAYMENT_MODEL)


# Create your views here.


@csrf_exempt
def create_order(request, object_id):
    if request.method == 'POST':
        payment_info = get_object_or_404(PAYMENT_OBJECT, pk=object_id)
        reference_id = f"{payment_info.get_id_request()}"

        environment = settings.PAYMENT_ENVIRONMENT
        ENDPOINT_URL = "https://api-m.sandbox.paypal.com" if environment == "sandbox" else "https://api-m.paypal.com"
        # Prepare the payload
        print(f"payment_info.get_currency(): {payment_info.get_currency()}")
        print(f"payment_info.get_amount_to_pay(): {payment_info.get_amount_to_pay()}")
        print(f"reference_id: {reference_id}")

        payload = {
            "purchase_units": [
                {
                    "amount": {
                        "currency_code": payment_info.get_currency() if payment_info.get_currency() else "USD",
                        "value": str(payment_info.get_amount_to_pay()),
                    },
                    "reference_id": reference_id,
                }
            ],
            "intent": "CAPTURE",
        }

        access_token = get_paypal_access_token(settings.PAYMENT_CLIENT_ID, settings.PAYMENT_CLIENT_SECRET, ENDPOINT_URL)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }

        # Send the create order request to PayPal
        print(f"json dump before create order: {json.dumps(payload)}")
        response = requests.post(f"{ENDPOINT_URL}/v2/checkout/orders", data=json.dumps(payload), headers=headers)

        if response.status_code == 201:
            order_data = response.json()

            payment_ = Payment(
                order_id=order_data["id"],
                reference_id=reference_id,
                amount=payment_info.get_amount_to_pay(),
                currency=payment_info.get_currency(),
                status=order_data["status"]
            )
            payment_.linked_object = payment_info
            payment_.save()
            return JsonResponse({"id": payment_.order_id})
        else:
            return JsonResponse({"error": "Failed to create order"}, status=400)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)


@csrf_exempt
def capture_order(request, order_id):  # Change this line
    if request.method == 'POST':
        payment_ = get_object_or_404(Payment, order_id=order_id)  # Change this line
        order_data = {
            "order_id": payment_.get_order_id(),
            "status": "COMPLETED",
        }
        payment_.status = "COMPLETED"
        payment_.save()
        return JsonResponse(order_data)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)


def payment(request, object_id, id_request):
    print(f"object_id {object_id} id_request {id_request}")
    payment_info = get_object_or_404(PAYMENT_OBJECT, pk=object_id)
    environment = settings.PAYMENT_ENVIRONMENT
    endpoint_url = "https://api-m.sandbox.paypal.com" if environment == "sandbox" else "https://api-m.paypal.com"

    access_token = get_paypal_access_token(settings.PAYMENT_CLIENT_ID, settings.PAYMENT_CLIENT_SECRET, endpoint_url)
    client_token = generate_client_token(access_token, endpoint_url)
    context = {
        "PAYMENT_BASE_TEMPLATE": PAYMENT_BASE_TEMPLATE,
        "PAYMENT_WEBSITE_NAME": PAYMENT_WEBSITE_NAME,
        "client_token": client_token,
        "service": payment_info,
        "object_id": object_id,
        "id_request": id_request,
        "client_id": settings.PAYMENT_CLIENT_ID,
    }
    return render(request, 'payment/payment.html', context=context)


def payment_success(request, object_id, order_id):
    payment_info = get_object_or_404(PAYMENT_OBJECT, pk=object_id)
    payment_info.set_paid_status(status=True)
    context = {
        "PAYMENT_BASE_TEMPLATE": PAYMENT_BASE_TEMPLATE,
        "PAYMENT_WEBSITE_NAME": PAYMENT_WEBSITE_NAME,
        "PAYMENT_REDIRECT_SUCCESS_URL": PAYMENT_REDIRECT_SUCCESS_URL,
        "appointment": payment_info,
        "order_id": order_id,
    }
    message = f"Thank you for your payment, it's been received and your booking is now confirmed. We're excited to " \
              f"have you on board! Your order # is {order_id}."
    email_context = {
        'first_name': payment_info.get_user().first_name,
        'message': message,
        'current_year': datetime.datetime.now().year,
        'company': PAYMENT_WEBSITE_NAME,
        "order_id": order_id
    }
    # Email the user
    send_email(
        recipient_list=[payment_info.get_user().email], subject="Payment successful",
        template_url='email_sender/thank_you_email.html', context=email_context
    )
    return render(request, 'payment/success.html', context=context)
