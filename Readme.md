# Overview
This simple quote rating app used Django as its framework. It uses the admin panel for data entry to save some time and exposes one ModelViewSet for the quotes. 

All values are stored somewhere in the database depending on the requirements for that piece of data. There are enterprise-wide policy values stored in the `GlobalPolicyVariable` table. Policies for each state are stored in the `StateRates` table.



# Quick Start
1. Setup your [virtual environment](https://docs.python.org/3/library/venv.html)
1. `pip install -r requirements.txt`
1. `python manage.py migrate`
1. `python manage.py runserver`

# Testing 
To run tests, do:
`coverage run manage.py test -v 2`

... then, if you would like to see a coverage report run:
`coverage html` and point your browser into the `htmlcov/` directory.
