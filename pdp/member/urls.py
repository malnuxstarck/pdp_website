# coding: utf-8

from django.conf.urls import patterns, url

import views

urlpatterns = patterns('',
    url(r'^voir/(?P<user_name>.+)$', views.details),
    url(r'^profil/editer$', views.edit_profile),
    url(r'^parametres/profil$', views.settings_profile),
    url(r'^parametres/compte$', views.settings_account),
    url(r'^connexion$', views.login_view),
    url(r'^inscription$', views.register_view),
    url(r'^deconnexion/$', views.logout_view),
    url(r'^$', views.index),
)
