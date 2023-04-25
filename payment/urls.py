from django.urls import path

from payment.views import create_order, capture_order, payment_success, payment

app_name = 'payment'

urlpatterns = [
    path('api/orders/<int:object_id>', create_order, name='create_order'),
    path('api/orders/<str:order_id>/capture/', capture_order, name='capture_order'),

    # path('', payment, name='payment'),  # not a good idea
    path('<int:object_id>/<str:id_request>/', payment, name='payment_linked'),

    # path('success/<str:order_id>/', payment_success, name='success'),  # not a good idea
    path('success/<int:object_id>/<str:order_id>/', payment_success, name='success_linked'),
]
