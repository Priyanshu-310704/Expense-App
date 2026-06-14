from django.contrib import admin

from .models import ExpenseGroup, GroupMembership, Person, PersonAlias

admin.site.register(Person)
admin.site.register(PersonAlias)
admin.site.register(ExpenseGroup)
admin.site.register(GroupMembership)
