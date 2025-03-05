# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
import razorpay
import json
from .models import Address, Cart, CartItem, Order, Payment, OrderItem
from math import ceil
from .models import Product, Order
from ecommerceapp.models import Contact
from django.utils.timezone import now
from decimal import Decimal
from razorpay.errors import SignatureVerificationError
import logging
# Initialize Razorpay Client
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

# Home page (Displays products in different categories)
def index(request):
    allProds = []
    catprods = Product.objects.values('category').distinct()
    cats = [item['category'] for item in catprods]

    for cat in cats:
        prod = Product.objects.filter(category=cat)
        allProds.append({'category': cat, 'products': prod})  # Fix structure

    params = {'allProds': allProds}
    return render(request, "index.html", params)

# Cart view (Displays items in the cart)
@login_required
def cart_view(request):
    """Fetch cart details and pass total amount to frontend"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.all()
    total_amount = cart.total_amount  # This uses the property method
    
    return render(request, 'cart.html', {'cart_items': cart_items, 'total_amount': total_amount})

# Contact page (Handles contact form submissions)
def contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")
        phone = request.POST.get("phone")

        # Create and save the Contact instance
        myquery = Contact(name=name, email=email, phone=phone, message=message)
        myquery.save()

        messages.success(request, "We will get back to you soon...")
        return redirect('contact')

    return render(request, "contact.html")

# Other static views

def about(request):
    return render(request, "about.html")

def profiles(request):
    return render(request, "profiles.html")

def cart(request):
    return render(request, "cart.html")


# Product Detail View
def product_detail(request, id):  # ✅ Corrected parameter name
    product = get_object_or_404(Product, id=id)
    return render(request, "product_detail.html", {"product": product})

def save_cart_session(request):
    if request.method == "POST":
        cart = request.POST.get('cart', '[]')  # Get cart data from the POST request
        total_amount = request.POST.get('total_amount', 0)

        # Save the cart and total amount in the session
        request.session['cart'] = cart
        request.session['total_amount'] = total_amount

        return JsonResponse({'success': True, 'message': 'Cart session saved successfully.'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})

# ✅ Add Product to Cart
@login_required
def add_to_cart(request, product_id):
    try:
        product = get_object_or_404(Product, id=product_id)
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

        if not created:
            cart_item.quantity += 1

        cart_item.total_price = cart_item.quantity * cart_item.product.price
        cart_item.save()

        return JsonResponse({"message": "Item added to cart", "total_price": cart_item.total_price})
    
    except Exception as e:
        print(f"Error adding to cart: {e}")
        return JsonResponse({"error": "Something went wrong while adding to cart"}, status=500)

# ✅ Get Cart Items
@login_required
def get_cart_items(request):
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = [
            {
                'cart_item_id': item.id,  # Send cart item ID instead of product ID
                'product_id': item.product.id,
                'product_name': item.product.product_name,
                'quantity': item.quantity,
                'price': float(item.price),  # Convert Decimal to float
                'image_url': item.product.image.url  # Get product image URL
            }
            for item in cart.items.all()
        ]

        return JsonResponse({
            "total_amount": float(cart.total_amount),  # Ensure JSON serialization
            "cart_items": cart_items
        })

    except Cart.DoesNotExist:
        return JsonResponse({
            "total_amount": 0,
            "cart_items": []
        })

# ✅ Update Quantity
@login_required
@csrf_exempt
def update_quantity(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            product_id = data.get("product_id")
            quantity = data.get("quantity", 1)

            cart, created = Cart.objects.get_or_create(user=request.user)
            product = get_object_or_404(Product, id=product_id)
            cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

            cart_item.quantity = max(1, quantity)
            cart_item.save()

            return JsonResponse({"message": "Quantity updated successfully"})
        
        except Exception as e:
            print(f"Error updating quantity: {e}")
            return JsonResponse({"error": "Something went wrong"}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)

# ✅ Remove Item from Cart
@login_required
@csrf_exempt
def remove_from_cart(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            cart_item_id = data.get("cart_item_id")
            user = request.user

            print(f"Attempting to remove CartItem ID: {cart_item_id} for User: {user}")

            # Get the cart item directly by its ID
            cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__user=user)

            print(f"Removing CartItem: {cart_item}")
            cart_item.delete()

            return JsonResponse({"message": "Item removed successfully"})

        except CartItem.DoesNotExist:
            return JsonResponse({"error": f"Cart item with ID {cart_item_id} not found"}, status=400)

        except Exception as e:
            print(f"Unexpected error: {e}")
            return JsonResponse({"error": "Something went wrong"}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=400)

# Clear Cart
@login_required
@csrf_exempt
def clear_cart(request):
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            cart.items.all().delete()  # Clear all items in the cart
            return JsonResponse({"message": "Cart cleared successfully."})
    return JsonResponse({"message": "No cart found."}, status=400)

# Increase Quantity
@login_required
@csrf_exempt
def increase_quantity(request):
    if request.method == "POST":
        data = json.loads(request.body)
        cart_item_id = data.get("cart_item_id")  # Get cart_item_id instead of product_id
        
        cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__user=request.user)
        cart_item.quantity += 1
        cart_item.save()
        
        return JsonResponse({"message": "Quantity increased", "new_quantity": cart_item.quantity})
    
    return JsonResponse({"error": "Invalid request"}, status=400)

# Decrease Quantity
@login_required
@csrf_exempt
def decrease_quantity(request):
    if request.method == "POST":
        data = json.loads(request.body)
        cart_item_id = data.get("cart_item_id")  # Get cart_item_id
        
        cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__user=request.user)

        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
            return JsonResponse({"message": "Quantity decreased", "new_quantity": cart_item.quantity})
        else:
            cart_item.delete()
            return JsonResponse({"message": "Item removed from cart"})
    
    return JsonResponse({"error": "Invalid request"}, status=400)

# Save Cart Session
@login_required
@csrf_exempt
def save_cart_session(request):
    if request.method == "POST":
        data = json.loads(request.body)
        request.session["cart"] = data.get("cart", [])
        request.session["total_amount"] = data.get("totalAmount", 0)
        return JsonResponse({"message": "Cart session saved successfully"})
    return JsonResponse({"error": "Invalid request"}, status=400)

def get_single_product(request):
    product_id = request.GET.get("product_id")
    if product_id:
        try:
            product = Product.objects.get(id=product_id)
            return JsonResponse({
                "status": "success",
                "product": {
                    "id": product.id,
                    "name": product.product_name,
                    "price": product.price,
                    "image_url": product.image.url if product.image else "",
                }
            })
        except Product.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Product not found."})
    return JsonResponse({"status": "error", "message": "Invalid request."})

# @login_required
# def checkout(request):
#     user = request.user
#     cart, created = Cart.objects.get_or_create(user=user)
#     cart_items = cart.items.all()  # Retrieve cart items
    
#     return render(request, 'checkout.html', {'cart_items': cart_items})

# @login_required
# def checkout(request):
#     user = request.user
#     product_id = request.GET.get('product_id')
#     price = request.GET.get('price')
#     quantity = request.GET.get('quantity', 1)  # Default quantity = 1

#     if product_id:  # Direct checkout
#         product = get_object_or_404(Product, id=product_id)
#         total_price = float(price) * int(quantity)

#         context = {
#             'product': product,
#             'price': price,
#             'quantity': quantity,
#             'total_price': total_price,
#             'cart_items': None  # No cart items in direct checkout
#         }
#     else:  # Cart checkout
#         cart, created = Cart.objects.get_or_create(user=user)
#         cart_items = cart.items.all()

#         total_price = sum(item.product.price * item.quantity for item in cart_items)

#         context = {
#             'cart_items': cart_items,
#             'total_price': total_price,
#         }

#     return render(request, 'checkout.html', context)

@login_required
def checkout(request):
    user = request.user
    product_id = request.GET.get('product_id')  # For single product checkout
    quantity = int(request.GET.get('quantity', 1))  # Default 1 if not provided
    razorpay_order = None
    order_created = False  # Flag to track order creation

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    if product_id:  # **Single Product Checkout**
        product = get_object_or_404(Product, id=product_id)
        amount = float(product.price) * quantity

        # Create Razorpay Order
        order_data = {
            "amount": int(amount * 100),  # Convert to paise
            "currency": "INR",
            "payment_capture": 1
        }
        razorpay_order = client.order.create(order_data)

        # Save Order and OrderItem
        order = Order.objects.create(user=user, amount=amount)
        OrderItem.objects.create(order=order, product=product, quantity=quantity, price=product.price)

        order_created = True  # Order successfully created

        context = {
            'single_product': product,
            'quantity': quantity,
            'amount': amount,
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_key': settings.RAZORPAY_KEY_ID,
            'order_created': order_created  # Pass flag to template
        }

    else:  # **Cart Checkout**
        cart, created = Cart.objects.get_or_create(user=user)
        cart_items = cart.items.all()

        if not cart_items.exists():
            return JsonResponse({"error": "Cart is empty"}, status=400)

        amount = sum(item.product.price * item.quantity for item in cart_items)

        # Create Razorpay Order
        order_data = {
            "amount": int(amount * 100),
            "currency": "INR",
            "payment_capture": 1,
        }
        razorpay_order = client.order.create(order_data)

        # Create Order and Save Order Items
        order = Order.objects.create(user=user, amount=amount)
        order_items = [
            OrderItem(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )
            for item in cart_items
        ]
        OrderItem.objects.bulk_create(order_items)

        order_created = True  # Order successfully created

        # # Clear Cart after Checkout
        # cart_items.delete()

        context = {
            'cart_items': cart_items,
            'amount': amount,
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_key': settings.RAZORPAY_KEY_ID,
            'order_created': order_created  # Pass flag to template
        }

    return render(request, 'checkout.html', context)


def get_saved_addresses(request):
    """Fetch saved addresses for the logged-in user."""
    if request.user.is_authenticated:
        addresses = Address.objects.filter(user=request.user)
        address_list = [
            {
                "id": address.id,
                "name": address.name,
                "phone": address.phone,
                "address1": address.address1,
                "address2": address.address2,
                "city": address.city,
                "state": address.state,
                "zip_code": address.zip_code,
            }
            for address in addresses
        ]
        return JsonResponse({"status": "success", "addresses": address_list})
    return JsonResponse({"status": "error", "message": "User not authenticated"})

@csrf_exempt
def save_address(request):
    """Save a new address or update an existing one."""
    if request.method == "POST" and request.user.is_authenticated:
        data = request.POST
        new_address = Address.objects.create(
            user=request.user,
            name=data["name"],
            phone=data["phone"],
            address1=data["address1"],
            address2=data.get("address2", ""),
            city=data["city"],
            state=data["state"],
            zip_code=data["zip_code"],
        )
        new_address.save()
        return get_saved_addresses(request)  # Return updated addresses
    return JsonResponse({"status": "error", "message": "Invalid request"})

@csrf_exempt
@login_required
def save_order(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            order_items = data.get("order_items", [])
            total_amount = data.get("total_amount")

            if not order_items or not total_amount:
                return JsonResponse({"status": "error", "message": "Invalid data"})

            order = Order.objects.create(user=request.user, total_amount=total_amount)

            for item in order_items:
                product = Product.objects.get(id=item["product_id"])
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item["quantity"],
                    price=item["price"]
                )

            return JsonResponse({"status": "success", "order_id": order.id})

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})
        
@login_required
def razorpay_payment(request):
    amount = request.GET.get('amount', '0')  # Ensure a valid string
    product_id = request.GET.get('product_id')  # Get product ID if provided
    quantity = int(request.GET.get('quantity', 1))  # Default to 1 if not provided
    
    print(f"Received in Django: amount={amount}, product_id={product_id}, quantity={quantity}")

    try:
        amount = int(amount) * 100  # Convert to paise
    except ValueError:
        return render(request, 'payment/razorpay_payment.html', {'error': 'Invalid amount'})

    if amount <= 0:
        return render(request, 'payment/razorpay_payment.html', {'error': 'Amount must be greater than zero'})

    try:
        # Initialize Razorpay client
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        # Create Razorpay order
        payment_order = client.order.create({
            'amount': amount,
            'currency': 'INR',
            'payment_capture': 1,  # Auto capture payment
        })
        razorpay_order_id = payment_order['id']
        
        # Define the payment_method
        payment_method = request.GET.get('payment_method', 'razorpay')

        # Save Order in Database
        user = request.user
        order = Order.objects.create(
            user=user,
            razorpay_order_id=razorpay_order_id,
            payment_method=payment_method,
            amount=amount / 100,  # Convert back to INR
            currency='INR',
            status='Pending'
        )

        # ✅ If it's a single product checkout, save OrderItem
        if product_id:
            product = get_object_or_404(Product, id=product_id)
            OrderItem.objects.create(order=order, product=product, quantity=quantity, price=product.price)

        # Save Payment in Database
        payment = Payment.objects.create(
            user=user,
            order=order,
            razorpay_order_id=razorpay_order_id,
            amount=amount / 100,
            status="Pending"
        )

        # Pass data to template
        context = {
            'order': order,
            'payment': payment,
            'razorpay_order_id': razorpay_order_id,
            'payment_method': payment_method,
            'razorpay_key': settings.RAZORPAY_KEY_ID,
            'amount': amount / 100,
            'currency': 'INR',
            'single_product': product_id is not None,  # Flag for template logic
            'product_id': product_id,  # ✅ Pass to template for redirect
            'quantity': quantity,  # ✅ Pass to template for redirect
        }

        return render(request, 'payment/razorpay_payment.html', context)

    except Exception as e:
        print("Error creating Razorpay order:", str(e))
        return render(request, 'payment/razorpay_payment.html', {'error': str(e)})

# @login_required
# def razorpay_payment(request):
#     amount_str = request.GET.get('amount', '0')  # Ensure a valid string
#     try:
#         amount = int(amount_str) * 100  # Convert to paise
#     except ValueError:
#         return render(request, 'payment/razorpay_payment.html', {'error': 'Invalid amount'})

#     if amount <= 0:
#         return render(request, 'payment/razorpay_payment.html', {'error': 'Amount must be greater than zero'})

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
        
#          # Define the payment_method here
#         payment_method = request.GET.get('payment_method', 'razorpay')  # Replace with actual method if necessary

#         # Save Order in Database
#         user = request.user
#         order = Order.objects.create(
#             user=user,
#             razorpay_order_id=razorpay_order_id,
#             payment_method=payment_method,
#             amount=amount / 100,  # Convert back to INR
#             currency='INR',
#             status='Pending'
#         )

#         # Save Payment in Database
#         payment = Payment.objects.create(
#             user=user,
#             order=order,
#             razorpay_order_id=razorpay_order_id,
#             amount=amount / 100,
#             status="Pending"
#         )

#         # Pass data to template
#         context = {
#             'order': order,
#             'payment': payment,
#             'razorpay_order_id': razorpay_order_id,
#             'payment_method': payment_method,
#             'razorpay_key': settings.RAZORPAY_KEY_ID,
#             'amount': amount / 100,
#             'currency': 'INR',
#         }

#         return render(request, 'payment/razorpay_payment.html', context)

#     except Exception as e:
#         print("Error creating Razorpay order:", str(e))
#         return render(request, 'payment/razorpay_payment.html', {'error': str(e)})

from django.db import transaction


@csrf_exempt
def payment_success(request):
    """Handles successful Razorpay payments and completes order processing."""
    if request.method != "GET":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    try:
        razorpay_payment_id = request.GET.get("payment_id")
        razorpay_order_id = request.GET.get("order_id")
        razorpay_signature = request.GET.get("signature")

        if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature]):
            return JsonResponse({"status": "failed", "message": "Missing payment details!"}, status=400)

        # Verify Razorpay payment signature
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        params_dict = {
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature
        }
        client.utility.verify_payment_signature(params_dict)

        with transaction.atomic():
            order = Order.objects.get(razorpay_order_id=razorpay_order_id)
            order.status = "Paid"
            order.payment_method = "Razorpay"
            order.save()

            # ✅ Save payment correctly
            payment = Payment.objects.create(
                user=order.user,
                order=order,
                razorpay_order_id=razorpay_order_id,
                razorpay_payment_id=razorpay_payment_id,
                razorpay_signature=razorpay_signature,
                amount=order.amount,
                status="Paid"
            )

            
            # ✅ Get product_id & quantity from request (for single product)
            product_id = request.GET.get("product_id")
            quantity = int(request.GET.get("quantity", 1))

            print("🔍 DEBUG: Received product_id:", product_id)  # ✅ Debugging Line
            print("🔍 DEBUG: Received quantity:", quantity)  # ✅ Debugging Line


            # ✅ Check if order already has OrderItems
            existing_order_items = OrderItem.objects.filter(order=order)

            if not existing_order_items.exists():
                if product_id:  
                    # ✅ If Single Product Checkout
                    product = get_object_or_404(Product, id=product_id)
                    OrderItem.objects.create(
                        order=order, 
                        product=product, 
                        quantity=quantity, 
                        price=product.price
                    )
                else:
                    # ✅ If Cart Checkout, fetch items from cart
                    cart_items = CartItem.objects.filter(cart__user=order.user)

                    if cart_items.exists():
                        for item in cart_items:
                            OrderItem.objects.create(
                                order=order, 
                                product=item.product, 
                                quantity=item.quantity, 
                                price=item.product.price
                            )

                        # cart_items.delete()  # Clear cart after successful payment

            # ✅ Fetch and display correct order items
            order_items = OrderItem.objects.filter(order=order)

        return render(request, "payment/payment_success.html", {
            "order": order, 
            "payment": payment, 
            "order_items": order_items, 
            "single_product": bool(product_id)  # Flag for template logic
        })

    except Order.DoesNotExist:
        return JsonResponse({"status": "failed", "message": "Order not found!"}, status=400)
    except SignatureVerificationError:
        return JsonResponse({"status": "failed", "message": "Invalid payment signature!"}, status=400)
    except Exception as e:
        return JsonResponse({"status": "failed", "message": str(e)}, status=500)


# @csrf_exempt
# def payment_success(request):
#     """Handles successful Razorpay payments and completes order processing."""
#     if request.method != "GET":
#         return JsonResponse({"error": "Invalid request method"}, status=400)

#     try:
#         razorpay_payment_id = request.GET.get("payment_id")
#         razorpay_order_id = request.GET.get("order_id")
#         razorpay_signature = request.GET.get("signature")

#         if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature]):
#             return JsonResponse({"status": "failed", "message": "Missing payment details!"}, status=400)

#         # Verify Razorpay payment signature
#         client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
#         params_dict = {
#             "razorpay_order_id": razorpay_order_id,
#             "razorpay_payment_id": razorpay_payment_id,
#             "razorpay_signature": razorpay_signature
#         }
#         client.utility.verify_payment_signature(params_dict)

#         with transaction.atomic():
#             order = Order.objects.get(razorpay_order_id=razorpay_order_id)
#             order.status = "Paid"
#             order.payment_method = "Razorpay"
#             order.save()

#             # ✅ Save payment correctly
#             payment = Payment.objects.create(
#                 user=order.user,
#                 order=order,
#                 razorpay_order_id=razorpay_order_id,
#                 razorpay_payment_id=razorpay_payment_id,
#                 razorpay_signature=razorpay_signature,
#                 amount=order.amount,
#                 status="Paid"
#             )

#             # ✅ Check if order already has OrderItems
#             existing_order_items = OrderItem.objects.filter(order=order)

#             if not existing_order_items.exists():  
#                 # ✅ Fetch product details from Razorpay metadata (for single product)
#                 razorpay_order_details = client.order.fetch(razorpay_order_id)
#                 product_id = razorpay_order_details.get('product_id')
#                 quantity = int(razorpay_order_details.get('quantity', 1))

#                 # ✅ If Single Product Checkout
#                 if product_id:
#                     single_product = get_object_or_404(Product, id=product_id)
#                     OrderItem.objects.create(
#                         order=order, 
#                         product=single_product, 
#                         quantity=quantity, 
#                         price=single_product.price
#                     )

#                 else:
#                     # ✅ If Cart Checkout, fetch items from cart
#                     cart_items = CartItem.objects.filter(cart__user=order.user)

#                     if cart_items.exists():
#                         for item in cart_items:
#                             OrderItem.objects.create(
#                                 order=order, 
#                                 product=item.product, 
#                                 quantity=item.quantity, 
#                                 price=item.product.price
#                             )

#                         # cart_items.delete()  # Clear cart after successful payment

#             # ✅ Fetch and display correct order items
#             order_items = OrderItem.objects.filter(order=order)

#         return render(request, "payment/payment_success.html", {
#             "order": order, 
#             "payment": payment, 
#             "order_items": order_items, 
#             "single_product": product_id is not None  # Flag for template logic
#         })

#     except Order.DoesNotExist:
#         return JsonResponse({"status": "failed", "message": "Order not found!"}, status=400)
#     except SignatureVerificationError:
#         return JsonResponse({"status": "failed", "message": "Invalid payment signature!"}, status=400)
#     except Exception as e:
#         return JsonResponse({"status": "failed", "message": str(e)}, status=500) 

# # Orderitem saving
# @csrf_exempt
# def payment_success(request):
#     """Handles successful Razorpay payments and completes order processing."""
#     if request.method != "GET":
#         return JsonResponse({"error": "Invalid request method"}, status=400)

#     try:
#         razorpay_payment_id = request.GET.get("payment_id")
#         razorpay_order_id = request.GET.get("order_id")
#         razorpay_signature = request.GET.get("signature")

#         if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature]):
#             return JsonResponse({"status": "failed", "message": "Missing payment details!"}, status=400)

#         # Verify Razorpay payment signature
#         client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
#         params_dict = {
#             "razorpay_order_id": razorpay_order_id,
#             "razorpay_payment_id": razorpay_payment_id,
#             "razorpay_signature": razorpay_signature
#         }
#         client.utility.verify_payment_signature(params_dict)

#         with transaction.atomic():
#             order = Order.objects.get(razorpay_order_id=razorpay_order_id)
#             order.status = "Paid"
#             order.payment_method = "Razorpay"
#             order.save()

#             # ✅ Save payment correctly
#             payment = Payment.objects.create(
#                 user=order.user,
#                 order=order,
#                 razorpay_order_id=razorpay_order_id,
#                 razorpay_payment_id=razorpay_payment_id,
#                 razorpay_signature=razorpay_signature,
#                 amount=order.amount,
#                 status="Paid"
#             )

#             # **Check if order already has OrderItems**
#             existing_order_items = OrderItem.objects.filter(order=order)

#             if not existing_order_items.exists():  # If no items exist, we need to add them
#                 cart_items = CartItem.objects.filter(cart__user=order.user)

#                 if cart_items.exists():  # **Cart Checkout**
#                     for item in cart_items:
#                         OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity, price=item.product.price * item.quantity)
                    
#                     # cart_items.delete()  # **Clear cart after successful payment**
                
#                 else:  # **Single Product Checkout**
#                     # ✅ Fetch product details from Razorpay metadata
#                     razorpay_order_details = client.order.fetch(razorpay_order_id)
#                     product_id = razorpay_order_details['notes'].get('product_id')
#                     quantity = int(razorpay_order_details['notes'].get('quantity', 1))

#                     if product_id:
#                         single_product = get_object_or_404(Product, id=product_id)
#                         OrderItem.objects.create(order=order, product=single_product, quantity=quantity, price=single_product.price)

#             # ✅ Fetch both single product and cart items for display
#             order_items = OrderItem.objects.filter(order=order)

#         return render(request, "payment/payment_success.html", {"order": order, "payment": payment, "order_items": order_items})

#     except Order.DoesNotExist:
#         return JsonResponse({"status": "failed", "message": "Order not found!"}, status=400)
#     except SignatureVerificationError:
#         return JsonResponse({"status": "failed", "message": "Invalid payment signature!"}, status=400)
#     except Exception as e:
#         return JsonResponse({"status": "failed", "message": str(e)}, status=500)


@login_required
def order_success(request):
    try:
        # Get the latest order for the logged-in user
        latest_order = Order.objects.filter(user=request.user).order_by("-id").first()
        
        if not latest_order:
            return render(request, "order_success.html", {
                "message": "No recent orders found.",
                "ordered_items": [],
                "total_amount": 0
            })

        # Fetch all items related to the order
        ordered_items = OrderItem.objects.filter(order=latest_order)

        # Prepare order items list
        items_list = []
        total_amount = 0
        for item in ordered_items:
            item_data = {
                "product_name": item.product.product_name,
                "quantity": item.quantity,
                "price": item.price,
                "image_url": item.product.image.url if item.product.image else "/static/default-image.jpg"
            }
            items_list.append(item_data)
            total_amount += item.price * item.quantity

        # Render HTML template with order details
        return render(request, "order_success.html", {
            "message": "Order details fetched successfully!",
            "ordered_items": items_list,
            "total_amount": total_amount
        })

    except Exception as e:
        return render(request, "order_success.html", {
            "message": f"Error: {str(e)}",
            "ordered_items": [],
            "total_amount": 0
        })

@login_required
def get_address(request):
    """ Fetch the saved address for the logged-in user """
    try:
        # Retrieve user's address
        address = Address.objects.filter(user=request.user).first()
        if address:
            return JsonResponse({
                "name": f"{address.name}",
                "address1": address.address1,  # Ensure correct field names
                "address2": address.address2 or "N/A",
                "city": address.city,
                "state": address.state,
                "zip_code": address.zip_code
            })
        else:
            return JsonResponse({"error": "No address found"}, status=404)

    except Exception as e:
        return JsonResponse({"error": f"Something went wrong: {str(e)}"}, status=500)

@login_required
def orders(request):
    return render(request, "orders.html")  # Renders the frontend page

@login_required
def get_orders(request):
    """Fetch orders for the logged-in user"""
    orders_data = []

    # ✅ Fetch orders and related items efficiently
    orders = Order.objects.filter(user=request.user).prefetch_related("orderitem_set__product")

    for order in orders:
        order_items = []

        # ✅ Iterate over order items
        for item in order.orderitem_set.all():
            try:
                order_items.append({
                    "product_name": item.product.product_name,
                    "quantity": item.quantity,
                    "price": float(item.price),  # Convert Decimal to float
                    "image_url": item.product.image.url if item.product.image else "/static/default.jpg"
                })
            except Exception as e:
                print(f"Error loading order item {item.id}: {e}")

        # ✅ Prevent `NoneType` error by setting default value
        total_amount = float(order.amount) if order.amount is not None else 0.0

        orders_data.append({
            "order_id": order.id,
            "order_date": order.order_date.strftime("%Y-%m-%d"),
            "status": order.status,
            "amount": total_amount,
            "items": order_items  # ✅ Ensuring "items" key is included
        })

    return JsonResponse({"orders": orders_data})

@login_required
def order_details(request, order_id):
    """Fetch details of a specific order for the logged-in user"""
    # ✅ Fetch order, ensuring it belongs to the logged-in user
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # ✅ Fetch related order items
    order_items = []
    for item in order.orderitem_set.all():
        order_items.append({
            "product_name": item.product.product_name,
            "quantity": item.quantity,
            "price": float(item.price),  # Convert Decimal to float
            "image_url": item.product.image.url if item.product.image else "/static/default.jpg"
        })

    # ✅ Fetch the saved shipping address (assuming one address per order)
    address = order.address  # Assuming there's an `address` ForeignKey in `Order`
    shipping_address = {
        "name": address.name,
        "address1": address.address1,
        "address2": address.address2,
        "city": address.city,
        "state": address.state,
        "zip_code": address.zip_code,
        "country": address.country
    } if address else None

    # ✅ Ensure total amount is handled correctly
    total_amount = float(order.amount) if order.amount is not None else 0.0

    # ✅ Return order details as JSON response
    return JsonResponse({
        "order_id": order.id,
        "order_date": order.order_date.strftime("%Y-%m-%d"),
        "status": order.status,
        "total_amount": total_amount,
        "shipping_address": shipping_address,
        "ordered_items": order_items
    })

@login_required
def order_list(request):
    """Fetch all orders for the logged-in user"""
    orders_data = []

    # ✅ Fetch orders with related order items and products
    orders = Order.objects.filter(user=request.user).prefetch_related("orderitem_set__product")

    for order in orders:
        order_items = []

        # ✅ Iterate over order items and extract details
        for item in order.orderitem_set.all():
            try:
                order_items.append({
                    "product_name": item.product.product_name,
                    "quantity": item.quantity,
                    "price": float(item.price),  # Convert Decimal to float
                    "image_url": item.product.image.url if item.product.image else "/static/default.jpg"
                })
            except Exception as e:
                print(f"Error loading order item {item.id}: {e}")

        # ✅ Ensure `total_amount` is correctly handled
        total_amount = float(order.amount) if order.amount is not None else 0.0

        # ✅ Append order details
        orders_data.append({
            "order_id": order.id,
            "order_date": order.order_date.strftime("%Y-%m-%d"),
            "status": order.status,
            "total_amount": total_amount,
            "items": order_items
        })

    return JsonResponse({"orders": orders_data})


@login_required
def order_details(request, order_id):
    """Fetch and display full details of a specific order"""
    
    # ✅ Get the order, or return a 404 if not found
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # ✅ Fetch all related order items
    ordered_items = order.orderitem_set.select_related("product").all()

    # ✅ Prepare order item details
    items_list = []
    total_amount = 0
    for item in ordered_items:
        items_list.append({
            "product_name": item.product.product_name,
            "quantity": item.quantity,
            "price": float(item.price),  # Convert Decimal to float
            "image_url": item.product.image.url if item.product.image else "/static/default.jpg"
        })
        total_amount += item.price * item.quantity

    # ✅ Pass order details to the template
    return render(request, "order_details.html", {
        "order": order,
        "ordered_items": items_list,
        "total_amount": total_amount
    })

@login_required
def profile(request):
    user = request.user  # Get logged-in user
    orders = Order.objects.filter(user=user)
    payments = Payment.objects.filter(user=user)
    cart_items = CartItem.objects.filter(cart__user=user)

    context = {
        "user": user,
        "orders": orders,
        "payments": payments,
        "cart_items": cart_items,
    }
    return render(request, "profile.html", context)

