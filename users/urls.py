from django.urls import path

from . import views

urlpatterns = [
    path(r'^register/$', views.register, name="register"),
    path(r'^login/$', views.user_login, name="login"),
    path(r'^logout/$', views.user_logout, name="logout"),
    path(r'^user/(?P<username>[0-9a-zA-Z_]*)$', views.user_profile, name="user_profile"),
    path(r'^profile/edit/$', views.edit_profile, name="edit_profile"),
]
