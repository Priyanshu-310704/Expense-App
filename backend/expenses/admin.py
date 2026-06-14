from django.contrib import admin

from .models import CurrencyRate, Expense, ExpenseSplit, LedgerEntry, Settlement

admin.site.register(CurrencyRate)
admin.site.register(Expense)
admin.site.register(ExpenseSplit)
admin.site.register(Settlement)
admin.site.register(LedgerEntry)
