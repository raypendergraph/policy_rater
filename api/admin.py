from django.contrib import admin
from django import forms
from .models import Quote, VariableSpecification, StateRates, Customer, QuoteVariable, GlobalPolicyVariables


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):

    def get_readonly_fields(self, request, obj=None):
        return ('created_at', 'updated_at')

@admin.register(QuoteVariable)
class QuoteVariableAdmin(admin.ModelAdmin):
    pass


@admin.register(VariableSpecification)
class VariableSpecificationAdmin(admin.ModelAdmin):
    pass


@admin.register(StateRates)
class StateRatesAdmin(admin.ModelAdmin):
    pass


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    pass

@admin.register(GlobalPolicyVariables)
class GlobalPolicyVariablesAdmin(admin.ModelAdmin):
    pass