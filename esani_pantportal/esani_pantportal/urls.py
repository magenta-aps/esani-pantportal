from django.urls import path
from esani_pantportal.views import PantportalLoginView

urlpatterns = [path("", PantportalLoginView.as_view(), name="login")]
