from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.http import HttpResponseRedirect


class CustomAdminSite(admin.AdminSite):
    site_header = "AI Copywriter Admin"
    site_title = "AI Copywriter Admin Portal"
    index_title = "Welcome to AI Copywriter Administration"
    
    def index(self, request, extra_context=None):
        """
        Custom admin index that includes link to superadmin dashboard
        """
        extra_context = extra_context or {}
        if request.user.is_superuser:
            extra_context['show_superadmin_link'] = True
        return super().index(request, extra_context)

# Replace the default admin site
admin.site = CustomAdminSite()
admin.sites.site = admin.site