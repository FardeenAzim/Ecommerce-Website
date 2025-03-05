from django.shortcuts import redirect

class RestrictAdminMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/admin/'):  # If accessing the admin panel
            if request.user.is_authenticated and not request.user.is_staff:
                return redirect('login')  # Redirect non-staff users to login
        elif request.user.is_authenticated and request.user.is_admin:
            return redirect('/admin/')  # Redirect admin users to the admin panel

        return self.get_response(request)


from django.shortcuts import redirect

class RestrictAdminMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if user is accessing the admin panel
        if request.path.startswith('/admin/'):
            if request.user.is_authenticated and not request.user.is_staff:
                return redirect('user_login')  # Non-staff users cannot access admin

        # Check if admin user tries to access the main website
        elif request.user.is_authenticated and request.user.is_staff:
            return redirect('/admin/')  # Admin users are redirected to admin panel

        return self.get_response(request)