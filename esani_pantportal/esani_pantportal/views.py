from django.contrib.auth.views import LoginView


class PantportalLoginView(LoginView):
    template_name = "esani_pantportal/login.html"
