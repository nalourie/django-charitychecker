from django.contrib import admin
from .models import IRSNonprofitData

class IRSNonprofitDataAdmin(admin.ModelAdmin):
    readonly_fields = (
        'ein',
        'name',
        'city',
        'state',
        'country',
        'deductability_code')
    search_fields = (
        'ein',
        'name')
admin.site.register(IRSNonprofitData, IRSNonprofitDataAdmin)
