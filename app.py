from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify

from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
import datetime
from flask_socketio import SocketIO, send, emit, join_room, leave_room


app = Flask(__name__)
app.secret_key = 'your_secret_key'

# SQLite Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bank.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
db = SQLAlchemy(app)
socketio = SocketIO(app)
messages = []

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    social_security_number = db.Column(db.String(12), nullable=False)
    member_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    account_type = db.Column(db.String(50), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.String(20), nullable=False)
    residential_address = db.Column(db.String(200), nullable=False)
    marital_status = db.Column(db.String(20), nullable=False)
    occupation = db.Column(db.String(100), nullable=False)
    debit_card_number = db.Column(db.String(20), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    income = db.Column(db.Float, default=0.0)
    debits = db.Column(db.Float, default=0.0)
    passport_photo = db.Column(db.String(100), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    bitcoin_address = db.Column(db.String(100), nullable=True)
    ethereum_address = db.Column(db.String(100), nullable=True)
    usdt_erc20_address = db.Column(db.String(100), nullable=True)
    usdt_trc20_address = db.Column(db.String(100), nullable=True)
    transactions = db.relationship('Transaction', backref='user', lazy=True)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    ref = db.Column(db.String(100), nullable=True)
    type_of_payment = db.Column(db.String(50), nullable=True)
    scope = db.Column(db.String(50), nullable=True)
    amount = db.Column(db.Float, nullable=True)
    date = db.Column(db.String(50), nullable=True)
    description = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(50), nullable=True)
    beneficiary_account_holder = db.Column(db.String(100), nullable=True)
    bank_name = db.Column(db.String(100), nullable=True)
    transaction_reference = db.Column(db.String(100), nullable=True)
    eur_usd_rate = db.Column(db.Float, nullable=True)
    account_number = db.Column(db.String(100), nullable=True)
    bank_sort_code = db.Column(db.String(100), nullable=True)
    pin1 = db.Column(db.String(1), nullable=True)
    pin2 = db.Column(db.String(1), nullable=True)
    pin3 = db.Column(db.String(1), nullable=True)
    pin4 = db.Column(db.String(1), nullable=True)



class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    loan_amount = db.Column(db.Float, nullable=False)
    credit_facility = db.Column(db.String(100), nullable=False)
    repayment_tenure = db.Column(db.String(50), nullable=False)
    purpose = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Pending')
    date_applied = db.Column(db.String(50), nullable=False)

class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    ticket_id = db.Column(db.String(100), nullable=False)
    customer_service_department = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    complaint = db.Column(db.String(500), nullable=False)
    reply = db.Column(db.String(500), nullable=True)

class KYC(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    ref = db.Column(db.String(100), nullable=False)
    date_submitted = db.Column(db.String(50), nullable=False)
    id_back = db.Column(db.String(100), nullable=False)
    id_front = db.Column(db.String(100), nullable=False)
    passport_photo = db.Column(db.String(100), nullable=True)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(100), nullable=False)
    receiver = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'sender': self.sender,
            'receiver': self.receiver,
            'content': self.content,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }

# class Message(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#     username = db.Column(db.String(80), nullable=False)
#     message = db.Column(db.String(500), nullable=False)
#     timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
#     room = db.Column(db.String(100), nullable=False)
#


# Routes

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        passport_photo_file = request.files['passport_photo']
        passport_photo_filename = None
        if passport_photo_file:
            passport_photo_filename = secure_filename(passport_photo_file.filename)
            passport_photo_file.save(os.path.join(app.config['UPLOAD_FOLDER'], passport_photo_filename))

        new_user = User(
            username=request.form['username'],
            password=request.form['password'],  # No hashing as requested
            social_security_number=request.form['ssn'],
            member_number=request.form['member_number'],
            email=request.form['email'],
            phone_number=request.form['phone_number'],
            account_type=request.form['account_type'],
            full_name=request.form['full_name'],
            date_of_birth=request.form['date_of_birth'],
            residential_address=request.form['residential_address'],
            marital_status=request.form['marital_status'],
            occupation=request.form['occupation'],
            debit_card_number=request.form['debit_card_number'],
            passport_photo=passport_photo_filename
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('signup'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Admin Login
        if request.form['username'] == 'Mayor' and request.form['password'] == 'Mayor':
            session['is_admin'] = True
            flash('Admin logged in successfully', 'success')
            return redirect(url_for('admin_dashboard'))

        # User Login
        user = User.query.filter_by(username=request.form['username'], password=request.form['password']).first()
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin  # Set admin status for user
            flash('User logged in successfully', 'success')
            return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid login credentials', 'danger')
    return render_template('login.html')

@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    transactions = Transaction.query.filter_by(user_id=user.id).all()
    complaints = Complaint.query.filter_by(user_id=user.id).all()
    current_time = datetime.datetime.now()
    # Fetch previous chat messages between the logged-in user and the admin
    admin_name = 'Mayor'  # Assuming admin's username is 'admin'
    # Fetch previous chat messages between the logged-in user and the admin
    admin_name = 'Admin'  # Change as per your admin username
    chat_messages = Message.query.filter(
        ((Message.sender == user.username) & (Message.receiver == admin_name)) |
        ((Message.sender == admin_name) & (Message.receiver == user.username))
    ).all()

    return render_template('dashboard.html', user=user, transactions=transactions, complaints=complaints,
                           messages=messages, current_time=current_time)
@app.route('/transactions')
def transactions():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    transactions = Transaction.query.filter_by(user_id=user.id).all()
    complaints = Complaint.query.filter_by(user_id=user.id).all()
    current_time = datetime.datetime.now()

    return render_template('transactions.html', user=user, transactions=transactions, current_time=current_time)


@app.route('/transactions_details')
def transactions_details():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    transactions = Transaction.query.filter_by(user_id=user.id).all()
    # complaints = Complaint.query.filter_by(user_id=user.id).all()

    return render_template('transactions-details.html', user=user, transactions=transactions)




@app.route('/crypto')
def crypto():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    return render_template('crypto.html', user=user)



@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('is_admin') != True:
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('login'))

    users = User.query.all()
    admin_name = 'Mayor'  # Admin's username
    messages = Message.query.filter(
        (Message.receiver == admin_name) | (Message.sender == admin_name)
    ).all()
    # Fetch previous chat messages between the admin and all users
    # messages = Message.query.filter_by(receiver=admin_name).all()

    return render_template('admin-dashboard.html', users=users, admin_name=admin_name, messages=messages)


@app.route('/get_messages', methods=['GET'])
def get_messages():
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    messages = Message.query.filter(
        (Message.sender == user.username) | (Message.receiver == user.username)
    ).all()
    return jsonify([message.to_dict() for message in messages])


@socketio.on('send_message')
def handle_message(data):
    # Append message to the messages list and save to the database
    message = {
        'sender': data['sender'],
        'receiver': data['receiver'],
        'content': data['content'],
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    messages.append(message)

    # Save to database (optional)
    new_message = Message(sender=data['sender'], receiver=data['receiver'], content=data['content'])
    db.session.add(new_message)
    db.session.commit()

    emit('receive_message', message, broadcast=True)

@app.route('/transfer', methods=['GET', 'POST'])
def transfer():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Create a new transaction
        new_transaction = Transaction(
            user_id=session['user_id'],
            ref=str(datetime.datetime.now()),
            type_of_payment=request.form['type_of_payment'],
            scope=request.form['scope'],
            amount=float(request.form['amount']),
            date=str(datetime.datetime.now().date()),
            description=request.form.get('description'),
            status='Completed',
            beneficiary_account_holder=request.form['account_holder'],
            bank_name=request.form['bank_name'],
            transaction_reference=request.form['transaction_reference'],
            eur_usd_rate=float(request.form['eur_usd_rate']),
            bank_sort_code=int(request.form['bank_sort_code']),
            account_number=int(request.form['account_number'])
        )
        # Add the transaction to the database
        db.session.add(new_transaction)
        db.session.commit()
        flash('Transfer Successful', 'success')
        return redirect(url_for('user_dashboard'))

    # Pass list of banks to the transfer form
    banks = ["Bank of America", "Chase", "Wells Fargo", "Citibank", "Capital One", "PNC Bank", "US Bank", "Morgan Stanley", "U.S. Bancorp", "Truist Financial", "First Horizon National Corporation", "Raymond James Financial", "Deutsche Bank", "Comerica", "New York Community Bank", "First Horizon National Corporation", "Raymond James Financial","Western Alliance Bancorporation", "Webster Bank", "Mizuho Financial Group", "Popular, Inc", "East West Bank", "CIBC Bank USA", "BNP Paribas", "John Deere", "Valley Bank", "Synovus", "Wintrust Financial", "Columbia Bank", "BOK Financial Corporation", "Cullen/Frost Bankers, Inc.","Old National Bank", "Pinnacle Financial Partners", "FNB Corporation", "UMB Financial Corporation", "South State Bank", "Associated Banc-Corp", "Prosperity Bancshares", "Stifel", "EverBank", "Midland", "Banc of California", "Hancock Whitney", "BankUnited", "Sumitomo Mitsui Banking Corporation", "SoFi", "First National of Nebraska", "Commerce Bancshares", "First Interstate BancSystem", "WaFd Bank", "United Bank (West Virginia)", "Texas Capital Bank", "Glacier Bancorp", "FirstBank Holding Co", "Fulton Financial Corporation", "Simmons Bank", "United Community Bank", "Arvest Bank", "BCI Financial Group", "Ameris Bancorp", "First Hawaiian Bank", "Bank of Hawaii", "Cathay Bank", "Credit Suisse", "Home BancShares", "Beal Bank", "Axos Financial", "Atlantic Union Bank", "Customers Bancorp", "Eastern Bank", "WSFS Bank", "Pinnacle Bank", "Independent Bank", "HTLF Bank / Heartland Financial", "Central Bancompany, Inc.", "First BanCorp", "Independent Bank Group, Inc.", "Pacific Premier Bancorp"]
    return render_template('transfer.html', banks=banks)

@app.route('/apply_loan', methods=['GET', 'POST'])
def apply_loan():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # loan = Loan.query.filter_by(user_id=user.id).all()

    user = User.query.get(session['user_id'])
    # loan = Loan.query.filter_by(user_id=user.id).all()

    if request.method == 'POST':
        try:
            loan_amount = float(request.form['loan_amount'])
            credit_facility = request.form['credit_facility']
            repayment_tenure = request.form['repayment_tenure']
            purpose = request.form['purpose']
            date_applied = str(datetime.datetime.now().date())

            # Create a new loan request
            new_loan = Loan(
                user_id=user.id,
                loan_amount=loan_amount,
                credit_facility=credit_facility,
                repayment_tenure=repayment_tenure,
                purpose=purpose,
                status='Pending',
                date_applied=date_applied
            )

            db.session.add(new_loan)
            db.session.commit()

            flash('Loan request submitted successfully!', 'success')
            return redirect(url_for('user_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error submitting loan request: {str(e)}', 'danger')
            return redirect(url_for('apply_loan'))

    # Available credit facilities for the loan form
    credit_facilities = ['Personal Loan', 'Home Loan', 'Car Loan', 'Education Loan']

    return render_template('loan.html', user=user, credit_facilities=credit_facilities)


@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if session.get('is_admin') != True:
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('login'))

    user = User.query.get(user_id)

    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        try:
            # Fetch the form data
            user.username = request.form['username']
            user.email = request.form['email']
            user.phone_number = request.form['phone_number']
            user.account_type = request.form['account_type']
            user.full_name = request.form['full_name']
            user.date_of_birth = request.form['date_of_birth']
            user.residential_address = request.form['residential_address']
            user.marital_status = request.form['marital_status']
            user.occupation = request.form['occupation']
            user.debit_card_number = request.form['debit_card_number']
            user.balance = float(request.form['balance'])
            user.income = float(request.form['income'])
            user.debits = float(request.form['debits'])
            user.bitcoin_address = request.form['bitcoin_address']
            user.ethereum_address = request.form['ethereum_address']
            user.usdt_erc20_address = request.form['usdt_erc20_address']
            user.usdt_trc20_address = request.form['usdt_trc20_address']

            # Handle passport photo update
            if 'passport_photo' in request.files:
                passport_photo_file = request.files['passport_photo']
                if passport_photo_file:
                    passport_photo_filename = secure_filename(passport_photo_file.filename)
                    passport_photo_file.save(os.path.join(app.config['UPLOAD_FOLDER'], passport_photo_filename))
                    user.passport_photo = passport_photo_filename

            # Commit changes
            db.session.commit()
            flash('User details updated successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating user: {str(e)}', 'danger')
            return redirect(url_for('edit_user', user_id=user.id))

    return render_template('edit_user.html',user=user)


@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'user_id' not in session or session['user_id'] != 'admin':
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('login'))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/complaint_form', methods=['GET', 'POST'])
def complaint_form():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_complaint = Complaint(
            user_id=session['user_id'],
            ticket_id=str(datetime.datetime.now()),
            customer_service_department=request.form['department'],
            date=str(datetime.datetime.now().date()),
            complaint=request.form['complaint']
        )
        db.session.add(new_complaint)
        db.session.commit()
        flash('Complaint submitted successfully', 'success')
        return redirect(url_for('user_dashboard'))

    return render_template('complaint-form.html')


@app.route('/kyc_form', methods=['GET', 'POST'])
def kyc_form():
    # Ensure user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Fetch the logged-in user from the database
    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        # Retrieve uploaded files
        id_back_file = request.files['id_back']
        id_front_file = request.files['id_front']

        # Ensure both files are provided
        if id_back_file and id_front_file:
            # Secure filenames and save them to the upload folder
            id_back_filename = secure_filename(id_back_file.filename)
            id_front_filename = secure_filename(id_front_file.filename)

            id_back_file.save(os.path.join(app.config['UPLOAD_FOLDER'], id_back_filename))
            id_front_file.save(os.path.join(app.config['UPLOAD_FOLDER'], id_front_filename))

            # Create a new KYC record
            new_kyc = KYC(
                user_id=session['user_id'],
                ref=str(datetime.datetime.now()),
                date_submitted=str(datetime.datetime.now().date()),
                id_back=id_back_filename,
                id_front=id_front_filename
            )
            # Add the KYC record to the database
            db.session.add(new_kyc)
            db.session.commit()

            flash('KYC submitted successfully', 'success')
            return redirect(url_for('user_dashboard'))

    return render_template('kyc-form.html', user=user)


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))


@app.route('/kyc_overview')
def kyc_overview():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Fetch the logged-in user's information
    user = User.query.get(session['user_id'])

    # Fetch the KYC records for the logged-in user
    kyc_records = KYC.query.filter_by(user_id=user.id).all()

    # Render the kyc_overview template and pass user and KYC records
    return render_template('kyc-overview.html', user=user, kyc_records=kyc_records)


@app.route('/kyc_application')
def kyc_application():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Fetch the logged-in user's information
    user = User.query.get(session['user_id'])

    # # Fetch the KYC records for the logged-in user
    # kyc_records = KYC.query.filter_by(user_id=user.id).all()
    #
    # # Render the kyc_overview template and pass user and KYC records
    return render_template('kyc-application.html', user=user)

@app.route('/kyc_details')
def kyc_details():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Fetch the logged-in user's information
    user = User.query.get(session['user_id'])

    # Fetch the KYC records for the logged-in user
    kyc_records = KYC.query.filter_by(user_id=user.id).all()

    # Render the kyc_overview template and pass user and KYC records
    return render_template('kyc-details.html', user=user, kyc_records=kyc_records)


@app.route('/kyc_thank_you')
def kyc_thank_you():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Fetch the logged-in user's information
    user = User.query.get(session['user_id'])

    # Fetch the KYC records for the logged-in user
    kyc_records = KYC.query.filter_by(user_id=user.id).all()

    # Render the kyc_overview template and pass user and KYC records
    return render_template('kyc-thank-you.html', user=user, kyc_records=kyc_records)


@app.route('/loan')
def loan():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Fetch the logged-in user's information
    user = User.query.get(session['user_id'])

    # Render the kyc_overview template and pass user and KYC records
    return render_template('loan.html', user=user)


@app.route('/summary')
def summary():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    transactions = Transaction.query.filter_by(user_id=user.id).all()
    complaints = Complaint.query.filter_by(user_id=user.id).all()

    return render_template('summary.html', user=user, transactions=transactions)



@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Fetch the logged-in user's information
    user = User.query.get(session['user_id'])

    # Fetch the KYC records for the logged-in user
    kyc_records = KYC.query.filter_by(user_id=user.id).all()

    # Render the kyc_overview template and pass user and KYC records
    return render_template('profile.html', user=user, kyc_records=kyc_records)


@app.route('/profile_cards')
def profile_cards():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Fetch the logged-in user's information
    user = User.query.get(session['user_id'])

    # Fetch the KYC records for the logged-in user
    kyc_records = KYC.query.filter_by(user_id=user.id).all()

    # Render the kyc_overview template and pass user and KYC records
    return render_template('profile-cards.html', user=user, kyc_records=kyc_records)


@app.route('/request_money_success')
def request_money_success():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Fetch the logged-in user's information
    user = User.query.get(session['user_id'])

    # Fetch the KYC records for the logged-in user
    kyc_records = KYC.query.filter_by(user_id=user.id).all()

    # Render the kyc_overview template and pass user and KYC records
    return render_template('request_money_success.html', user=user, kyc_records=kyc_records)



@app.route('/send_money', methods = ['GET', 'POST'])
def send_money():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        # Create a new transaction
        new_transaction = Transaction(
            user_id=session['user_id'],
            beneficiary_account_holder=request.form['account_holder'],
        )

    # Fetch the logged-in user's information
    user = User.query.get(session['user_id'])
    transactions = Transaction.query.filter_by(user_id=user.id).all()
    current_time = datetime.datetime.now()


    # # Fetch the KYC records for the logged-in user
    # kyc_records = KYC.query.filter_by(user_id=user.id).all()

    # Render the kyc_overview template and pass user and KYC records
    return render_template('send-money.html', user=user, transactions=transactions, current_time=current_time)

@app.route('/send_money_accross', methods = ['GET', 'POST'])
def send_money_accross():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Fetch the logged-in user's information
    user = User.query.get(session['user_id'])

    # Fetch the KYC records for the logged-in user
    kyc_records = KYC.query.filter_by(user_id=user.id).all()

    # Render the kyc_overview template and pass user and KYC records
    return render_template('send-money_accross.html', user=user, kyc_records=kyc_records)


@app.route('/send_money_confirm')
def send_money_confirm():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    transactions = Transaction.query.filter_by(user_id=user.id).all()
    last_transaction = transactions[-1] if transactions else None

    current_time = datetime.datetime.now()

    return render_template('send-money-confirm.html', user=user, last_transaction=last_transaction,
                           current_time=current_time)
# @app.route('/send_money_details', methods=['GET', 'POST'])
# def send_money_details():
#     if 'user_id' not in session:
#         return redirect(url_for('login'))
#     user = User.query.get(session['user_id'])
#     transactions = Transaction.query.filter_by(user_id=user.id).all()
#
#     if request.method == 'POST':
#         new_transaction = Transaction(
#             # Ensure that all required fields are present and valid
#             amount = float(request.form['amount']),
#             description = request.form['description'],
#             beneficiary_account_holder = request.form['beneficiary_account_holder'],
#             bank_name = request.form['bank_name'],
#             pin1 = request.form['pin1'],
#             pin2 = request.form['pin2'],
#             pin3 = request.form['pin3'],
#             pin4 = request.form['pin4'],
#         )
#         db.session.add(new_transaction)
#         db.session.commit()
#         flash('Transfer Successful', 'success')
#         return redirect(url_for('send_money_success'))
#
#     banks = ["Bank of America", "Chase", "Wells Fargo", "Citibank", "Capital One", "PNC Bank", "US Bank",
#              "Morgan Stanley", "U.S. Bancorp", "Truist Financial", "First Horizon National Corporation",
#              "Raymond James Financial", "Deutsche Bank", "Comerica", "New York Community Bank",
#              "First Horizon National Corporation", "Raymond James Financial", "Western Alliance Bancorporation",
#              "Webster Bank", "Mizuho Financial Group", "Popular, Inc", "East West Bank", "CIBC Bank USA", "BNP Paribas",
#              "John Deere", "Valley Bank", "Synovus", "Wintrust Financial", "Columbia Bank", "BOK Financial Corporation",
#              "Cullen/Frost Bankers, Inc.", "Old National Bank", "Pinnacle Financial Partners", "FNB Corporation",
#              "UMB Financial Corporation", "South State Bank", "Associated Banc-Corp", "Prosperity Bancshares", "Stifel",
#              "EverBank", "Midland", "Banc of California", "Hancock Whitney", "BankUnited",
#              "Sumitomo Mitsui Banking Corporation", "SoFi", "First National of Nebraska", "Commerce Bancshares",
#              "First Interstate BancSystem", "WaFd Bank", "United Bank (West Virginia)", "Texas Capital Bank",
#              "Glacier Bancorp", "FirstBank Holding Co", "Fulton Financial Corporation", "Simmons Bank",
#              "United Community Bank", "Arvest Bank", "BCI Financial Group", "Ameris Bancorp", "First Hawaiian Bank",
#              "Bank of Hawaii", "Cathay Bank", "Credit Suisse", "Home BancShares", "Beal Bank", "Axos Financial",
#              "Atlantic Union Bank", "Customers Bancorp", "Eastern Bank", "WSFS Bank", "Pinnacle Bank",
#              "Independent Bank", "HTLF Bank / Heartland Financial", "Central Bancompany, Inc.", "First BanCorp",
#              "Independent Bank Group, Inc.", "Pacific Premier Bancorp"]
#
#
#     return render_template('send-money-details.html', user=user, transactions=transactions, banks=banks)

@app.route('/send_money_details', methods=['GET', 'POST'])
def send_money_details():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Fetch user from session
    user = User.query.get(session['user_id'])

    # Fetch all user transactions
    transactions = Transaction.query.filter_by(user_id=user.id).all()

    if request.method == 'POST':
        print(request.form)  # Log submitted form data
        try:
            amount = float(request.form['amount'])
            if amount <= 0:
                flash('Invalid amount. Please enter a positive number.', 'error')
                return redirect(url_for('send_money_details'))

            # Check if the user has enough balance
            if amount > user.balance:
                flash('Insufficient funds. Please check your account balance.', 'error')
                return redirect(url_for('send_money_details'))

            # Create a new transaction
            new_transaction = Transaction(
                amount=amount,
                description=request.form['description'],
                beneficiary_account_holder=request.form['beneficiary_account_holder'],
                bank_name=request.form['bank_name'],
                pin1=request.form['pin1'],
                pin2=request.form['pin2'],
                pin3=request.form['pin3'],
                pin4=request.form['pin4'],
                user_id=user.id  # Link the transaction to the logged-in user
            )

            # Add transaction to the database
            db.session.add(new_transaction)
            db.session.commit()  # Commit transaction

            # Deduct the amount from user balance
            user.balance -= amount
            db.session.commit()  # Commit user balance update

            flash('Transfer Successful!', 'success')
            return redirect(url_for('send_money_confirm'))

        except ValueError:
            flash('Invalid input. Please check your data and try again.', 'error')
            return redirect(url_for('send_money_details'))
        except Exception as e:
            db.session.rollback()
            print(f'Error occurred: {e}')  # Log error details
            flash('An error occurred while processing your transaction.', 'error')
            return redirect(url_for('send_money_details'))
    # List of available banks

    banks = list(set([
        "Bank of America", "Chase", "Wells Fargo", "Citibank", "Capital One", "PNC Bank", "US Bank",
        "Morgan Stanley", "U.S. Bancorp", "Truist Financial", "First Horizon National Corporation",
        "Raymond James Financial", "Deutsche Bank", "Comerica", "New York Community Bank",
        "Western Alliance Bancorporation", "Webster Bank", "Mizuho Financial Group", "Popular, Inc",
        "East West Bank", "CIBC Bank USA", "BNP Paribas", "John Deere", "Valley Bank", "Synovus",
        "Wintrust Financial", "Columbia Bank", "BOK Financial Corporation", "Cullen/Frost Bankers, Inc.",
        "Old National Bank", "Pinnacle Financial Partners", "FNB Corporation", "UMB Financial Corporation",
        "South State Bank", "Associated Banc-Corp", "Prosperity Bancshares", "Stifel", "EverBank",
        "Midland", "Banc of California", "Hancock Whitney", "BankUnited", "Sumitomo Mitsui Banking Corporation",
        "SoFi", "First National of Nebraska", "Commerce Bancshares", "First Interstate BancSystem",
        "WaFd Bank", "United Bank (West Virginia)", "Texas Capital Bank", "Glacier Bancorp",
        "FirstBank Holding Co", "Fulton Financial Corporation", "Simmons Bank", "United Community Bank",
        "Arvest Bank", "BCI Financial Group", "Ameris Bancorp", "First Hawaiian Bank", "Bank of Hawaii",
        "Cathay Bank", "Credit Suisse", "Home BancShares", "Beal Bank", "Axos Financial",
        "Atlantic Union Bank", "Customers Bancorp", "Eastern Bank", "WSFS Bank", "Pinnacle Bank",
        "Independent Bank", "HTLF Bank / Heartland Financial", "Central Bancompany, Inc.", "First BanCorp",
        "Independent Bank Group, Inc.", "Pacific Premier Bancorp"
    ]))

    return render_template('send-money-details.html', user=user, transactions=transactions, banks=banks)


@app.route('/send_money_success')
def send_money_success():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    transactions = Transaction.query.filter_by(user_id=user.id).all()
    last_transaction = transactions[-1] if transactions else None

    current_time = datetime.datetime.now()

    return render_template('send-money-success.html', user=user, last_transaction=last_transaction,
                           current_time=current_time)
# current_time = datetime.datetime.now()


@app.route('/virtual_card')
def virtual_card():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Fetch the logged-in user's information
    user = User.query.get(session['user_id'])

    # Render the virtual_card template and pass user and KYC records
    return render_template('virtual-card.html', user=user)



@app.route('/confirmation')
def confirmation():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    transactions = Transaction.query.filter_by(user_id=user.id).all()
    complaints = Complaint.query.filter_by(user_id=user.id).all()
    current_time = datetime.datetime.now()
    # Fetch previous chat messages between the logged-in user and the admin
    admin_name = 'Mayor'  # Assuming admin's username is 'admin'
    messages = Message.query.filter(
        ((Message.sender == user.username) & (Message.receiver == admin_name)) |
        ((Message.sender == admin_name) & (Message.receiver == user.username))
    ).all()

    return render_template('confirmation.html', user=user, transactions=transactions, complaints=complaints, messages=messages, current_time=current_time)


@socketio.on('send_message')
def handle_send_message(data):
    message = {
        'sender': data['sender'],
        'receiver': data['receiver'],
        'content': data['content'],
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    # Save message to the database (if needed)
    new_message = Message(sender=message['sender'], receiver=message['receiver'], content=message['content'])
    db.session.add(new_message)
    db.session.commit()

    # Broadcast the message to the chat room
    emit('receive_message', message, broadcast=True)


from flask import send_from_directory

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],filename)


# Error Handling
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    db.create_all()  # Create database tables
    socketio.run(app, debug=True)
    # app.run(debug=True)

