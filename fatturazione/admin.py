# coding=utf-8
from fatturazione.models import Fattura, RigaFattura
from django.contrib import admin


class FatturaAdmin(admin.ModelAdmin):
	date_hierarchy = 'data'


admin.site.register(Fattura, FatturaAdmin)
admin.site.register(RigaFattura)
