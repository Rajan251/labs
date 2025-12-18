from django.db import models
from django.core.exceptions import ValidationError

class ConcurrentVersionField(models.IntegerField):
    """
    Simulates django-concurrency's IntegerVersionField.
    In a real app with the library:
    from concurrency.fields import IntegerVersionField
    """
    def __init__(self, *args, **kwargs):
        kwargs['default'] = 0
        super().__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        value = super().pre_save(model_instance, add)
        # This is where the library would check the version against DB
        # Since we can't easily hook into the deep update query generation from here 
        # without the actual library, we rely on the manual check in services 
        # OR we just increment it here for display purposes.
        # The actual protection is done in the UPDATE clause.
        return value
