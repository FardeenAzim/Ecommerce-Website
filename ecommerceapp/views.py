# from django.shortcuts import render

# # Create your views here.
# # views 
# # views.py

# # Imports
# from django.shortcuts import render, redirect
# from django.conf import settings
# from django.views.decorators.csrf import csrf_exempt
# # from django.utils.decorators import method_decorator
# from django.contrib.auth.decorators import login_required
# from django.contrib import messages
# from django.http import JsonResponse, HttpResponse
# import razorpay
# # import json
# import hashlib
# from math import ceil

# # Models and keys
# from .models import Product, Order
# from ecommerceapp.models import Contact

# # Initialize Razorpay Client
# client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

# # Views

# # Home page (Displays products in different categories)
# def index(request):
#     allProds = []
#     catprods = Product.objects.values('category', 'id')
#     cats = {item['category'] for item in catprods}

#     for cat in cats:
#         prod = Product.objects.filter(category=cat)
#         n = len(prod)
#         nSlides = ceil(n / 4)
#         allProds.append([prod, range(1, nSlides + 1), nSlides])

#     params = {'allProds': allProds}
#     return render(request, "index.html", params)

# # Cart view (Displays items in the cart)
# @login_required
# def cart_view(request):
#     cart_items = request.session.get('cart', [])
#     total_price = 0
#     items = []
    
#     for item in cart_items:
#         try:
#             product = Product.objects.get(id=item['product_id'])
#             items.append({
#                 'product': product,
#                 'quantity': item['quantity'],
#                 'total': product.price * item['quantity']
#             })
#             total_price += product.price * item['quantity']
#         except Product.DoesNotExist:
#             continue
    
#     context = {
#         'cart_items': items,
#         'total_price': total_price,
#     }
#     return render(request, 'cart.html', context)

# # Contact page (Handles contact form submissions)
# def contact(request):
#     if request.method == "POST":
#         name = request.POST.get("name")
#         email = request.POST.get("email")
#         desc = request.POST.get("desc")
#         phone = request.POST.get("phone")

#         # Create and save the Contact instance
#         myquery = Contact(name=name, email=email, phone=phone, desc=desc)
#         myquery.save()

#         messages.success(request, "We will get back to you soon...")
#         return redirect('contact')

#     return render(request, "contact.html")

# # Other static views

# def about(request):
#     return render(request, "about.html")

# def profiles(request):
#     return render(request, "profiles.html")

# # Add product to cart
# @login_required
# def add_to_cart(request, product_id):
#     cart = request.session.get('cart', {})
#     try:
#         product = Product.objects.get(id=product_id)
#     except Product.DoesNotExist:
#         return HttpResponse("Product not found", status=404)

#     if product_id in cart:
#         cart[product_id] += 1
#     else:
#         cart[product_id] = 1

#     request.session['cart'] = cart
#     return redirect('checkout')

# # Checkout page (Displays cart items and handles order creation)

# @login_required
# def checkout(request):
#     if request.method == "POST":
#         # Get data from the form
#         items_json = request.POST.get('itemsJson', '')
#         name = request.POST.get('name', '')
#         email = request.POST.get('email', '')
#         phone = request.POST.get('phone', '')
#         amount = request.POST.get('amount')
#         address1 = request.POST.get('address1', '')
#         address2 = request.POST.get('address2', '')
#         city = request.POST.get('city', '')
#         state = request.POST.get('state', '')
#         zip_code = request.POST.get('zip_code', '')
        
#          # Retrieve the actual amount from POST data
#         amount = request.POST.get('amount')
#         if amount is not None:
#             amount = int(amount)  # Convert to integer if necessary
#         else:
#             amount = 0  # Fallback in case of error

#         try:
#             # Create and save order
#             order = Order(
#                 items_json=items_json,
#                 name=name,
#                 email=email,
#                 phone=phone,
#                 amount=amount,
#                 address1=address1,
#                 address2=address2,
#                 city=city,
#                 state=state,
#                 zip_code=zip_code
#             )
#             order.save()
#             print(f"Order amount: {amount}")
#             order_id = order.order_id

#             # Save order update
#             # update = OrderUpdate(order_id=order.order_id, update_desc="The order has been placed")
#             # update.save()

#             # Return success response with order ID
#             return JsonResponse({'success': True, 'order_id': order.order_id})

#         except Exception as e:
#             return JsonResponse({'success': False, 'error': str(e)})

#     return render(request, "checkout.html")
#  # Make sure this matches your actual model

# # @login_required
# # def get_address(request):
# #     """Fetch the saved address of the logged-in user."""
# #     try:
# #         user = request.user  # Get the logged-in user
# #         # address = UserAddress.objects.get(user=user)  # Fetch user's saved address

# #         address_data = {
# #             "recipient_name": address.recipient_name,
# #             "address_line_1": address.address_line_1,
# #             "address_line_2": address.address_line_2 or "",
# #             "city": address.city,
# #             "state": address.state,
# #             "zip_code": address.zip_code,
# #             "country": address.country,
# #         }
# #         return JsonResponse(address_data)

# #     except UserAddress.DoesNotExist:
# #         return JsonResponse({"error": "Address not found"}, status=404)


# @login_required
# def razorpay_payment(request):
#     amount = int(request.GET.get('amount', 0)) * 100  # Convert to paise
    
#     if amount <= 0:
#         return render(request, 'payment/razorpay_payment.html', {'error': 'Invalid amount'})

#     try:
#         # Initialize Razorpay client
#         client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

#         # Create Razorpay order
#         payment_order = client.order.create({
#             'amount': amount,
#             'currency': 'INR',
#             'payment_capture': 1,  # Auto capture payment
#         })
#         razorpay_order_id = payment_order['id']

#         # Save the Order
#         user = request.user
#         order = Order.objects.create(
#             user=user,
#             razorpay_order_id=razorpay_order_id,
#             amount=amount / 100,  # Convert back to INR
#             currency='INR',
#             status='Pending'
#         )

#         # # Save Payment Record in DB
#         # payment = Payment.objects.create(
#         #     user=user,
#         #     order=order,
#         #     razorpay_order_id=razorpay_order_id,
#         #     amount=amount / 100,  # Convert back to INR
#         #     status='Pending'  # Will update after payment success
#         # )

#         # print("Order Created:", order)
#         # print("Payment Created:", payment)

#         # Pass data to template
#         context = {
#             'order': order,
#             'razorpay_order_id': razorpay_order_id,
#             'razorpay_key': settings.RAZORPAY_KEY_ID,
#             'amount': amount / 100,
#             'currency': 'INR'
#         }

#         return render(request, 'payment/razorpay_payment.html', context)

#     except Exception as e:
#         print("Error creating Razorpay order:", str(e))
#         return render(request, 'payment/razorpay_payment.html', {'error': str(e)})

# @csrf_exempt
# def payment_success(request):
#     if request.method == "POST":
#         razorpay_order_id = request.POST.get('razorpay_order_id')
#         razorpay_payment_id = request.POST.get('razorpay_payment_id')
#         razorpay_signature = request.POST.get('razorpay_signature')

#         # Find the order
#         order = Order.objects.get(razorpay_order_id=razorpay_order_id)

#         # Create the signature string
#         generated_signature = f"{razorpay_order_id}|{razorpay_payment_id}"
#         expected_signature = hashlib.sha256(generated_signature.encode('utf-8')).hexdigest()

#         if expected_signature == razorpay_signature:
#             # Payment successful
#             order.payment_id = razorpay_payment_id
#             order.paid = True
#             order.save()

#             # Return success response
#             return JsonResponse({'success': True, 'message': 'Payment Successful'})
#         else:
#             # Payment failed
#             return JsonResponse({'success': False, 'message': 'Payment Verification Failed'})

#     return JsonResponse({'success': False, 'message': 'Invalid Request'})

