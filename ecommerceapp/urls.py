from django.urls import path
from . import views  # Import views from the current app

urlpatterns = [
    # Home and static pages
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('profiles/', views.profiles, name='profiles'),

    # Cart and Checkout
    path('cart/', views.cart_view, name='cart_view'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('checkout/', views.checkout, name='checkout'),

    # Address Management

    # Razorpay Payment
    path('razorpay-payment/', views.razorpay_payment, name='razorpay_payment'),
    path('payment-success/', views.payment_success, name='payment_success'),
]
