import unittest
import requests
from api import db
from random import choice

class ApiTest(unittest.TestCase):
    API_URL = "http://127.0.0.1:5000"
    LIST_CUSTOMERS_URL = "{}/list_customers".format(API_URL)
    CREATE_ACCOUNT_URL = "{}/create_account".format(API_URL)
    LIST_ACCOUNTS_URL = "{}/list_accounts".format(API_URL)
    GET_BALANCE_URL = "{}/get_balance".format(API_URL)
    LIST_TRANSACTIONS_URL = "{}/list_transactions".format(API_URL)
    TRANSFER_URL = "{}/transfer".format(API_URL)

    def test_get_all_customers(self):
        # find number of records in Customer table
        num = db.engine.execute("SELECT count(*) FROM customer").first()[0]
        r = requests.get(ApiTest.LIST_CUSTOMERS_URL)
        # find number of customer records returned by request
        num_req = len(r.json()['data']['customers'])
        self.assertEqual(num, num_req)
        # check for correct status codes
        if num:
            self.assertEqual(r.status_code, 200)
        else:
            self.assertEqual(r.status_code, 204)

    def test_create_account(self):
        # get random customer id from db
        id = choice(db.engine.execute("SELECT id FROM customer").all())[0]
        dep = 4000      # inital deposit amount
        params = {'cust_id':id, 'init_dep':dep}
        r = requests.post(ApiTest.CREATE_ACCOUNT_URL, params=params)
        acc_id = r.json()['data']['account_id']
        balance = db.engine.execute("SELECT balance FROM account WHERE id = :id", {'id':acc_id}).first()[0]
        self.assertEqual(dep, balance)
        self.assertEqual(r.status_code, 201)

    def test_create_account_zero_deposit(self):
        # get random customer id from db
        id = choice(db.engine.execute("SELECT id FROM customer").all())[0]
        dep = -1      # initial deposit amount, forbidden
        params = {'cust_id':id, 'init_dep':dep}
        r = requests.post(ApiTest.CREATE_ACCOUNT_URL, params=params)
        self.assertEqual(r.status_code, 403)

    def test_list_accounts(self):
        # get random customer id from db
        id = choice(db.engine.execute("SELECT id FROM customer").all())[0]
        # the number of accounts owned, from db
        num_accs_db = db.engine.execute("SELECT count(id) FROM account WHERE owner_id = :id", {'id':id}).first()[0]
        r = requests.get(ApiTest.LIST_ACCOUNTS_URL, params={'cust_id':id})
        if num_accs_db:
            # get number of account records from request response
            num_accs_res = len(r.json()['data']['accounts'])
            self.assertEqual(num_accs_db, num_accs_res)
            self.assertEqual(r.status_code, 200)
        else:
            self.assertEqual(r.status_code, 404)

    def test_get_balance(self):
        # get random account id from db
        id = choice(db.engine.execute("SELECT id FROM account").all())[0]
        # get balance from db
        balance_db = db.engine.execute("SELECT balance FROM account WHERE id = :id",{'id':id}).first()[0]
        # get balance from api request
        r = requests.get(ApiTest.GET_BALANCE_URL, params={'acc_id':id})
        balance_req = r.json()['data']['balance']
        self.assertEqual(balance_req, balance_db)
        self.assertEqual(r.status_code, 200)

    def test_create_transfer(self):
        # get 2 random account ids from db
        id1 = choice(db.engine.execute("SELECT id FROM account").all())[0]
        id2 = choice(db.engine.execute("SELECT id FROM account").all())[0]
        ref = 'hamster tank'
        amount = 1  # amount in grains of salt
        params = {'from_acc':id1, 'to_acc':id2, 'ref':ref, 'amount':amount}
        r = requests.post(ApiTest.TRANSFER_URL, params=params)
        if id1 == id2:      # transfer to and from same account
            self.assertEqual(r.status_code,403)
        else:
            tx_exists = bool(db.engine.execute("SELECT * FROM transfer WHERE from_id = :from_acc AND to_id = :to_acc AND reference = :ref AND amount = :amount", params).first())
            self.assertTrue(tx_exists)
            self.assertEqual(r.status_code,201)

    def test_create_transfer_insuf_funds(self):
        # get 2 random account ids from db
        id1 = choice(db.engine.execute("SELECT id FROM account").all())[0]
        id2 = choice(db.engine.execute("SELECT id FROM account").all())[0]
        ref = 'cat elevator'
        # get balance from db
        amount = db.engine.execute("SELECT balance FROM account WHERE id = :id",{'id':id1}).first()[0]
        amount += 1   # more salt than current balance 
        params = {'from_acc':id1, 'to_acc':id2, 'ref':ref, 'amount':amount}
        r = requests.post(ApiTest.TRANSFER_URL, params=params)
        self.assertEqual(r.status_code,403)

    def test_list_transactions(self):
        # get random account id from db
        id = choice(db.engine.execute("SELECT id FROM account").all())[0]
        # get number of transactions from db
        num_db = db.engine.execute("SELECT count(id) FROM transfer WHERE from_id = :id OR to_id = :id",{'id':id}).first()[0]
        # get number of transactions from api response
        r = requests.get(ApiTest.LIST_TRANSACTIONS_URL,params={'acc_id':id})
        num_resp = len(r.json()['data']['transactions'])
        self.assertEqual(num_resp, num_db)
        self.assertEqual(r.status_code, 200)

if __name__ == '__main__':
    unittest.main()
