from django.test import TestCase
from .models import Quote, Customer, RatingResult, PolicyVariable, trunc, normalized_percent, GLOBAL_SCOPE, STATE_TAX_RATE_KEY, PREMIUM_POLICY_BASE_KEY, BASIC_POLICY_BASE_KEY
from .serializers import QuoteSerializer
# Create your tests here.


class ModelTests(TestCase):
    fixtures = ["policy_variables.json" ]
    def test_trunc(self):
        self.assertEqual(trunc(43.12345), 43.12)
        self.assertNotEqual(trunc(43.12999945), 43.13)

    def test_normalized_percent(self):
        self.assertEqual(normalized_percent(9.75), .0975)

    def test_quote_basics(self):

        c = Customer.objects.create(name="Leroy Jenkins")
        quote_description = "This is a great quote"
        q = Quote.objects.create(customer=c,
                                 description=quote_description,
                                 state='TX',
                                 coverage_type='basic')
        self.assertTrue(isinstance(q, Quote))
        self.assertTrue(str(q).startswith(quote_description))
        self.assertEqual(q.customer_name, c.name)
        # This also tests if the rater bombs with no variables
        # attached to the quote.
        rate: RatingResult = q.rate
        policy_base_var = PolicyVariable.objects.get(scope=GLOBAL_SCOPE, key=BASIC_POLICY_BASE_KEY)
        state_tax_var = PolicyVariable.objects.get(scope='TX', key=STATE_TAX_RATE_KEY)
        self.assertEqual(rate.subtotal, policy_base_var.value)
        self.assertAlmostEqual(
            rate.taxes, state_tax_var.value*policy_base_var.value / 100.0)
        
        q.coverage_type = 'premium'
        rate = q.rate
        policy_base_var = PolicyVariable.objects.get(scope=GLOBAL_SCOPE, key=PREMIUM_POLICY_BASE_KEY)
        self.assertEqual(rate.subtotal, policy_base_var.value)
        self.assertAlmostEqual(
            rate.taxes, state_tax_var.value*policy_base_var.value / 100.0)


class CannedScenarioTests(TestCase):
    fixtures = ["customers.json",
                "policy_variables.json",
                "quote_variables.json",
                "quotes.json",
                "variable_specifications.json"]

    def test_quote_one(self):
        q = Quote.objects.get(pk=1)
        rate: RatingResult = q.rate
        self.assertEqual(rate.subtotal, 40.8)
        self.assertEqual(rate.taxes, .40)
        self.assertEqual(rate.total, 41.2)

    def test_quote_two(self):
        q = Quote.objects.get(pk=2)
        rate: RatingResult = q.rate
        self.assertEqual(rate.subtotal, 61.2)
        self.assertEqual(rate.taxes, .61)
        self.assertEqual(rate.total, 61.81)

    def test_quote_three(self):
        q = Quote.objects.get(pk=3)
        rate: RatingResult = q.rate
        self.assertEqual(rate.subtotal, 60.0)
        self.assertEqual(rate.taxes, 1.20)
        self.assertEqual(rate.total, 61.20)

    def test_quote_four(self):
        q = Quote.objects.get(pk=4)
        rate: RatingResult = q.rate
        self.assertEqual(rate.subtotal, 30.0)
        self.assertEqual(rate.taxes, .15)
        self.assertEqual(rate.total, 30.15)


class SerializerTests(TestCase):
    fixtures = ["customers.json",
                "policy_variables",
                "quote_variables.json",
                "quotes.json",
                "variable_specifications.json"]

    def test_serializer_basic(self):
       q = Quote.objects.get(pk=1)
       r = q.rate
       s = QuoteSerializer(q)
       d = s.data
       expected = {'customer_name': q.customer_name,
                   'description': q.description,
                   'state': q.state,
                   'coverage_type': q.coverage_type,
                   'cost': {
                       'subtotal': r.subtotal,
                       'taxes': r.taxes,
                       'total': r.total}}

       self.assertDictEqual(expected, d)
