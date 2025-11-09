from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from functools import wraps
import razorpay

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'gaming_platform'
mysql = MySQL(app)

# Razorpay Configuration
RAZORPAY_KEY_ID = 'your_razorpay_key_id'
RAZORPAY_KEY_SECRET = 'your_razorpay_key_secret'
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_admin'):
            flash('Admin access required', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('landing.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        gpay_number = request.form['gpay_number']
        pubg_usernames = request.form.getlist('pubg_username[]')
        
        hashed_password = generate_password_hash(password)
        
        cur = mysql.connection.cursor()
        try:
            # Insert user
            cur.execute("INSERT INTO users (username, password, gpay_number, coins) VALUES (%s, %s, %s, 0)",
                       (username, hashed_password, gpay_number))
            user_id = cur.lastrowid
            
            # Insert PUBG usernames
            for pubg_username in pubg_usernames:
                if pubg_username.strip():
                    cur.execute("INSERT INTO pubg_usernames (user_id, pubg_username) VALUES (%s, %s)",
                               (user_id, pubg_username.strip()))
            
            mysql.connection.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Registration failed: {str(e)}', 'danger')
        finally:
            cur.close()
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, username, password, is_admin FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        
        if user and check_password_hash(user[2], password):
            print(">>>>>>>>>>>>>>>>>1<<<<<<<<<<<<<<<")
            print(user)
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['is_admin'] = user[3]
            flash('Login successful!', 'success')
            if user[3]:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/home')
@login_required
def home():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT r.id, r.room_name, r.entry_fee, r.prize_pool, r.max_players, r.game_type,
               COUNT(e.id) as enrolled_count, r.status
        FROM rooms r
        LEFT JOIN enrollments e ON r.id = e.room_id
        WHERE r.status = 'open'
        GROUP BY r.id
        ORDER BY r.created_at DESC
    """)
    rooms = cur.fetchall()
    
    cur.execute("SELECT coins FROM users WHERE id = %s", (session['user_id'],))
    user_coins = cur.fetchone()[0]
    cur.close()
    
    return render_template('home.html', rooms=rooms, user_coins=user_coins)

@app.route('/room/<int:room_id>', methods=['GET', 'POST'])
@login_required
def room_details(room_id):
    cur = mysql.connection.cursor()
    
    if request.method == 'POST':
        pubg_username_id = request.form['pubg_username']
        
        # Check if user has enough coins
        cur.execute("SELECT coins FROM users WHERE id = %s", (session['user_id'],))
        user_coins = cur.fetchone()[0]
        
        cur.execute("SELECT entry_fee FROM rooms WHERE id = %s", (room_id,))
        entry_fee = cur.fetchone()[0]
        
        if user_coins < entry_fee:
            flash('Insufficient coins!', 'danger')
            return redirect(url_for('room_details', room_id=room_id))
        
        try:
            # Deduct coins
            cur.execute("UPDATE users SET coins = coins - %s WHERE id = %s", (entry_fee, session['user_id']))
            
            # Enroll user
            cur.execute("""
                INSERT INTO enrollments (room_id, user_id, pubg_username_id, payment_status)
                VALUES (%s, %s, %s, 'paid')
            """, (room_id, session['user_id'], pubg_username_id))
            
            mysql.connection.commit()
            flash('Enrolled successfully!', 'success')
            return redirect(url_for('room_enrollments', room_id=room_id))
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Enrollment failed: {str(e)}', 'danger')
    
    # Get room details
    cur.execute("SELECT * FROM rooms WHERE id = %s", (room_id,))
    room = cur.fetchone()
    
    # Get user's PUBG usernames
    cur.execute("SELECT id, pubg_username FROM pubg_usernames WHERE user_id = %s", (session['user_id'],))
    pubg_usernames = cur.fetchall()
    
    # Get user coins
    cur.execute("SELECT coins FROM users WHERE id = %s", (session['user_id'],))
    user_coins = cur.fetchone()[0]
    
    cur.close()
    
    return render_template('room_details.html', room=room, pubg_usernames=pubg_usernames, user_coins=user_coins)

@app.route('/room/<int:room_id>/enrollments')
@login_required
def room_enrollments(room_id):
    cur = mysql.connection.cursor()
    
    cur.execute("SELECT * FROM rooms WHERE id = %s", (room_id,))
    room = cur.fetchone()
    
    cur.execute("""
        SELECT u.username, pu.pubg_username, e.enrolled_at
        FROM enrollments e
        JOIN users u ON e.user_id = u.id
        JOIN pubg_usernames pu ON e.pubg_username_id = pu.id
        WHERE e.room_id = %s
        ORDER BY e.enrolled_at DESC
    """, (room_id,))
    enrollments = cur.fetchall()
    
    cur.close()
    
    return render_template('room_enrollments.html', room=room, enrollments=enrollments)

@app.route('/profile')
@login_required
def profile():
    cur = mysql.connection.cursor()
    
    cur.execute("SELECT username, gpay_number, coins FROM users WHERE id = %s", (session['user_id'],))
    user = cur.fetchone()
    
    cur.execute("SELECT id, pubg_username FROM pubg_usernames WHERE user_id = %s", (session['user_id'],))
    pubg_usernames = cur.fetchall()
    
    cur.execute("""
        SELECT w.id, w.amount, w.gpay_number, w.status, w.requested_at, w.payment_screenshot
        FROM withdrawals w
        WHERE w.user_id = %s
        ORDER BY w.requested_at DESC
    """, (session['user_id'],))
    withdrawals = cur.fetchall()
    
    cur.close()
    
    return render_template('profile.html', user=user, pubg_usernames=pubg_usernames, withdrawals=withdrawals)

@app.route('/add_coins', methods=['POST'])
@login_required
def add_coins():
    amount = int(request.form['amount'])
    
    # Create Razorpay order
    order_data = {
        'amount': amount * 100,  # Amount in paise
        'currency': 'INR',
        'payment_capture': 1
    }
    
    try:
        order = razorpay_client.order.create(data=order_data)
        return jsonify({'order_id': order['id'], 'amount': amount})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/payment_success', methods=['POST'])
@login_required
def payment_success():
    payment_id = request.form['payment_id']
    amount = int(request.form['amount'])
    
    cur = mysql.connection.cursor()
    try:
        # Add coins to user account
        cur.execute("UPDATE users SET coins = coins + %s WHERE id = %s", (amount, session['user_id']))
        
        # Record transaction
        cur.execute("""
            INSERT INTO transactions (user_id, type, amount, payment_id)
            VALUES (%s, 'credit', %s, %s)
        """, (session['user_id'], amount, payment_id))
        
        mysql.connection.commit()
        flash(f'{amount} coins added successfully!', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Payment processing failed: {str(e)}', 'danger')
    finally:
        cur.close()
    
    return redirect(url_for('profile'))

@app.route('/withdraw', methods=['POST'])
@login_required
def withdraw():
    amount = int(request.form['amount'])
    gpay_number = request.form.get('gpay_number')
    
    if amount < 150:
        flash('Minimum withdrawal amount is 150 Rs', 'danger')
        return redirect(url_for('profile'))
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT coins, gpay_number FROM users WHERE id = %s", (session['user_id'],))
    user = cur.fetchone()
    
    if user[0] < amount:
        flash('Insufficient coins!', 'danger')
        return redirect(url_for('profile'))
    
    gpay_number = gpay_number if gpay_number else user[1]
    
    try:
        cur.execute("UPDATE users SET coins = coins - %s WHERE id = %s", (amount, session['user_id']))
        cur.execute("""
            INSERT INTO withdrawals (user_id, amount, gpay_number, status)
            VALUES (%s, %s, %s, 'pending')
        """, (session['user_id'], amount, gpay_number))
        mysql.connection.commit()
        flash('Withdrawal request submitted!', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Withdrawal failed: {str(e)}', 'danger')
    finally:
        cur.close()
    
    return redirect(url_for('profile'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    cur = mysql.connection.cursor()
    
    cur.execute("""
        SELECT w.id, u.username, w.amount, w.gpay_number, w.status, w.requested_at
        FROM withdrawals w
        JOIN users u ON w.user_id = u.id
        WHERE w.status = 'pending'
        ORDER BY w.requested_at DESC
    """)
    pending_withdrawals = cur.fetchall()
    
    cur.execute("SELECT * FROM rooms ORDER BY created_at DESC")
    rooms = cur.fetchall()
    
    cur.close()
    
    return render_template('admin_dashboard.html', pending_withdrawals=pending_withdrawals, rooms=rooms)

@app.route('/admin/approve_withdrawal/<int:withdrawal_id>', methods=['POST'])
@admin_required
def approve_withdrawal(withdrawal_id):
    screenshot = request.files.get('screenshot')
    
    if screenshot:
        filename = secure_filename(f"{withdrawal_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        screenshot.save(filepath)
        
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE withdrawals 
            SET status = 'approved', payment_screenshot = %s, processed_at = NOW()
            WHERE id = %s
        """, (filename, withdrawal_id))
        mysql.connection.commit()
        cur.close()
        
        flash('Withdrawal approved!', 'success')
    else:
        flash('Please upload payment screenshot', 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/create_room', methods=['POST'])
@admin_required
def create_room():
    room_name = request.form['room_name']
    game_type = request.form['game_type']
    entry_fee = int(request.form['entry_fee'])
    prize_pool = int(request.form['prize_pool'])
    max_players = int(request.form['max_players'])
    room_id_game = request.form['room_id_game']
    room_password = request.form['room_password']
    
    cur = mysql.connection.cursor()
    try:
        cur.execute("""
            INSERT INTO rooms (room_name, game_type, entry_fee, prize_pool, max_players, room_id_game, room_password, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'open')
        """, (room_name, game_type, entry_fee, prize_pool, max_players, room_id_game, room_password))
        mysql.connection.commit()
        flash('Room created successfully!', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Room creation failed: {str(e)}', 'danger')
    finally:
        cur.close()
    
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)