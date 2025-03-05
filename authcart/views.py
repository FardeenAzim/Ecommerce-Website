from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import EmailMessage
from django.contrib.auth import logout, login, authenticate
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from .utils import generate_token 
from django.contrib.auth import get_user_model
from ecommerceapp.models import CustomUser
from .forms import CustomUserCreationForm
from django.contrib.auth.views import LoginView

def clean_string(s):
    return ''.join(c for c in s if ord(c) < 128)  # Keep only ASCII characters


from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect

def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authenticate the user
        admin_user = authenticate(request, username=username, password=password)

        if admin_user and admin_user.is_staff:  # Check if user is staff
            login(request, admin_user)
            return redirect('/admin/')  # Redirect to Django admin panel
        else:
            return render(request, 'admin/login.html', {'error': 'Invalid credentials or not an admin'})

    return render(request, 'admin/login.html')



def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_user = True  # Mark the user as a website user
            user.save()
            login(request, user)
            messages.success(request, "Signup successful! You are now logged in.")
            return redirect('/')
        else:
            # Log or display the errors
            messages.error(request, "Signup failed. Please correct the errors below.")
            print(form.errors)  # Log errors to the console for debugging
    else:
        form = CustomUserCreationForm()

    return render(request, 'authentication/signup.html', {'form': form})


def login_view(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        myuser = authenticate(request, username=email, password=password)
        User = get_user_model()
        
        if myuser:
            login(request, myuser)
            if myuser.is_admin:
                return redirect('/admin/')
            elif myuser.is_user:
                return redirect('/')
        else:
            if not User.objects.filter(email=email).exists():
                messages.error(request, "You are not registered. Please register and try again.")
                return redirect('signup')
            else:
                messages.error(request, "Invalid credentials. Please try again.")
    
    return render(request, "authentication/login.html")


# def login_view(request):
#     if request.method == 'POST':
#         username = request.POST.get('username')
#         password = request.POST.get('password')

#         # Authenticate the user
#         user = authenticate(request, username=username, password=password)

#         if user and not user.is_staff:  # Ensure the user is not an admin
#             login(request, user)
#             return redirect('/')  # Redirect to the website home
#         else:
#             return render(request, 'authentication/login.html', {'error': 'Invalid credentials or admin user'})

#     return render(request, 'authentication/login.html')

# def logout_view(request):
#     logout(request)
#     return redirect('user_login')



def logout_view(request):
    logout(request)
    messages.info(request, "Logged out successfully!")
    return redirect('login')


class CustomLoginView(LoginView):
    def get_success_url(self):
        user = self.request.user
        if user.is_admin:
            return '/admin/'
        elif user.is_user:
            return '/'
        return super().get_success_url()





# def signup(request):
#     if request.method == "POST":
#         username = request.POST.get('username', '').strip()
#         email = request.POST.get('email', '').strip()
#         password = request.POST.get('pass1', '').strip()
#         confirm_password = request.POST.get('pass2', '').strip()

#         # Check if passwords match
#         if password != confirm_password:
#             messages.warning(request, "Passwords do not match.")
#             return render(request, "authentication/signup.html")

#         # Check if user already exists
#         if User.objects.filter(email=email).exists():
#             messages.info(request, "Email already exists.")
#             return render(request, "authentication/signup.html")

#         # Create a new user
#         user = User.objects.create_user(username=username, email=email, password=password)
#         user.is_active = False  # Set to inactive until email verification
#         user.is_staff = False  # Ensure user is not set as staff/admin
#         user.is_superuser = False  # Ensure user is not set as superuser
#         user.save()

#         # Prepare email verification
#         current_site = get_current_site(request)
#         email_subject = "Activate your Account"
#         message = render_to_string('authentication/activate.html', {
#             'user': user,
#             'domain': current_site.domain,
#             'uid': urlsafe_base64_encode(force_bytes(user.pk)),
#             'token': generate_token.make_token(user),
#         })

#         # Clean email subject and message
#         email_subject = clean_string(email_subject)
#         message = clean_string(message)

#         # Create email message
#         email_message = EmailMessage(
#             email_subject,
#             message,
#             to=[email]
#         )
#         email_message.send()

#         messages.success(request, "Activate your account by clicking the link sent to your email.")
#         return redirect('signup')

#     return render(request, "authentication/signup.html")

# def activate(request, uidb64, token):
#     try:
#         uid = force_str(urlsafe_base64_decode(uidb64))
#         user = User.objects.get(pk=uid)
#     except(TypeError, ValueError, OverflowError, User.DoesNotExist):
#         user = None

#     if user is not None and generate_token.check_token(user, token):
#         user.is_active = True  # Activate the user
#         user.save()
#         login(request, user)  # Log the user in
#         return redirect('/')  # Redirect to a success page
#     else:
#         messages.warning(request, "Activation link is invalid!")
#         return render(request, 'activatefail.html')