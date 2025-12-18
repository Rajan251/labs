from django.db import models
from django.db import transaction
from django.core.exceptions import ValidationError
from .fields import ConcurrentVersionField

class Wallet(models.Model):
    user_id = models.IntegerField(unique=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    version = ConcurrentVersionField() # Replaces standard IntegerField

    def __str__(self):
        return f"Wallet {self.user_id}: {self.balance}"

    def clean(self):
        if self.balance < 0:
            raise ValidationError("Balance cannot be negative")
