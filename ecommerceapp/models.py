from django.db import models
# Create your models here.
from django.conf import settings
from django.utils.timezone import now
from decimal import Decimal
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.dispatch import receiver
from django.db.models.signals import post_save



class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and return a regular user.
        """
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        extra_fields.setdefault('is_user', True)  # Set is_user=True by default
        extra_fields.setdefault('is_active', True)  # Mark user as active by default
        extra_fields.setdefault('is_admin', False)  # Ensure is_admin=False
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and return a superuser.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_admin', True)  # Ensure is_admin=True for superusers
        extra_fields.setdefault('is_user', False)  # Ensure is_user=False
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    profile_picture = models.ImageField(upload_to="profile_pics/", default="default.jpg")
    phone = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    username = models.CharField(max_length=150, blank=True, null=True)  # Optional username
    cart = models.OneToOneField('Cart', on_delete=models.SET_NULL, null=True, blank=True, related_name='custom_user')
    pass  # Your CustomUser model (ensure no duplicate profile logic)
    
    is_active = models.BooleanField(default=True)  # Custom field for website users
    is_staff = models.BooleanField(default=False)  # Custom field for website users

    is_user = models.BooleanField(default=False)  # Custom field for website users
    is_admin = models.BooleanField(default=False)  # Custom field for admin users

    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'  # Use email for authentication
    REQUIRED_FIELDS = []  # No additional required fields

    def __str__(self):
        return self.email


class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, Profile

@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class Product(models.Model):
    product_name = models.CharField(max_length=100)
    desc = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    category = models.CharField(max_length=100)
    subcategory = models.CharField(max_length=100)
    image = models.ImageField(upload_to='shop/images', null=True, blank=True)

    def __str__(self):
        return self.product_name
    
class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_cart'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart for {self.user.email}"

    @property
    def total_amount(self):
        """Calculate total amount based on cart items"""
        return sum(item.quantity * item.price for item in self.items.all())  # Ensuring proper calculation

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        """Ensure price is set from product price if not provided"""
        if not self.price or self.price != self.product.price:
            self.price = self.product.price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} x {self.product.product_name} ({self.cart.user.username})"

    
class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField() 
    message = models.TextField(max_length=500)
    phone = models.CharField(max_length=15)

    def __str__(self):
        return self.name

class Address(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, default='Anonymous')
    phone = models.CharField(max_length=15, default='0000000000')
    address1 = models.TextField(default='Default Address Line 1')
    address2 = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, default='Default City')
    state = models.CharField(max_length=100, default='Default State')
    zip_code = models.CharField(max_length=10, default='000000')
    created_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.user.username} - {self.name}, {self.phone}"

class Order(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Shipped", "Shipped"),
        ("Delivered", "Delivered"),
        ("Cancelled", "Cancelled"),
    ]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True)
    payment_method = models.CharField(max_length=50, default="Razorpay")  # ✅ Set a default value
    razorpay_order_id = models.CharField(max_length=255)
    order_date = models.DateTimeField(default=now)  # Use timezone.now as default
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    currency = models.CharField(max_length=10, default="INR")  # Add this line
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} - {self.user}"
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.product_name} (x{self.quantity})"

    
class Payment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Added user field
    order = models.ForeignKey(Order, related_name='payments', on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=50, default="Razorpay")
    razorpay_payment_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_order_id = models.CharField(max_length=255)
    razorpay_signature = models.CharField(max_length=255, null=True, blank=True)  # 🔹 Add this line
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='Pending')
    payment_date = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"Payment {self.razorpay_payment_id} for Order {self.order.id}"


