# Overview
This simple quote rating app used Django as its framework. It uses the admin panel for data entry to save some time and exposes one ModelViewSet for the quotes.

All variables applied into the quote are stored in as a `PolicyVariable`. These values are then pulled based on a profile of (relationships to) `QuoteVariable` and `VariableSpecification`. A `Quote` has many `QuoteVariable` which reifies a `VariableSpecification`. The specification has the information that allows the variable to be quickly templated into the `Quote`.

# Quick Start
1. Setup your [virtual environment](https://docs.python.org/3/library/venv.html)
1. `pip install -r requirements.txt`
1. `python manage.py migrate`
1. `python manage.py loaddata api/fixtures/*.json`
1. `python manage.py runserver`

If you wan to log into the admin panel to poke around ([here](http://localhost:8000/admin) there is a test user with the credentials `user:password` 

# Testing 
To run tests, do:
`coverage run manage.py test -v 2`

... then, if you would like to see a coverage report run:
`coverage html` and point your browser to `htmlcov/index.html`.

# URLs
The quote URL tree is served from a standard ModelViewSet on which `get` and `list` are configured. Check out the `rest.http` file for examples on these. The serializer produces something like this:

```
{
  "customer_name": "Irwin Fletcher",
  "description": "Quote 1",
  "state": "CA",
  "coverage_type": "basic",
  "cost": {
    "subtotal": 40.8,
    "taxes": 0.4,
    "total": 41.2
  }
}
```