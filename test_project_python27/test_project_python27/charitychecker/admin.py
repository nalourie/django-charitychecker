from django.contrib import admin
from .models import IRSNonprofitData

class IRSNonprofitDataAdmin(admin.ModelAdmin):
    fields = ('ein', 'name', 'city', 'state',
              'country', 'deductability_code')
admin.site.register(IRSNonprofitData, IRSNonprofitDataAdmin)
