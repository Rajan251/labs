from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from .services import PaymentService
from .models import Wallet

@csrf_exempt
@require_http_methods(["POST"])
def transfer_pessimistic(request):
    data = json.loads(request.body)
    try:
        PaymentService.transfer_funds_pessimistic(
            data['from_user'], data['to_user'], data['amount']
        )
        return JsonResponse({"status": "success"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def transfer_optimistic(request):
    data = json.loads(request.body)
    try:
        # Simple retry logic could go here
        success = PaymentService.transfer_funds_optimistic(
            data['from_user'], data['to_user'], data['amount']
        )
        if success:
            return JsonResponse({"status": "success"})
        else:
            return JsonResponse({"status": "retry", "message": "Concurrent update"}, status=409)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)
        
@csrf_exempt
@require_http_methods(["POST"])
def create_wallet(request):
    data = json.loads(request.body)
    Wallet.objects.create(user_id=data['user_id'], balance=data['balance'])
    return JsonResponse({"status": "created"})
