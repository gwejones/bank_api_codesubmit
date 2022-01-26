from api import db
from api.models import *

db.drop_all()
db.create_all()

# populate customer table with initial records
initial_customers = None
initial_customers = ['Arisha Barron', 'Branden Gibson', 'Ronda Church', 'Georgina Hazel']
if initial_customers:
    for cust in initial_customers:
        db.session.add(Customer(name=cust))
    db.session.commit()
