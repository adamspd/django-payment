import datetime
from decimal import Decimal

import requests
import json
import logging

from django.apps import apps
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from payment.email_sender import send_email, notify_admin
from payment import settings
from payment.models import Payment
from payment.settings import PAYMENT_MODEL, PAYMENT_BASE_TEMPLATE, PAYMENT_WEBSITE_NAME, PAYMENT_REDIRECT_SUCCESS_URL, \
    PAYMENT_APPLY_PAYPAL_FEES, DEFAULT_EMAIL_MESSAGE, DEFAULT_EMAIL_PAYMENT_SUCCESS_TEMPLATE
from payment.utils import get_paypal_access_token, generate_client_token, calculate_total_amount

PAYMENT_OBJECT = apps.get_model(PAYMENT_MODEL)

logging.basicConfig(level=logging.INFO)


@csrf_exempt
def create_order(request, object_id):
    if request.method == 'POST':
        payment_info = get_object_or_404(PAYMENT_OBJECT, pk=object_id)
        reference_id = f"{payment_info.get_id_request()}"

        environment = settings.PAYMENT_PAYPAL_ENVIRONMENT
        ENDPOINT_URL = "https://api-m.sandbox.paypal.com" if environment == "sandbox" else "https://api-m.paypal.com"
        # Prepare the payload
        logging.info(f"payment_info.get_currency(): {payment_info.get_currency()}")
        logging.info(f"payment_info.get_amount_to_pay(): {payment_info.get_amount_to_pay()}")
        logging.info(f"reference_id: {reference_id}")

        value = calculate_total_amount(payment_info.get_amount_to_pay()) if PAYMENT_APPLY_PAYPAL_FEES else \
            str(payment_info.get_amount_to_pay())
        currency = payment_info.get_currency() if payment_info.get_currency() else "USD"
        logging.info(f"total amount after fee calculation: {currency} {value}")

        payload = {
            "purchase_units": [
                {
                    "amount": {
                        "currency_code": currency,
                        "value": value,
                    },
                    "reference_id": reference_id,
                }
            ],
            "intent": "CAPTURE",
        }

        access_token = get_paypal_access_token(settings.PAYMENT_PAYPAL_CLIENT_ID, settings.PAYMENT_PAYPAL_CLIENT_SECRET,
                                               ENDPOINT_URL)
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
                fee=Decimal(value=value) - payment_info.get_amount_to_pay(),
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
    environment = settings.PAYMENT_PAYPAL_ENVIRONMENT
    endpoint_url = "https://api-m.sandbox.paypal.com" if environment == "sandbox" else "https://api-m.paypal.com"

    access_token = get_paypal_access_token(settings.PAYMENT_PAYPAL_CLIENT_ID, settings.PAYMENT_PAYPAL_CLIENT_SECRET,
                                           endpoint_url)
    client_token = generate_client_token(access_token, endpoint_url)
    total_amount = calculate_total_amount(payment_info.get_amount_to_pay()) if PAYMENT_APPLY_PAYPAL_FEES else str(
        payment_info.get_amount_to_pay())
    fee = Decimal(total_amount) - payment_info.get_amount_to_pay()
    fee_amount = "{:.2f}".format(fee)
    context = {
        "PAYMENT_BASE_TEMPLATE": PAYMENT_BASE_TEMPLATE,
        "PAYMENT_WEBSITE_NAME": PAYMENT_WEBSITE_NAME,
        "client_token": client_token,
        "service": payment_info,
        "object_id": object_id,
        "id_request": id_request,
        "client_id": settings.PAYMENT_PAYPAL_CLIENT_ID,
        "total_amount": total_amount,
        "fee_amount": fee_amount,
    }
    return render(request, 'payment/payment.html', context=context)


def payment_success(request, object_id, order_id):
    object_info = get_object_or_404(PAYMENT_OBJECT, pk=object_id)
    object_info.set_paid_status(status=True)
    payment_info = get_object_or_404(Payment, order_id=order_id)
    first_name = object_info.get_user_name()
    company = PAYMENT_WEBSITE_NAME

    common_context = {
        'first_name': first_name,
        'company': company,
        "order_id": order_id,
        "payment_info": payment_info,
    }

    context = {
        **common_context,
        "PAYMENT_BASE_TEMPLATE": PAYMENT_BASE_TEMPLATE,
        "PAYMENT_REDIRECT_SUCCESS_URL": PAYMENT_REDIRECT_SUCCESS_URL,
        "object_info": object_info,
    }
    link = request.build_absolute_uri(payment_info.get_absolute_url())
    message = DEFAULT_EMAIL_MESSAGE or f"Thank you for your payment, it's been received and your booking is now confirmed" \
                                       f"You can view it by clicking <a href='{link}'>here</a> " \
                                       f"We're excited to have you on board! Your order # is {order_id}."


    template_url_email = DEFAULT_EMAIL_PAYMENT_SUCCESS_TEMPLATE or 'email_sender/payment_email.html'

    email_context = {
        **common_context,
        'message': message,
        'current_year': datetime.datetime.now().year,
    }

    # Email the user
    send_email(
        recipient_list=[object_info.get_user_email()], subject="Payment successful",
        template_url=template_url_email, context=email_context
    )
    return render(request, 'payment/success.html', context=context)


def payment_details(request, reference_id, object_id, order_id):
    object_info = get_object_or_404(PAYMENT_OBJECT, pk=object_id)
    first_name = object_info.get_user_name()
    user_email = object_info.get_user_email()
    payment_ = get_object_or_404(Payment, order_id=order_id)
    logging.info(f"payment details: {payment_}")
    linked_object = payment_.linked_object
    context = {
        "PAYMENT_BASE_TEMPLATE": PAYMENT_BASE_TEMPLATE,
        "PAYMENT_WEBSITE_NAME": PAYMENT_WEBSITE_NAME,
        'payment_info': payment_,
        'linked_object': linked_object,
        'reference_id': reference_id,
        "current_date": payment_.get_created_at().strftime("%B %d, %Y"),
        "first_name": first_name,
        "user_email": user_email,
        "status": payment_.get_payment_status_css_status(),
    }
    logging.info(f"notifying admin for payment details: {context}")
    notify_admin(subject="Payment details for order # {}".format(order_id), template_url="email_sender/notify_admin.html",
                 context=context)
    return render(request, 'payment/payment_details.html', context)
