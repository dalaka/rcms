from django.contrib import admin

# Register your models here.
from django.contrib import admin

from rcmsapp.models import User, Company, Transaction, Config, Item, Report


class AuthorAdmin(admin.ModelAdmin):
    pass
admin.site.register(User, AuthorAdmin)
admin.site.register(Company)
admin.site.register(Transaction)
admin.site.register(Config)
admin.site.register(Item)
admin.site.register(Report)