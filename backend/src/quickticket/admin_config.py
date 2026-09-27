from django.contrib.admin.apps import AdminConfig


class CustomAdmin(AdminConfig):
    default_site = "quickticket.sites.get_site"
