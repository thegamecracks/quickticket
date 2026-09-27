from django.contrib.admin import AdminSite


class OIDCLoginAdminSite(AdminSite):
    login_template = "login.html"
    site_header = "Administration Site"


site = OIDCLoginAdminSite(name="quickticket-admin")


def get_site() -> OIDCLoginAdminSite:
    return site
