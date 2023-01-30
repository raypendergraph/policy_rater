from django.db import models
from natural_keys import NaturalKeyModel
from collections import namedtuple
from typing import Union, List
from functools import reduce
from math import floor
from decimal import Decimal, ROUND_DOWN, ROUND_FLOOR
from collections.abc import Mapping
import logging

BASIC_POLICY_BASE_KEY = "basic_policy_base"
PREMIUM_POLICY_BASE_KEY = "premium_policy_base"
STATE_TAX_RATE_KEY = 'state_tax_rate'
RatingResult = namedtuple("RatingResult", "subtotal taxes total")
COVERAGE_TYPE_BASIC = "basic"
COVERAGE_TYPE_PREMIUM = "premium"
COVERAGE_TYPE_CHOICES = (
    (COVERAGE_TYPE_BASIC, "Basic"),
    (COVERAGE_TYPE_PREMIUM, "Premium")
)
GLOBAL_SCOPE = "global"
VARIABLE_TYPE_STATE_LOOKUP = "state_lookup"
VARIABLE_TYPE_GLOBAL_LOOKUP = "global_lookup"
VARIABLE_TYPE_SIMPLE = "simple"

VARIABLE_TYPE_CHOICES = (
    (VARIABLE_TYPE_STATE_LOOKUP, "State Policy Lookup"),
    (VARIABLE_TYPE_GLOBAL_LOOKUP, "Global Policy Lookup"),
    (VARIABLE_TYPE_SIMPLE, "Simple Value"),
)
QUOTE_STATE_CHOICES = (
    ("NY", "New York"),
    ("CA", "California"),
    ("TX", "Texas"),
)
VARIABLE_APPLICATION_MULTIPLIER = "multiplier"
VARIABLE_APPLICATION_ADDITIVE = "additive"
VARIABLE_APPLICATION_CHOICES = (
    ("multiplier", "Multiplier"),
    ("additive", "Additive"),
)


class PolicyVariableManager(models.Manager):
    def get_variables_in_scope(self, scope: str, *variables: str):
        return self.filter(scope=scope, key__in=list(*variables))


class PolicyVariable(models.Model):
    objects = PolicyVariableManager()

    key = models.CharField(max_length=64, null=False, blank=False, default="")
    scope = models.CharField(max_length=64, null=False,
                             blank=False, default="global")
    value = models.FloatField(null=False, blank=False)

    def __str__(self) -> str:
        return "{}/{} - {}".format(self.scope, self.key, self.value)

    class Meta:
        unique_together = (("key", "scope"),)


class Customer(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.name


class VariableSpecification(models.Model):
    code = models.CharField(max_length=32, primary_key=True)
    # basically determines how the value of the variable is ascertained.
    type = models.CharField(
        choices=VARIABLE_TYPE_CHOICES, max_length=16)
    # defines how the variable is applied to the policy
    application = models.CharField(
        choices=VARIABLE_APPLICATION_CHOICES, max_length=16)
    description = models.TextField(max_length=512, null=False)
    default_value = models.FloatField(null=True, blank=True)
    priority = models.IntegerField(null=False, default=10)
    lookup_key = models.CharField(max_length=64, null=True, blank=True)

    def __str__(self) -> str:
        return "{} - {}".format(self.code, self.type)

    def natural_key(self):
        return (self.code, )


class QuotesManager(models.Manager):
    def get_queryset(self):
        return (super().
                get_queryset().
                prefetch_related("customer", "variables__spec"))


class QuoteVariablesManager(models.Manager):
    def get_queryset(self):
        return (super().
                get_queryset().
                prefetch_related("spec").
                order_by("spec__priority"))


class QuoteVariable(models.Model):
    objects = QuoteVariablesManager()

    quote = models.ForeignKey(
        "Quote", related_name="variables", on_delete=models.CASCADE)
    spec = models.ForeignKey(VariableSpecification, on_delete=models.CASCADE)
    notes = models.TextField(max_length=1024, null=True, blank=True)
    value = models.FloatField(null=True, blank=True)

    def __str__(self) -> str:
        return "{}-{}".format(self.quote.description, self.spec)

    class Meta:
        unique_together = ("quote", "spec",)


class Quote(models.Model):
    objects = QuotesManager()

    customer = models.ForeignKey(Customer, on_delete=models.DO_NOTHING)
    description = models.CharField(max_length=50, null=True, blank=True)
    state = models.CharField(
        choices=QUOTE_STATE_CHOICES, max_length=2, null=False, blank=False)
    coverage_type = models.CharField(
        choices=COVERAGE_TYPE_CHOICES, null=False, default="basic", max_length=16)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return "{} - {} - {}".format(self.description, self.customer.name, self.coverage_type)

    @property
    def rate(self) -> RatingResult:
        pr = PolicyRater(self)
        return pr.calculate_quote_rate()

    @property
    def customer_name(self) -> str:
        return self.customer.name


class PolicyRater:
    def __init__(self, quote: Quote):
        self.quote = quote
        self.vars = vars

    def calculate_quote_rate(self) -> float:
        base_key = BASIC_POLICY_BASE_KEY
        if self.quote.coverage_type == COVERAGE_TYPE_PREMIUM:
            base_key = PREMIUM_POLICY_BASE_KEY
        base_pv = PolicyVariable.objects.get(scope=GLOBAL_SCOPE, key=base_key)
        base_cost = base_pv.value
        sub = reduce(lambda acc, var: acc + self.variable_value(acc, var),
                     self.quote.variables.all(),
                     base_cost)
        # we call out tax separately here because we have to report it as a separate line item. It
        # should be possible to mark variables as taxes and lower their priority so that we could
        # remove this and automatically accumulate all applicable taxes. Then taxes would be calculated
        # with the rest of the variables.
        state_tax_var = PolicyVariable.objects.get(
            scope=self.quote.state, key=STATE_TAX_RATE_KEY)
        tax = sub * normalized_percent(state_tax_var.value)
        sub = round(sub, 2)
        return RatingResult(subtotal=(sub),
                            taxes=trunc(tax),
                            total=trunc(sub+tax))

    def variable_value(self, base_value: float, var: QuoteVariable) -> float:
        var_value = None
        type = var.spec.type
        if type == VARIABLE_TYPE_STATE_LOOKUP:
            pv = PolicyVariable.objects.get(
                scope=self.quote.state, key=var.spec.lookup_key)
            var_value = pv.value
        elif type == VARIABLE_TYPE_GLOBAL_LOOKUP:
            pv = PolicyVariable.objects.get(
                scope=GLOBAL_SCOPE, key=var.spec.lookup_key)
            var_value = pv.value
        elif type == VARIABLE_TYPE_SIMPLE:
            var_value = var.value

        if var_value == None:
            logging.warn("unknown variable type {}".format(type))
            return base_value

        return self.calculate_value(base_value, var.spec.application, var_value)

    def calculate_value(self, base_value: float,
                        application: str,
                        var_value: float) -> float:
        if application == VARIABLE_APPLICATION_ADDITIVE:
            return var_value
        elif application == VARIABLE_APPLICATION_MULTIPLIER:
            return base_value * normalized_percent(var_value)
        logging.WARN(
            "Can't handle application {} so returning base value", application)
        return base_value


IntOrFloat = Union[int, float]


def normalized_percent(n: IntOrFloat) -> float:
    return float(n) / 100.0


def trunc(n: IntOrFloat) -> float:
    return floor(n * 100) / 100
