from django.contrib import admin
from .models import IRSNonprofitData

class IRSNonprofitDataAdmin(admin.ModelAdmin):
    pass
admin.site.register(IRSNonprofitData, IRSNonprofitDataAdmin)
