from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Payment(models.Model):
    order_id = models.CharField(max_length=255, unique=True)
    reference_id = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3)
    status = models.CharField(max_length=20)

    linked_object_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    linked_object_id = models.PositiveIntegerField(null=True, blank=True)
    linked_object = GenericForeignKey('linked_object_type', 'linked_object_id')

    # meta data
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.created_at} - {self.order_id} - {self.reference_id} - {self.amount} - {self.currency} - {self.status}"

    def get_order_id(self):
        return self.order_id

    def get_reference_id(self):
        return self.reference_id

    def get_amount(self):
        return self.amount

    def get_currency(self):
        return self.currency

    def get_status(self):
        return self.status

    def get_linked_object(self):
        return self.linked_object

    def get_created_at(self):
        return self.created_at

    def get_updated_at(self):
        return self.updated_at
