from api.models import *
from api import app
from flask import request, jsonify, make_response 

@app.route('/list_customers', methods=['GET'])
def list_customers():
    """
    Endpoint for listing all customers in the bank database.
    Returns:
        response (JSON) : list of all customers
    """
    try:
        customers = [{'id':row.id, 'name':row.name} for row in Customer.query.all()]
    except:
        response = jsonify({'status':'error', 'message':'unable to query database'})
        return make_response(response,500)
    if customers:   # there are customers found
        response = {'status':'success','data':{'customers':customers}}
        return make_response(jsonify(response), 200)
    else:       # no customers found in database
        response = {'status':'fail', 'message':'no customers found'}
        return make_response(jsonify(response), 204)

@app.route('/create_account', methods=['POST'])
def create_account():
    """
    Endpoint to create new account.
    Parameters:
        cust_id (int) : id of account owner
        init_dep (int) : initial deposit amount
    Returns:
        response (JSON) : success / failure message
    """
    cust_id = request.args.get('cust_id')
    init_dep = request.args.get('init_dep')
    if (not cust_id) or (not init_dep):     # missing parameters
        response = {'status':'fail', 'message':'required arguments <cust_id> and <init_dep> not found'}
        return make_response(jsonify(response),400) 
    elif int(init_dep)<1:       # forbidden deposit amount
        response = {'status':'fail', 'message':'initial deposit must be positive int'}
        return make_response(jsonify(response),403) 
    try:
        customer = Customer.query.filter_by(id=cust_id).first()
        if customer:    # customer exists in database 
            new_acc = Account(balance=int(init_dep), owner=customer)
            new_tx = Transfer(reference='Initial Deposit', amount=int(init_dep), from_acc=new_acc, to_acc=new_acc)
            db.session.add(new_acc)
            db.session.commit()
            response = {'status':'success','data':{'account_id':new_acc.id}}
            return make_response(jsonify(response),201)
        else:           # customer doesnt exist
            message = f"customer with id={cust_id} does not exist"
            response = {'status':'fail', 'message':message}
            return make_response(jsonify(response),406)
    except:
        response = jsonify({'status':'error', 'message':'unable to query database'})
        return make_response(response,500)

@app.route('/list_accounts', methods=['GET'])
def list_accounts():
    """
    Endpoint to list all accounts of a customer.
    Parameters:
        cust_id (int) : id of account owner
    Returns:
        response (JSON) : list of account ids and balances
    """
    cust_id = request.args.get('cust_id')
    if not cust_id:     # missing parameter
        response = {'status':'fail', 'message':'required argument <cust_id> not found'}
        return make_response(jsonify(response), 400)
    try:
        customer = Customer.query.filter_by(id=cust_id).first()
        if not customer:    # customer doesnt exist
            message = f"customer with id={cust_id} does not exist"
            response = {'status':'fail', 'message':message}
            return make_response(jsonify(response),406)
        acc_list = [{'id':acc.id, 'balance':acc.balance} for acc in customer.accounts]
        if acc_list:        # the customer has accounts
            response = {'status':'success','data':{'accounts':acc_list}}
            return make_response(jsonify(response),200)
        else:           # customer has no accounts
            return make_response("",404)
    except:
        response = jsonify({'status':'error', 'message':'unable to query database'})
        return make_response(response,500)

@app.route('/get_balance', methods=['GET'])
def get_balance():
    """
    Retrieves the balance of a given account.
    Parameters:
        acc_id (int) : id of account
    Returns:
        response (JSON) : account balance
    """
    acc_id = request.args.get('acc_id')
    if not acc_id:
        response = {'status':'fail', 'message':'required argument <acc_id> not found'}
        return make_response(jsonify(response), 400)
    try:
        acc = Account.query.filter_by(id=acc_id).first()
        if not acc:     # account doesnt exist
            message = f"account with id={acc_id} does not exist"
            response = {'status':'fail', 'message':message}
            return make_response(jsonify(response),406)
        else:           # account exists
            response = {'status':'success', 'data':{'balance':acc.balance}}
            return make_response(jsonify(response),200)
    except:
        response = jsonify({'status':'error', 'message':'unable to query database'})
        return make_response(response,500)

@app.route('/list_transactions', methods=['GET'])
def list_transactions():
    acc_id = request.args.get('acc_id')
    if not acc_id:
        response = {'status':'fail', 'message':'required argument <acc_id> not found'}
        return make_response(jsonify(response), 400)
    try:
        acc = Account.query.filter_by(id=acc_id).first()
        if not acc:     # account doesnt exist
            message = f"account with id={acc_id} does not exist"
            response = {'status':'fail', 'message':message}
            return make_response(jsonify(response),406)
        # sort transactions choronologically
        transactions = sorted(acc.transfers_in+acc.transfers_out, key=lambda x:x.id)
        # the initial deposit will map twice into the list since it is
        # related by both the 'from_acc' and the 'to_acc' foreign keys
        tx_list = [{'date':transactions[0].create_date, 'ref':transactions[0].reference, 'amount':transactions[0].amount}]
        tx_list += [{'date':tx.create_date, 'ref':tx.reference, 'amount':-tx.amount} if tx.from_acc==acc else {'date':tx.create_date, 'ref':tx.reference, 'amount':tx.amount} for tx in transactions[2:]]
        response = {'status':'success','data':{'transactions':tx_list}}
        return make_response(jsonify(response),200)
    except:
        response = jsonify({'status':'error', 'message':'unable to query database'})
        return make_response(response,500)

@app.route('/transfer',methods=['POST'])
def transfer():
    """
    Registers a transfer between two accounts.
    Parameters:
        from_acc (int) : id of source account
        to_acc (int) : id of destination account
        ref (string) : payment reference
        amount (int) : amount to be transfered
    Returns:
        response (JSON) : success / fail message
    """
    from_acc = request.args.get('from_acc')
    to_acc = request.args.get('to_acc')
    ref = request.args.get('ref')
    amount = request.args.get('amount')
    if not (from_acc and to_acc and ref and amount):
        response = {'status':'fail', 'message':'required argument(s) <from_acc>, <to_acc>, <ref>, <amount> not found'}
        return make_response(jsonify(response), 400)
    try:
        from_account = Account.query.filter_by(id=from_acc).first()
        to_account = Account.query.filter_by(id=to_acc).first()
        if not from_account:    # source acc doesnt exist
            message = f"payment account id={from_acc} doesnt exist"
            response = {'status':'fail', 'message':message}
            return make_response(jsonify(response),404)
        elif not to_account:    # dest account doesnt exist
            message = f"beneficiary account id={to_acc} doesnt exist"
            response = {'status':'fail', 'message':message}
            return make_response(jsonify(response),404)
        elif int(amount)<0:     # forbidden amount
            message = f"cannot transfer a negative amount"
            response = {'status':'fail', 'message':message}
            return make_response(jsonify(response),403)
        elif from_acc == to_acc:    # transfer to same account
            message = "cannot transfer from and to identical account"
            response = {'status':'fail', 'message':message}
            return make_response(jsonify(response),403)
        elif from_account.balance < int(amount):    # inusfficient funds
            message = "insufficient funds"
            response = {'status':'fail', 'message':message}
            return make_response(jsonify(response),403)
        else:       # all requirements met to affect the transfer
            # adjust balances in db
            from_account.balance -= int(amount)
            to_account.balance += int(amount)
            # insert transfer into db
            tx = Transfer(from_acc=from_account, to_acc=to_account, reference=ref, amount=amount)
            db.session.add(tx)
            db.session.commit()
            response = {'status':'success'}
            return make_response(jsonify(response), 201)
    except:
        response = jsonify({'status':'error', 'message':'unable to query database'})
        return make_response(response,500)

