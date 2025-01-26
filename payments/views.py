from django.shortcuts import render, redirect
from django.http import JsonResponse
import razorpay
from django.conf import settings
from .models import Payment
from django.contrib.auth.decorators import login_required

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@login_required
def initiate_payment(request):
    """
    Initiates the Razorpay payment by creating an order on Razorpay's platform.
    """
    if request.method == "POST":
        amount = int(request.POST.get("amount")) * 100  # Amount in paise (1 INR = 100 paise)
        currency = "INR"

        # Create the payment order on Razorpay
        order = razorpay_client.order.create(dict(amount=amount, currency=currency, payment_capture='1'))

        # Store the payment details in the database
        payment = Payment(user=request.user, amount=amount / 100, order_id=order['id'])
        payment.save()

        # Return the order details for frontend to handle
        return JsonResponse({
            'order_id': order['id'],
            'key_id': settings.RAZORPAY_KEY_ID,
            'amount': amount,
            'currency': currency,
        })
    return render(request, 'payment/initiate_payment.html')


@login_required
def handle_payment_success(request):
    """
    Handles payment success response from Razorpay.
    Verifies payment, captures payment details and marks it successful.
    """
    if request.method == "POST":
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_signature = request.POST.get('razorpay_signature')

        # Verify the payment signature using Razorpay's library
        try:
            razorpay_client.utility.verify_payment_signature(dict(
                razorpay_payment_id=razorpay_payment_id,
                razorpay_order_id=razorpay_order_id,
                razorpay_signature=razorpay_signature
            ))

            # Payment verification successful
            payment = Payment.objects.get(order_id=razorpay_order_id)
            payment.payment_id = razorpay_payment_id
            payment.signature = razorpay_signature
            payment.status = 'success'
            payment.save()

            return JsonResponse({'status': 'success', 'message': 'Payment Successful'})

        except Exception as e:
            # If verification fails, mark the payment as failed
            payment = Payment.objects.get(order_id=razorpay_order_id)
            payment.status = 'failed'
            payment.save()

            return JsonResponse({'status': 'failed', 'message': 'Payment Failed', 'error': str(e)})

    return redirect('payment:failure')


@login_required
def handle_payment_failure(request):
    """
    Handles the payment failure response.
    """
    return render(request, 'payment/payment_failure.html')
