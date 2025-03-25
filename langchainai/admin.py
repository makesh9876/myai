
# Register your models here.
from django.contrib import admin
from .models import KeyConfiguration, CustomerMessage

@admin.register(KeyConfiguration)
class KeyConfiguration(admin.ModelAdmin):
    list_display = ('key', 'value')  # Fields shown in the admin list view
    search_fields = ('key',)  # Enable search by 'key'





@admin.register(CustomerMessage)
class CustomerMessage(admin.ModelAdmin):
    list_display = ('user_name', 'text')  # Fields shown in the admin list view
    search_fields = ('user_name',)  # Enable search by 'key'