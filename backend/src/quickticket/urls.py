"""
URL configuration for quickticket project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django_pyoidc.helper import OIDCHelper
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerOauthRedirectView,
    SpectacularSwaggerView,
)

from quickticket import views

urlpatterns = [
    path("", views.index),
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api-auth/", include("rest_framework.urls")),
]

if hasattr(settings, "DJANGO_PYOIDC"):
    oidc_helper = OIDCHelper(op_name="sso")
    urlpatterns += [
        path(
            "api/docs/oauth2-redirect.html",
            SpectacularSwaggerOauthRedirectView.as_view(),
            name="swagger-ui-oauth",
        ),
        path(
            "auth/",
            include(
                (oidc_helper.get_urlpatterns(), "django_pyoidc"),
                namespace="auth",
            ),
        ),
    ]
