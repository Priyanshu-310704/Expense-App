from django.contrib import admin

from .models import ImportAnomaly, ImportBatch, ImportRow

admin.site.register(ImportBatch)
admin.site.register(ImportRow)
admin.site.register(ImportAnomaly)
