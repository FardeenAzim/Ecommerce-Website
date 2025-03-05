from django.shortcuts import render, redirect
from django.contrib.auth import logout, login, authenticate
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.views.decorators.csrf import csrf_exempt

from .utils import generate_token
from ecommerceapp.models import Profile
from .forms import CustomUserCreationForm

User = get_user_model()

def clean_string(s):
    return ''.join(c for c in s if ord(c) < 128)  # Keep only ASCII characters


### **Signup View with Email Verification**
def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Disable login until email verification
            user.is_user = True  # Mark the user as a website user
            user.save()

            # ✅ Ensure a Profile is created for the user
            Profile.objects.get_or_create(user=user)

            # **Send Email Verification**
            current_site = get_current_site(request)
            email_subject = "Activate Your Account"
            email_message = render_to_string('authentication/activate.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': generate_token.make_token(user),
            })

            email_subject = clean_string(email_subject)
            email_message = clean_string(email_message)

            email = EmailMessage(email_subject, email_message, to=[user.email])
            email.send()

            messages.success(request, "Check your email to activate your account.")
            return redirect('login')

        else:
            messages.error(request, "Signup failed. Please correct the errors below.")
            print(form.errors)  # Debugging

    else:
        form = CustomUserCreationForm()

    return render(request, 'authentication/signup.html', {'form': form})


### **Activation View**
def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and generate_token.check_token(user, token):
        user.is_active = True  # Activate the user
        user.save()
        login(request, user)  # Log in the user automatically
        messages.success(request, "Account activated successfully! You are now logged in.")
        return redirect('/')  # Redirect to home

    else:
        messages.warning(request, "Activation link is invalid or expired!")
        return render(request, 'authentication/activation_failed.html')


### **Login View**
@csrf_exempt  # Use only if necessary (not recommended)
def login_view(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        myuser = authenticate(request, username=email, password=password)

        if myuser:
            if myuser.is_active:
                login(request, myuser)
                return redirect('/admin/' if myuser.is_admin else '/')
            else:
                messages.error(request, "Your account is not activated. Check your email.")
                return redirect('login')
        else:
            messages.error(request, "Invalid credentials or account does not exist.")
    
    return render(request, "authentication/login.html")


### **Logout View**
def logout_view(request):
    logout(request)
    messages.info(request, "Logged out successfully!")
    return redirect('login')


### **Admin Login**
def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        admin_user = authenticate(request, username=username, password=password)

        if admin_user and admin_user.is_staff:
            login(request, admin_user)
            return redirect('/admin/')
        else:
            return render(request, 'admin/login.html', {'error': 'Invalid credentials or not an admin'})

    return render(request, 'admin/login.html')


### **Custom Login View for Django Auth**
class CustomLoginView(LoginView):
    def get_success_url(self):
        user = self.request.user
        return '/admin/' if user.is_admin else '/'
