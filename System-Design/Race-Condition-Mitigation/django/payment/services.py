from django.db import transaction
from django.db.models import F
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
import time
from .models import Wallet

class PaymentService:
    
    @staticmethod
    def transfer_funds_pessimistic(from_user_id, to_user_id, amount):
        """
        Uses select_for_update(nowait=True) to lock rows.
        Fails immediately if lock cannot be acquired.
        """
        from django.db.utils import OperationalError
        
        try:
            with transaction.atomic():
                # Lock both rows to prevent deadlock, order by ID
                first_id, second_id = sorted([from_user_id, to_user_id])
                
                # Acquire locks with nowait=True
                # Note: fetch one by one or using filter, but simple get() is fine here
                try:
                    Wallet.objects.select_for_update(nowait=True).get(user_id=first_id)
                    Wallet.objects.select_for_update(nowait=True).get(user_id=second_id)
                except OperationalError:
                    raise ValueError("Could not acquire lock immediately")
                except ObjectDoesNotExist:
                    raise ValueError("Wallet not found")

                # Now perform updates using F expressions for atomicity
                sender = Wallet.objects.get(user_id=from_user_id) # re-fetch (cached by cache framework usually but here safe)
                if sender.balance < amount:
                    raise ValueError("Insufficient funds")

                # Atomic DB updates
                Wallet.objects.filter(user_id=from_user_id).update(balance=F('balance') - amount)
                Wallet.objects.filter(user_id=to_user_id).update(balance=F('balance') + amount)
                
                return True
        except OperationalError:
             raise ValueError("Transaction failed due to locking conflict")

    @staticmethod
    def transfer_funds_optimistic(from_user_id, to_user_id, amount):
        """
        Uses a version number to detect concurrent updates.
        Returns False if update fails, caller should retry.
        """
        with transaction.atomic():
            sender = Wallet.objects.get(user_id=from_user_id)
            receiver = Wallet.objects.get(user_id=to_user_id)
            
            if sender.balance < amount:
                raise ValueError("Insufficient funds")
            
            # Try to update sender
            updated_sender = Wallet.objects.filter(
                id=sender.id, 
                version=sender.version
            ).update(
                balance=sender.balance - amount,
                version=sender.version + 1
            )
            
            if updated_sender == 0:
                # Concurrent update happened
                return False
                
            # Try to update receiver
            updated_receiver = Wallet.objects.filter(
                id=receiver.id,
                version=receiver.version
            ).update(
                balance=receiver.balance + amount,
                version=receiver.version + 1
            )
            
            if updated_receiver == 0:
                 # Rollback will happen automatically due to raising exception? 
                 # Actually in simpler optimistic locking we might need to manually rollback or simple fail the transaction
                 # But here we are in atomic block, so raising exception rolls back.
                 raise ValueError("Concurrent update on receiver")

            return True

    @staticmethod
    def transfer_funds_distributed_lock(from_user_id, to_user_id, amount):
        """
        Uses Redis distributed lock to ensure exclusive access.
        """
        lock_id = f"lock:wallet:{min(from_user_id, to_user_id)}_{max(from_user_id, to_user_id)}"
        
        # Acquire lock (blocking up to 5 seconds)
        with cache.lock(lock_id, timeout=10, blocking_timeout=5):
            with transaction.atomic():
                sender = Wallet.objects.get(user_id=from_user_id)
                receiver = Wallet.objects.get(user_id=to_user_id)
                
                if sender.balance < amount:
                    raise ValueError("Insufficient funds")
                
                sender.balance -= amount
                sender.save()
                
                receiver.balance += amount
                receiver.save()
                
                return True
