from django.db import models
from natural_keys import NaturalKeyModel
from collections import namedtuple
from typing import Union
from functools import reduce
from math import floor
from decimal import Decimal, ROUND_DOWN, ROUND_FLOOR

RatingResult = namedtuple("RatingResult", "subtotal taxes total")

COVERAGE_TYPE_CHOICES = (
    ('basic', "Basic"),
    ('premium', "Premium")
)

POLICY_MODIFIER_TYPE_CHOICES = (
    ('indicator', 'Indicator'),
    ('base_flat', 'Base fee or discount'),
    ('base_multiplier', 'Percentage fee or discount'),
)


class Customer(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.name


class StateRates(models.Model):
    state = models.CharField(unique=True, max_length=2, default='')
    flood_multiplier_percent = models.FloatField()
    monthly_tax_percent = models.FloatField()

    def __str__(self) -> str:
        return self.state

    def natural_key(self):
        return (self.state,)


class VariableSpecification(models.Model):
    code = models.CharField(max_length=32, primary_key=True)
    type = models.CharField(
        choices=POLICY_MODIFIER_TYPE_CHOICES, max_length=16)
    description = models.TextField(max_length=512, null=False)
    default_value = models.FloatField(null=True, blank=True)
    priority = models.IntegerField(null=False, default=10)

    def __str__(self) -> str:
        return "{} - {}".format(self.code, self.type)

    def natural_key(self):
        return (self.code, )


class GlobalPolicyVariables(models.Model):
    basic_policy_base = models.FloatField()
    premium_policy_base = models.FloatField()
    pet_premium = models.FloatField()


class QuotesManager(models.Manager):
    def get_queryset(self):
        return (super().
                get_queryset().
                prefetch_related('customer', 'rate_model', 'variables__spec'))


class Quote(models.Model):
    objects = QuotesManager()

    customer = models.ForeignKey(Customer, on_delete=models.DO_NOTHING)
    description = models.CharField(max_length=50, null=True, blank=True)
    rate_model = models.ForeignKey(
        StateRates, db_column='state', to_field='state', null=False, on_delete=models.DO_NOTHING)
    coverage_type = models.CharField(
        choices=COVERAGE_TYPE_CHOICES, null=False, default="basic", max_length=16)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return "{} - {} - {}".format(self.description, self.customer.name, self.coverage_type)

    @property
    def state(self):
        return self.rate_model.state

    @property
    def rate(self) -> RatingResult:
        gp = GlobalPolicyVariables.objects.first()
        rater = PolicyRater(self, self.rate_model, gp)
        return rater.calculate_quote_rate()

    @property
    def customer_name(self) -> str:
        return self.customer.name


class QuoteVariablesManager(models.Manager):
    def get_queryset(self):
        return (super().
                get_queryset().
                prefetch_related("spec").
                order_by("spec__priority"))


class QuoteVariable(models.Model):
    objects = QuoteVariablesManager()

    quote = models.ForeignKey(
        Quote, related_name='variables', on_delete=models.CASCADE)
    spec = models.ForeignKey(VariableSpecification, on_delete=models.CASCADE)
    notes = models.TextField(max_length=1024, null=True, blank=True)
    value = models.FloatField(null=True, blank=True)

    def __str__(self) -> str:
        return "{}-{}".format(self.quote.description, self.spec)

    class Meta:
        unique_together = ('quote', 'spec',)


class PolicyRater:
    def __init__(self, quote: Quote,
                 state_policy: StateRates,
                 global_policy: GlobalPolicyVariables) -> None:
        self.quote = quote
        self.state_policy = state_policy
        self.global_policy = global_policy

    def calculate_quote_rate(self) -> float:
        base = (self.global_policy.basic_policy_base if self.quote.coverage_type == 'basic'
                else self.global_policy.premium_policy_base)
        sub = reduce(lambda acc, var: acc + self.variable_value(acc, var),
                     self.quote.variables.all(),
                     base)
        tax = sub * normalized_percent(self.state_policy.monthly_tax_percent)
        sub = round(sub, 2)
        return RatingResult(subtotal=(sub),
                            taxes=trunc(tax),
                            total=trunc(sub+tax))

    def variable_value(self, base_value: float, var: QuoteVariable) -> float:
        match var.spec.type:
            # case 'base_flat':
            #     return var.value
            # case 'base_multiplier':
            #     return base_value * var.value
            case 'indicator':
                return self.calculate_from_indicator(base_value, var)
        return base_value

    def calculate_from_indicator(self, base_value: float,
                                 var: QuoteVariable) -> float:
        match var.spec.code:
            case 'pet_ownership_indicator':
                return self.global_policy.pet_premium
            case 'flood_addition_indicator':
                return base_value * normalized_percent(self.state_policy.flood_multiplier_percent)
        return base_value


int_or_float = Union[int, float]


def normalized_percent(n: int_or_float) -> float:
    return float(n) / 100.0


TWO_PLACES = Decimal('.01')


def trunc(n: int_or_float) -> float:
    return floor(n * 100) / 100