from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from functools import wraps
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configuration
app.secret_key = os.getenv('SECRET_KEY', 'fallback-secret-key-change-this')
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'static/uploads')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16777216))  # 16MB default

# MySQL Configuration
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '1111')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'gaming_platform')

# Production settings
if os.getenv('FLASK_ENV') == 'production':
    app.config['DEBUG'] = False
    # Set up logging for production
    logging.basicConfig(level=logging.INFO)
else:
    app.config['DEBUG'] = True

mysql = MySQL(app)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Context processor to make user_coins available in all templates
@app.context_processor
def inject_user_coins():
    if 'user_id' in session:
        cur = mysql.connection.cursor()
        try:
            cur.execute("SELECT coins FROM users WHERE id = %s", (session['user_id'],))
            result = cur.fetchone()
            user_coins = result[0] if result else 0
        except:
            user_coins = 0
        finally:
            cur.close()
        return {'user_coins': user_coins}
    return {'user_coins': 0}

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

@app.route('/health')
def health_check():
    """Health check endpoint for deployment platforms"""
    try:
        # Simple database connectivity test
        cur = mysql.connection.cursor()
        cur.execute("SELECT 1")
        cur.close()
        return jsonify({
            'status': 'healthy',
            'message': 'Gaming platform is running',
            'database': 'connected'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'message': 'Database connection failed',
            'error': str(e)
        }), 503

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        gpay_number = request.form['gpay_number']
        pubg_usernames = request.form.getlist('pubg_username[]')
        
        cur = mysql.connection.cursor()
        try:
            # Insert user
            cur.execute("INSERT INTO users (username, password, gpay_number, coins) VALUES (%s, %s, %s, 0)",
                       (username, password, gpay_number))
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
        
        if user and user[2] == password:
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
    # Temporary fix - use old query structure until new tables are created
    cur.execute("""
        SELECT r.id, r.room_name, r.entry_fee, r.prize_pool, r.max_players, r.game_type,
               0 as team_count, r.status, 
               COALESCE(r.event_timing, NOW()) as event_timing, 
               COALESCE(r.is_multiplayer, 1) as is_multiplayer,
               COALESCE(r.min_team_size, 1) as min_team_size, 
               COALESCE(r.max_team_size, 4) as max_team_size,
               0 as enrolled_players
        FROM rooms r
        WHERE r.status = 'open'
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
    
    # Get room details
    try:
        cur.execute("SELECT * FROM rooms WHERE id = %s", (room_id,))
        room = cur.fetchone()
    except Exception as e:
        print(f"Error in room details query: {e}")
        room = None
    
    if not room:
        flash('Room not found', 'danger')
        return redirect(url_for('home'))
    
    # Check if user is already enrolled in this room using NEW gaming IDs system
    cur.execute("""
        SELECT COUNT(*) FROM room_user_enrollments
        WHERE room_id = %s AND user_id = %s AND is_active = TRUE
    """, (room_id, session['user_id']))
    
    user_already_enrolled = cur.fetchone()[0] > 0
    
    # Get user's active gaming IDs count
    cur.execute("""
        SELECT COUNT(*) FROM user_gaming_ids
        WHERE user_id = %s AND is_active = TRUE
    """, (session['user_id'],))
    user_gaming_ids_count = cur.fetchone()[0]
    
    # Get user coins
    cur.execute("SELECT coins FROM users WHERE id = %s", (session['user_id'],))
    user_coins = cur.fetchone()[0]
    
    # Check if user is blocked from this room
    cur.execute("SELECT id FROM blocked_users WHERE room_id = %s AND user_id = %s", (room_id, session['user_id']))
    user_is_blocked = cur.fetchone() is not None
    
    # Calculate current enrolled players using NEW gaming IDs system
    cur.execute("""
        SELECT COALESCE(SUM(gaming_ids_count), 0) as total_players
        FROM room_user_enrollments
        WHERE room_id = %s AND payment_status = 'paid' AND is_active = TRUE
    """, (room_id,))
    current_total_players = cur.fetchone()[0]
    available_slots = room[5] - current_total_players  # room[5] is max_players
    
    cur.close()
    
    return render_template('room_details.html', room=room, user_coins=user_coins,
                         current_players=current_total_players, available_slots=available_slots,
                         user_is_blocked=user_is_blocked, user_already_enrolled=user_already_enrolled,
                         user_gaming_ids_count=user_gaming_ids_count)

@app.route('/room/<int:room_id>/enrollments')
@login_required
def room_enrollments(room_id):
    cur = mysql.connection.cursor()
    
    cur.execute("SELECT * FROM rooms WHERE id = %s", (room_id,))
    room = cur.fetchone()
    
    # Get NEW gaming ID enrollments
    cur.execute("""
        SELECT rue.id, rue.user_id, u.username, rue.gaming_ids_count, 
               rue.total_entry_fee, rue.enrolled_at, rue.payment_status,
               GROUP_CONCAT(CONCAT(ug.display_name, ' (', ug.gaming_platform, ')') SEPARATOR ', ') as gaming_ids_display
        FROM room_user_enrollments rue
        JOIN users u ON rue.user_id = u.id
        LEFT JOIN room_gaming_ids rg ON rue.id = rg.room_user_enrollment_id
        LEFT JOIN user_gaming_ids ug ON rg.user_gaming_id = ug.id
        WHERE rue.room_id = %s AND rue.is_active = TRUE
        GROUP BY rue.id
        ORDER BY rue.enrolled_at DESC
    """, (room_id,))
    gaming_id_enrollments = cur.fetchall()
    
    # Get OLD team enrollments (for backward compatibility)
    cur.execute("""
        SELECT rte.id, ut.team_name, ut.team_email, u.username as leader, 
               rte.total_entry_fee, rte.enrolled_at as created_at, rte.payment_status,
               COUNT(utm.id) as member_count
        FROM room_team_enrollments rte
        JOIN user_teams ut ON rte.user_team_id = ut.id
        JOIN users u ON ut.user_id = u.id
        LEFT JOIN user_team_members utm ON ut.id = utm.user_team_id
        WHERE rte.room_id = %s
        GROUP BY rte.id, ut.id, u.id
        ORDER BY rte.enrolled_at DESC
    """, (room_id,))
    team_enrollments = cur.fetchall()
    
    # Calculate total players from BOTH systems
    total_players_gaming_ids = sum(enrollment[3] for enrollment in gaming_id_enrollments if enrollment[6] == 'paid')
    total_players_teams = sum(team[7] for team in team_enrollments if team[6] == 'paid')
    total_players = total_players_gaming_ids + total_players_teams
    
    # Get team members for old team enrollments
    team_members = {}
    for team in team_enrollments:
        cur.execute("SELECT user_team_id FROM room_team_enrollments WHERE id = %s", (team[0],))
        user_team_result = cur.fetchone()
        if user_team_result:
            user_team_id = user_team_result[0]
            cur.execute("""
                SELECT utm.member_username, utm.gaming_id, utm.joined_at
                FROM user_team_members utm
                WHERE utm.user_team_id = %s
                ORDER BY utm.joined_at ASC
            """, (user_team_id,))
            team_members[team[0]] = cur.fetchall()
    
    # Get detailed gaming IDs for each enrollment
    gaming_id_details = {}
    for enrollment in gaming_id_enrollments:
        cur.execute("""
            SELECT ug.gaming_platform, ug.gaming_username, ug.display_name, rg.kills_count, rg.reward_earned, rg.status
            FROM room_gaming_ids rg
            JOIN user_gaming_ids ug ON rg.user_gaming_id = ug.id
            WHERE rg.room_user_enrollment_id = %s
            ORDER BY ug.gaming_platform, ug.display_name
        """, (enrollment[0],))
        gaming_id_details[enrollment[0]] = cur.fetchall()
    
    # Print debug info
    print(f"=== UPDATED ROOM ENROLLMENTS DEBUG ===")
    print(f"Room ID: {room_id}")
    print(f"Room Name: {room[1] if room else 'Unknown'}")
    print(f"Gaming ID Enrollments: {len(gaming_id_enrollments)}")
    print(f"Team Enrollments: {len(team_enrollments)}")
    print(f"Total Players (Gaming IDs): {total_players_gaming_ids}")
    print(f"Total Players (Teams): {total_players_teams}")
    print(f"Total Players (Combined): {total_players}")
    print(f"Max Players: {room[5] if room else 'Unknown'}")
    print("=== Gaming ID Enrollments ===")
    for i, enrollment in enumerate(gaming_id_enrollments, 1):
        status = "✅ Paid" if enrollment[6] == 'paid' else "⚠️ Pending"
        print(f"Enrollment {i}: {enrollment[2]} - {enrollment[3]} gaming IDs ({status})")
    print("===============================")
    
    cur.close()
    
    return render_template('room_enrollments.html', 
                         total_player_in_room=total_players, 
                         room=room, 
                         teams=team_enrollments,  # Old team enrollments
                         team_members=team_members,
                         gaming_id_enrollments=gaming_id_enrollments,  # New gaming ID enrollments
                         gaming_id_details=gaming_id_details,
                         total_players_gaming_ids=total_players_gaming_ids,
                         total_players_teams=total_players_teams)

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

@app.route('/my_teams')
@login_required
def my_teams():
    cur = mysql.connection.cursor()
    
    # Get user's teams
    cur.execute("""
        SELECT ut.id, ut.team_name, ut.team_email, ut.is_active, ut.created_at,
               COUNT(utm.id) as member_count
        FROM user_teams ut
        LEFT JOIN user_team_members utm ON ut.id = utm.user_team_id
        WHERE ut.user_id = %s
        GROUP BY ut.id
        ORDER BY ut.created_at DESC
    """, (session['user_id'],))
    teams = cur.fetchall()
    
    # Get team members for each team
    team_members = {}
    for team in teams:
        cur.execute("""
            SELECT member_username, gaming_id, email, is_leader
            FROM user_team_members
            WHERE user_team_id = %s
            ORDER BY is_leader DESC, member_username ASC
        """, (team[0],))
        team_members[team[0]] = cur.fetchall()
    
    cur.close()
    
    return render_template('my_teams.html', teams=teams, team_members=team_members)

@app.route('/create_team', methods=['GET', 'POST'])
@login_required
def create_user_team():
    if request.method == 'POST':
        team_name = request.form['team_name']
        team_email = request.form['team_email']
        member_usernames = request.form.getlist('member_username[]')
        gaming_ids = request.form.getlist('gaming_id[]')
        member_emails = request.form.getlist('member_email[]')
        
        cur = mysql.connection.cursor()
        try:
            # Count valid members first
            count = 0;
            valid_members = [username for username in member_usernames if username.strip()]
            
            team_size = len(member_emails)
            
            # Create team with team_size
            cur.execute("""
                INSERT INTO user_teams (user_id, team_name, team_email, team_size)
                VALUES (%s, %s, %s, %s)
            """, (session['user_id'], team_name, team_email, team_size))
            
            team_id = cur.lastrowid
            
            # Add team members
            for i, username in enumerate(member_usernames):
                if username.strip():
                    gaming_id = gaming_ids[i].strip() if i < len(gaming_ids) else ''
                    member_email = member_emails[i].strip() if i < len(member_emails) else ''
                    is_leader = username.strip() == session['username']
                    
                    cur.execute("""
                        INSERT INTO user_team_members (user_team_id, member_username, gaming_id, email, is_leader)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (team_id, username.strip(), gaming_id, member_email, is_leader))
            
            mysql.connection.commit()
            flash('Team created successfully!', 'success')
            return redirect(url_for('my_teams'))
            
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Team creation failed: {str(e)}', 'danger')
        finally:
            cur.close()
    
    return render_template('create_team.html')

@app.route('/edit_team/<int:team_id>', methods=['GET', 'POST'])
@login_required
def edit_team(team_id):
    cur = mysql.connection.cursor()
    
    # Verify team ownership
    cur.execute("SELECT * FROM user_teams WHERE id = %s AND user_id = %s", (team_id, session['user_id']))
    team = cur.fetchone()
    
    if not team:
        flash('Team not found or access denied', 'danger')
        return redirect(url_for('my_teams'))
    
    if request.method == 'POST':
        team_name = request.form['team_name']
        team_email = request.form['team_email']
        member_usernames = request.form.getlist('member_username[]')
        gaming_ids = request.form.getlist('gaming_id[]')
        member_emails = request.form.getlist('member_email[]')
        
        try:
            # Count valid members first
            valid_members = [username for username in member_usernames if username.strip()]
            team_size = len(valid_members)
            
            # Update team with team_size
            cur.execute("""
                UPDATE user_teams 
                SET team_name = %s, team_email = %s, team_size = %s, updated_at = NOW()
                WHERE id = %s
            """, (team_name, team_email, team_size, team_id))
            
            # Delete existing members
            cur.execute("DELETE FROM user_team_members WHERE user_team_id = %s", (team_id,))
            
            # Add updated members
            for i, username in enumerate(member_usernames):
                if username.strip():
                    gaming_id = gaming_ids[i].strip() if i < len(gaming_ids) else ''
                    member_email = member_emails[i].strip() if i < len(member_emails) else ''
                    is_leader = username.strip() == session['username']
                    
                    cur.execute("""
                        INSERT INTO user_team_members (user_team_id, member_username, gaming_id, email, is_leader)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (team_id, username.strip(), gaming_id, member_email, is_leader))
            
            mysql.connection.commit()
            flash('Team updated successfully!', 'success')
            return redirect(url_for('my_teams'))
            
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Team update failed: {str(e)}', 'danger')
        finally:
            cur.close()
    
    # Get team members for editing
    cur.execute("""
        SELECT member_username, gaming_id, email, is_leader
        FROM user_team_members
        WHERE user_team_id = %s
        ORDER BY is_leader DESC, member_username ASC
    """, (team_id,))
    members = cur.fetchall()
    
    cur.close()
    
    return render_template('edit_team.html', team=team, members=members)

@app.route('/toggle_team/<int:team_id>', methods=['POST'])
@login_required
def toggle_team(team_id):
    cur = mysql.connection.cursor()
    try:
        # Verify team ownership
        cur.execute("SELECT id FROM user_teams WHERE id = %s AND user_id = %s", (team_id, session['user_id']))
        if not cur.fetchone():
            return jsonify({'success': False, 'message': 'Team not found'})
        
        data = request.get_json()
        activate = data.get('activate', True)
        
        cur.execute("UPDATE user_teams SET is_active = %s WHERE id = %s", (activate, team_id))
        mysql.connection.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cur.close()

@app.route('/add_coins', methods=['POST'])
@login_required
def add_coins():
    if 'payment_screenshot' not in request.files:
        flash('Payment screenshot is required!', 'danger')
        return redirect(url_for('profile'))
    
    file = request.files['payment_screenshot']
    amount = int(request.form['amount'])
    
    if file.filename == '':
        flash('Please select a payment screenshot!', 'danger')
        return redirect(url_for('profile'))
    
    if amount < 10:
        flash('Minimum payment amount is 10 Rs', 'danger')
        return redirect(url_for('profile'))
    
    # Check file extension
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
        flash('Only image files (PNG, JPG, JPEG, GIF) are allowed!', 'danger')
        return redirect(url_for('profile'))
    
    try:
        # Save screenshot with unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = secure_filename(f"payment_{session['user_id']}_{timestamp}_{file.filename}")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        cur = mysql.connection.cursor()
        try:
            # Record transaction as pending for admin approval
            cur.execute("""
                INSERT INTO transactions (user_id, type, amount, payment_screenshot, status)
                VALUES (%s, 'credit_pending', %s, %s, 'pending')
            """, (session['user_id'], amount, filename))
            
            mysql.connection.commit()
            flash(f'Payment screenshot uploaded! Your request for {amount} coins is pending admin approval.', 'info')
        except Exception as e:
            mysql.connection.rollback()
            # Delete uploaded file if database insert fails
            if os.path.exists(file_path):
                os.remove(file_path)
            flash(f'Failed to submit payment request: {str(e)}', 'danger')
        finally:
            cur.close()
            
    except Exception as e:
        flash(f'Failed to upload screenshot: {str(e)}', 'danger')
    
    return redirect(url_for('profile'))

@app.route('/api/user_coins')
@login_required
def get_user_coins():
    cur = mysql.connection.cursor()
    cur.execute("SELECT coins FROM users WHERE id = %s", (session['user_id'],))
    user_coins = cur.fetchone()[0]
    cur.close()
    return jsonify({'coins': user_coins})



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
    
    # Get recent processed withdrawals (approved/rejected) for tracking
    cur.execute("""
        SELECT w.id, u.username, w.amount, w.gpay_number, w.status, w.requested_at, w.processed_at
        FROM withdrawals w
        JOIN users u ON w.user_id = u.id
        WHERE w.status IN ('approved', 'rejected')
        ORDER BY w.processed_at DESC
        LIMIT 10
    """)
    processed_withdrawals = cur.fetchall()
    
    # Get financial statistics
    # 1. Total money collected from room enrollments
    cur.execute("""
        SELECT COALESCE(SUM(total_entry_fee), 0) as total_collected
        FROM room_team_enrollments 
        WHERE payment_status = 'paid'
    """)
    total_collected = cur.fetchone()[0]
    
    # 2. Total player coins across all users
    cur.execute("SELECT COALESCE(SUM(coins), 0) as total_player_coins FROM users")
    total_player_coins = cur.fetchone()[0]
    
    # 3. Withdrawal statistics
    cur.execute("""
        SELECT 
            COUNT(*) as total_requests,
            COALESCE(SUM(amount), 0) as total_amount_requested,
            COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_count,
            COALESCE(SUM(CASE WHEN status = 'pending' THEN amount END), 0) as pending_amount,
            COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved_count,
            COALESCE(SUM(CASE WHEN status = 'approved' THEN amount END), 0) as approved_amount,
            COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_count,
            COALESCE(SUM(CASE WHEN status = 'rejected' THEN amount END), 0) as rejected_amount
        FROM withdrawals
    """)
    withdrawal_stats = cur.fetchone()
    
    # 4. Room enrollment statistics
    cur.execute("""
        SELECT 
            COUNT(DISTINCT r.id) as total_rooms,
            COUNT(rte.id) as total_enrollments,
            COUNT(CASE WHEN rte.payment_status = 'paid' THEN 1 END) as paid_enrollments,
            COUNT(CASE WHEN rte.payment_status = 'pending' THEN 1 END) as pending_enrollments
        FROM rooms r
        LEFT JOIN room_team_enrollments rte ON r.id = rte.room_id
    """)
    enrollment_stats = cur.fetchone()
    
    # 5. Recent transactions summary
    cur.execute("""
        SELECT 
            COUNT(CASE WHEN type = 'credit' THEN 1 END) as total_credits,
            COALESCE(SUM(CASE WHEN type = 'credit' THEN amount END), 0) as total_credit_amount,
            COUNT(CASE WHEN type = 'debit' THEN 1 END) as total_debits,
            COALESCE(SUM(CASE WHEN type = 'debit' THEN amount END), 0) as total_debit_amount
        FROM transactions
    """)
    transaction_stats = cur.fetchone()
    
    # Compile financial data
    financial_stats = {
        'total_collected': total_collected,
        'total_player_coins': total_player_coins,
        'withdrawal_stats': {
            'total_requests': withdrawal_stats[0],
            'total_amount_requested': withdrawal_stats[1],
            'pending_count': withdrawal_stats[2],
            'pending_amount': withdrawal_stats[3],
            'approved_count': withdrawal_stats[4],
            'approved_amount': withdrawal_stats[5],
            'rejected_count': withdrawal_stats[6],
            'rejected_amount': withdrawal_stats[7]
        },
        'enrollment_stats': {
            'total_rooms': enrollment_stats[0],
            'total_enrollments': enrollment_stats[1],
            'paid_enrollments': enrollment_stats[2],
            'pending_enrollments': enrollment_stats[3]
        },
        'transaction_stats': {
            'total_credits': transaction_stats[0],
            'total_credit_amount': transaction_stats[1],
            'total_debits': transaction_stats[2],
            'total_debit_amount': transaction_stats[3]
        }
    }
    
    # 6. Top performing rooms by revenue
    cur.execute("""
        SELECT 
            r.room_name,
            r.game_type,
            COUNT(rte.id) as total_enrollments,
            COUNT(CASE WHEN rte.payment_status = 'paid' THEN 1 END) as paid_enrollments,
            COALESCE(SUM(CASE WHEN rte.payment_status = 'paid' THEN rte.total_entry_fee END), 0) as total_revenue
        FROM rooms r
        LEFT JOIN room_team_enrollments rte ON r.id = rte.room_id
        GROUP BY r.id, r.room_name, r.game_type
        HAVING total_revenue > 0
        ORDER BY total_revenue DESC
        LIMIT 5
    """)
    top_rooms = cur.fetchall()
    
    financial_stats['top_rooms'] = top_rooms
    
    # Get pending payment requests
    cur.execute("""
        SELECT t.id, u.username, t.amount, t.payment_screenshot, t.created_at
        FROM transactions t
        JOIN users u ON t.user_id = u.id
        WHERE t.type = 'credit_pending' AND t.status = 'pending'
        ORDER BY t.created_at DESC
    """)
    pending_payments = cur.fetchall()
    
    cur.close()
    
    return render_template('admin_dashboard.html', 
                         pending_withdrawals=pending_withdrawals, 
                         processed_withdrawals=processed_withdrawals, 
                         pending_payments=pending_payments,
                         financial_stats=financial_stats)

@app.route('/admin/rooms')
@admin_required
def admin_rooms():
    cur = mysql.connection.cursor()
    
    # Get rooms with consistent column order regardless of schema
    try:
        # Check what columns exist
        cur.execute("SHOW COLUMNS FROM rooms")
        columns = [col[0] for col in cur.fetchall()]
        
        # Build query based on available columns
        base_columns = ['id', 'room_name', 'game_type', 'entry_fee', 'prize_pool', 'max_players', 'room_id_game', 'room_password']
        optional_columns = []
        
        if 'event_timing' in columns:
            optional_columns.append('event_timing')
        else:
            optional_columns.append('created_at as event_timing')
            
        if 'is_multiplayer' in columns:
            optional_columns.append('is_multiplayer')
        else:
            optional_columns.append('1 as is_multiplayer')
            
        if 'min_team_size' in columns:
            optional_columns.append('min_team_size')
        else:
            optional_columns.append('1 as min_team_size')
            
        if 'max_team_size' in columns:
            optional_columns.append('max_team_size')
        else:
            optional_columns.append('4 as max_team_size')
            
        if 'status' in columns:
            optional_columns.append('status')
        else:
            optional_columns.append("'open' as status")
            
        if 'kill_rewards_enabled' in columns:
            optional_columns.append('kill_rewards_enabled')
        else:
            optional_columns.append('0 as kill_rewards_enabled')
        
        if 'is_active' in columns:
            optional_columns.append('is_active')
        else:
            optional_columns.append('1 as is_active')
        
        # Create the final query
        all_columns = base_columns + optional_columns
        query = f"SELECT {', '.join(all_columns)} FROM rooms ORDER BY created_at DESC"
        
        cur.execute(query)
        rooms = cur.fetchall()
        
    except Exception as e:
        print(f"Error in admin rooms query: {e}")
        # Ultimate fallback
        cur.execute("""
            SELECT id, room_name, game_type, entry_fee, prize_pool, max_players, 
                   room_id_game, room_password, 
                   COALESCE(created_at, NOW()) as event_timing,
                   1 as is_multiplayer, 1 as min_team_size, 4 as max_team_size,
                   'open' as status, 0 as kill_rewards_enabled, 1 as is_active
            FROM rooms ORDER BY created_at DESC
        """)
        rooms = cur.fetchall()
    
    cur.close()
    
    return render_template('admin_rooms.html', rooms=rooms)

@app.route('/admin/debug_rooms')
@admin_required
def debug_rooms():
    cur = mysql.connection.cursor()
    
    # Get table structure
    cur.execute("DESCRIBE rooms")
    columns = cur.fetchall()
    
    # Get all rooms
    cur.execute("SELECT * FROM rooms LIMIT 5")
    rooms = cur.fetchall()
    
    cur.close()
    
    debug_info = {
        'columns': columns,
        'rooms': rooms,
        'room_count': len(rooms)
    }
    
    return jsonify(debug_info)

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

@app.route('/admin/reject_withdrawal/<int:withdrawal_id>', methods=['POST'])
@admin_required
def reject_withdrawal(withdrawal_id):
    cur = mysql.connection.cursor()
    try:
        # Get withdrawal details first
        cur.execute("SELECT user_id, amount FROM withdrawals WHERE id = %s", (withdrawal_id,))
        withdrawal = cur.fetchone()
        
        if not withdrawal:
            flash('Withdrawal not found', 'danger')
            return redirect(url_for('admin_dashboard'))
        
        user_id, amount = withdrawal
        
        # Return money to user's account
        cur.execute("UPDATE users SET coins = coins + %s WHERE id = %s", (amount, user_id))
        
        # Update withdrawal status
        cur.execute("""
            UPDATE withdrawals 
            SET status = 'rejected', processed_at = NOW()
            WHERE id = %s
        """, (withdrawal_id,))
        
        # Record transaction
        cur.execute("""
            INSERT INTO transactions (user_id, type, amount, description)
            VALUES (%s, 'credit', %s, %s)
        """, (user_id, amount, f'Withdrawal rejection refund - ID: {withdrawal_id}'))
        
        mysql.connection.commit()
        flash('Withdrawal rejected and money returned to user!', 'success')
        
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error rejecting withdrawal: {str(e)}', 'danger')
    finally:
        cur.close()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/approve_payment/<int:transaction_id>', methods=['POST'])
@admin_required
def approve_payment(transaction_id):
    cur = mysql.connection.cursor()
    try:
        # Get transaction details
        cur.execute("SELECT user_id, amount FROM transactions WHERE id = %s AND type = 'credit_pending' AND status = 'pending'", (transaction_id,))
        transaction = cur.fetchone()
        
        if not transaction:
            flash('Transaction not found or already processed', 'danger')
            return redirect(url_for('admin_dashboard'))
        
        user_id, amount = transaction
        
        # Add coins to user's account
        cur.execute("UPDATE users SET coins = coins + %s WHERE id = %s", (amount, user_id))
        
        # Update transaction status
        cur.execute("UPDATE transactions SET status = 'approved', type = 'credit' WHERE id = %s", (transaction_id,))
        
        mysql.connection.commit()
        flash(f'Payment approved! {amount} coins added to user account.', 'success')
        
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error approving payment: {str(e)}', 'danger')
    finally:
        cur.close()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject_payment/<int:transaction_id>', methods=['POST'])
@admin_required
def reject_payment(transaction_id):
    cur = mysql.connection.cursor()
    try:
        # Update transaction status to rejected
        cur.execute("UPDATE transactions SET status = 'rejected' WHERE id = %s AND type = 'credit_pending' AND status = 'pending'", (transaction_id,))
        
        if cur.rowcount == 0:
            flash('Transaction not found or already processed', 'danger')
        else:
            mysql.connection.commit()
            flash('Payment rejected!', 'success')
        
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error rejecting payment: {str(e)}', 'danger')
    finally:
        cur.close()
    
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
    event_timing = request.form.get('event_timing', None)
    is_multiplayer = bool(int(request.form.get('is_multiplayer', 1)))
    min_team_size = int(request.form.get('min_team_size', 1))
    max_team_size = int(request.form.get('max_team_size', 4))
    min_players_to_start = int(request.form.get('min_players_to_start', 2))
    
    # Kill reward system
    enable_kill_rewards = 'enable_kill_rewards' in request.form
    min_kills_required = int(request.form.get('min_kills_required', 0)) if enable_kill_rewards else 0
    reward_per_kill = float(request.form.get('reward_per_kill', 0.00)) if enable_kill_rewards else 0.00
    
    # Winner reward configuration
    enable_custom_rewards = 'enable_custom_rewards' in request.form
    winner_rewards = {}
    if enable_custom_rewards:
        try:
            winner_rewards = {
                1: {  # 1st place
                    'base_reward': float(request.form.get('first_place_base_reward', 0.00)),
                    'kill_bonus': float(request.form.get('first_place_kill_bonus', 0.00)),
                    'max_kill_bonus': float(request.form.get('first_place_max_kill_bonus', 0.00))
                },
                2: {  # 2nd place
                    'base_reward': float(request.form.get('second_place_base_reward', 0.00)),
                    'kill_bonus': float(request.form.get('second_place_kill_bonus', 0.00)),
                    'max_kill_bonus': float(request.form.get('second_place_max_kill_bonus', 0.00))
                },
                3: {  # 3rd place
                    'base_reward': float(request.form.get('third_place_base_reward', 0.00)),
                    'kill_bonus': float(request.form.get('third_place_kill_bonus', 0.00)),
                    'max_kill_bonus': float(request.form.get('third_place_max_kill_bonus', 0.00))
                }
            }
        except (ValueError, TypeError):
            flash('Invalid winner reward values. Please check your input.', 'danger')
            return redirect(url_for('admin_dashboard'))
    
    # Room status and blocking
    is_active = bool(int(request.form.get('is_active', 1)))
    blocked_users_text = request.form.get('blocked_users', '').strip()
    block_reason = request.form.get('block_reason', '').strip()
    
    # Parse blocked users
    blocked_usernames = []
    if blocked_users_text:
        blocked_usernames = [username.strip() for username in blocked_users_text.split('\n') if username.strip()]
    
    # Validation
    if min_team_size > max_team_size:
        flash('Minimum team size cannot be greater than maximum team size', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    if min_players_to_start > max_players:
        flash('Minimum players to start cannot be greater than maximum players', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    if not is_multiplayer and (min_team_size > 1 or max_team_size > 1):
        flash('Single player mode should have team size of 1', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    if enable_kill_rewards and (min_kills_required < 1 or reward_per_kill <= 0):
        flash('Invalid kill reward settings', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    cur = mysql.connection.cursor()
    try:
        # Check if new columns exist in rooms table
        cur.execute("SHOW COLUMNS FROM rooms LIKE 'event_timing'")
        has_new_columns = cur.fetchone() is not None
        
        if has_new_columns:
            # Check if kill reward columns exist
            cur.execute("SHOW COLUMNS FROM rooms LIKE 'enable_kill_rewards'")
            has_kill_columns = cur.fetchone() is not None
            
            if has_kill_columns:
                # Use full new schema with kill rewards
                cur.execute("""
                    INSERT INTO rooms (room_name, game_type, entry_fee, prize_pool, max_players, 
                                     min_players_to_start, room_id_game, room_password, event_timing, 
                                     is_multiplayer, min_team_size, max_team_size, kill_rewards_enabled, 
                                     min_kills_required, reward_per_kill, is_active, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'open')
                """, (room_name, game_type, entry_fee, prize_pool, max_players, min_players_to_start,
                      room_id_game, room_password, event_timing, is_multiplayer, min_team_size, max_team_size,
                      enable_kill_rewards, min_kills_required, reward_per_kill, is_active))
            else:
                # Use schema without kill rewards
                cur.execute("""
                    INSERT INTO rooms (room_name, game_type, entry_fee, prize_pool, max_players, 
                                     min_players_to_start, room_id_game, room_password, event_timing, 
                                     is_multiplayer, min_team_size, max_team_size, is_active, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'open')
                """, (room_name, game_type, entry_fee, prize_pool, max_players, min_players_to_start,
                      room_id_game, room_password, event_timing, is_multiplayer, min_team_size, max_team_size, is_active))
        else:
            # Use old schema
            cur.execute("""
                INSERT INTO rooms (room_name, game_type, entry_fee, prize_pool, max_players, 
                                 room_id_game, room_password, is_active, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'open')
            """, (room_name, game_type, entry_fee, prize_pool, max_players, room_id_game, room_password, is_active))
        
        # Get the created room ID
        room_id = cur.lastrowid
        
        # Create winner reward settings
        if enable_custom_rewards and winner_rewards:
            # Insert custom reward settings from form
            for position, rewards in winner_rewards.items():
                cur.execute("""
                    INSERT INTO room_reward_settings 
                    (room_id, position, base_reward, kill_bonus_per_kill, max_kill_bonus)
                    VALUES (%s, %s, %s, %s, %s)
                """, (room_id, position, rewards['base_reward'], rewards['kill_bonus'], rewards['max_kill_bonus']))
        else:
            # Create default reward settings based on prize pool
            total_prize_pool = float(prize_pool) * 0.8  # 80% of prize pool for winners
            default_rewards = [
                (1, total_prize_pool * 0.50, 10.0, total_prize_pool * 0.10),   # 1st: 50% + 10/kill
                (2, total_prize_pool * 0.30, 7.5, total_prize_pool * 0.06),    # 2nd: 30% + 7.5/kill  
                (3, total_prize_pool * 0.20, 5.0, total_prize_pool * 0.04),    # 3rd: 20% + 5/kill
            ]
            
            for position, base_reward, kill_bonus, max_kill_bonus in default_rewards:
                cur.execute("""
                    INSERT INTO room_reward_settings 
                    (room_id, position, base_reward, kill_bonus_per_kill, max_kill_bonus)
                    VALUES (%s, %s, %s, %s, %s)
                """, (room_id, position, base_reward, kill_bonus, max_kill_bonus))
        
        # Handle blocked users if any were specified
        if blocked_usernames:
            blocked_count = 0
            for username in blocked_usernames:
                try:
                    # Check if user exists
                    cur.execute("SELECT id FROM users WHERE username = %s", (username,))
                    user_result = cur.fetchone()
                    
                    if user_result:
                        user_id = user_result[0]
                        # Insert blocked user (ignore if already exists due to unique constraint)
                        cur.execute("""
                            INSERT IGNORE INTO blocked_users (room_id, user_id, blocked_by, reason)
                            VALUES (%s, %s, %s, %s)
                        """, (room_id, user_id, session['user_id'], block_reason or f'Pre-blocked during room creation'))
                        blocked_count += 1
                except Exception as block_error:
                    print(f"Error blocking user {username}: {block_error}")
            
            if blocked_count > 0:
                flash(f'Room created successfully! {blocked_count} users were pre-blocked.', 'success')
            else:
                flash('Room created successfully! Note: No valid users were found to block.', 'warning')
        else:
            flash('Room created successfully!', 'success')
        
        mysql.connection.commit()
        
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Room creation failed: {str(e)}', 'danger')
        print(f"Room creation error: {e}")  # For debugging
    finally:
        cur.close()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/create_team/<int:room_id>', methods=['POST'])
@login_required
def create_team(room_id):
    team_name = request.form['team_name']
    team_email = request.form['team_email']
    member_usernames = request.form.getlist('member_username[]')
    member_pubg_ids = request.form.getlist('member_pubg_id[]')
    
    cur = mysql.connection.cursor()
    try:
        # Get room details
        cur.execute("SELECT entry_fee, min_team_size, max_team_size, is_multiplayer FROM rooms WHERE id = %s", (room_id,))
        room = cur.fetchone()
        
        if not room:
            flash('Room not found', 'danger')
            return redirect(url_for('home'))
        
        entry_fee, min_team_size, max_team_size, is_multiplayer = room
        
        # Validate team size
        team_size = len([u for u in member_usernames if u.strip()])
        if team_size < min_team_size or team_size > max_team_size:
            flash(f'Team size must be between {min_team_size} and {max_team_size} players', 'danger')
            return redirect(url_for('room_details', room_id=room_id))
        
        # Check if any member is already enrolled in this room
        for username in member_usernames:
            if username.strip():
                cur.execute("""
                    SELECT COUNT(*) FROM team_members tm
                    JOIN teams t ON tm.team_id = t.id
                    JOIN users u ON tm.user_id = u.id
                    WHERE t.room_id = %s AND u.username = %s
                """, (room_id, username.strip()))
                
                if cur.fetchone()[0] > 0:
                    flash(f'Player {username} is already enrolled in this room', 'danger')
                    return redirect(url_for('room_details', room_id=room_id))
        
        # Calculate total entry fee
        total_entry_fee = entry_fee * team_size
        
        # Check if team leader has enough coins
        cur.execute("SELECT coins FROM users WHERE id = %s", (session['user_id'],))
        user_coins = cur.fetchone()[0]
        
        if user_coins < total_entry_fee:
            flash('Insufficient coins to pay for the entire team!', 'danger')
            return redirect(url_for('room_details', room_id=room_id))
        
        # Create team
        cur.execute("""
            INSERT INTO teams (room_id, team_name, team_email, team_leader_id, total_entry_fee, payment_status)
            VALUES (%s, %s, %s, %s, %s, 'paid')
        """, (room_id, team_name, team_email, session['user_id'], total_entry_fee))
        
        team_id = cur.lastrowid
        
        # Deduct coins from team leader
        cur.execute("UPDATE users SET coins = coins - %s WHERE id = %s", (total_entry_fee, session['user_id']))
        
        # Add team members
        for i, username in enumerate(member_usernames):
            if username.strip():
                # Get user ID
                cur.execute("SELECT id FROM users WHERE username = %s", (username.strip(),))
                user_result = cur.fetchone()
                
                if not user_result:
                    raise Exception(f'User {username} not found')
                
                user_id = user_result[0]
                
                # Get PUBG username ID
                pubg_username = member_pubg_ids[i].strip() if i < len(member_pubg_ids) else ''
                if pubg_username:
                    cur.execute("SELECT id FROM pubg_usernames WHERE user_id = %s AND pubg_username = %s", 
                               (user_id, pubg_username))
                    pubg_result = cur.fetchone()
                    
                    if not pubg_result:
                        raise Exception(f'PUBG username {pubg_username} not found for user {username}')
                    
                    pubg_username_id = pubg_result[0]
                else:
                    # Get first PUBG username for the user
                    cur.execute("SELECT id FROM pubg_usernames WHERE user_id = %s LIMIT 1", (user_id,))
                    pubg_result = cur.fetchone()
                    
                    if not pubg_result:
                        raise Exception(f'No PUBG username found for user {username}')
                    
                    pubg_username_id = pubg_result[0]
                
                # Add team member
                cur.execute("""
                    INSERT INTO team_members (team_id, user_id, pubg_username_id)
                    VALUES (%s, %s, %s)
                """, (team_id, user_id, pubg_username_id))
        
        mysql.connection.commit()
        flash('Team created and enrolled successfully!', 'success')
        return redirect(url_for('room_enrollments', room_id=room_id))
        
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Team creation failed: {str(e)}', 'danger')
        return redirect(url_for('room_details', room_id=room_id))
    finally:
        cur.close()

@app.route('/admin/room/<int:room_id>/kills')
@admin_required
def manage_kills(room_id):
    cur = mysql.connection.cursor()
    
    # Get room details
    cur.execute("SELECT * FROM rooms WHERE id = %s", (room_id,))
    room = cur.fetchone()
    
    if not room:
        flash('Room not found', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    # Get all players in this room from gaming ID enrollment system only
    cur.execute("""
        SELECT rue.user_id, u.username, ugi.gaming_username, 
               ugi.display_name as team_name,
               COALESCE(girs.kills_count, 0) as kills_count,
               COALESCE(girs.reward_earned, 0) as reward_earned,
               COALESCE(girs.reward_status, 'pending') as reward_status,
               girs.id as kill_record_id,
               ugi.id as gaming_id
        FROM room_user_enrollments rue
        JOIN users u ON rue.user_id = u.id
        JOIN room_gaming_ids rgi ON rue.id = rgi.room_user_enrollment_id
        JOIN user_gaming_ids ugi ON rgi.user_gaming_id = ugi.id
        LEFT JOIN gaming_id_room_stats girs ON girs.user_gaming_id = ugi.id AND girs.room_id = %s
        WHERE rue.room_id = %s AND rue.payment_status = 'paid'
        ORDER BY u.username, ugi.gaming_username
    """, (room_id, room_id))
    players = cur.fetchall()
    
    cur.close()
    
    return render_template('admin_kills.html', room=room, players=players)

@app.route('/admin/record_kills/<int:room_id>', methods=['POST'])
@admin_required
def record_kills(room_id):
    user_id = int(request.form['user_id'])
    kills_count = int(request.form['kills_count'])
    gaming_id = request.form.get('gaming_id')
    screenshot = request.files.get('screenshot')
    
    if not gaming_id:
        flash('Gaming ID required for kill recording', 'danger')
        return redirect(url_for('manage_kills', room_id=room_id))
    
    cur = mysql.connection.cursor()
    try:
        # Get room kill reward settings
        cur.execute("""
            SELECT enable_kill_rewards, min_kills_required, reward_per_kill 
            FROM rooms WHERE id = %s
        """, (room_id,))
        room_settings = cur.fetchone()
        
        if not room_settings:
            flash('Room not found', 'danger')
            return redirect(url_for('admin_dashboard'))
        
        enable_kill_rewards, min_kills_required, reward_per_kill = room_settings
        
        # Calculate reward
        reward_earned = 0.00
        if enable_kill_rewards and kills_count >= min_kills_required:
            eligible_kills = kills_count - min_kills_required + 1  # Include the minimum kill
            reward_earned = eligible_kills * float(reward_per_kill)
        
        # Handle screenshot upload
        screenshot_filename = None
        if screenshot:
            screenshot_filename = secure_filename(f"kills_{room_id}_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png")
            screenshot_path = os.path.join(app.config['UPLOAD_FOLDER'], screenshot_filename)
            screenshot.save(screenshot_path)
        
        # Update gaming_id_room_stats for gaming ID system
        cur.execute("""
            INSERT INTO gaming_id_room_stats (user_gaming_id, room_id, kills_count, reward_earned, 
                                            reward_status, screenshot_proof, recorded_by)
            VALUES (%s, %s, %s, %s, 'approved', %s, %s)
            ON DUPLICATE KEY UPDATE
            kills_count = %s, reward_earned = %s, screenshot_proof = %s, 
            recorded_by = %s, recorded_at = NOW()
        """, (gaming_id, room_id, kills_count, reward_earned, screenshot_filename, 
              session['user_id'], kills_count, reward_earned, screenshot_filename, session['user_id']))
        
        # Add reward to user's coins if applicable
        if reward_earned > 0:
            cur.execute("UPDATE users SET coins = coins + %s WHERE id = %s", (int(reward_earned), user_id))
            
            # Record transaction
            cur.execute("""
                INSERT INTO transactions (user_id, type, amount, payment_id)
                VALUES (%s, 'kill_reward', %s, %s)
            """, (user_id, int(reward_earned), f"room_{room_id}_gaming_id_kills_{kills_count}"))
        
        mysql.connection.commit()
        flash(f'Kill record updated! Reward: {reward_earned} Rs', 'success')
        
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Failed to record kills: {str(e)}', 'danger')
    finally:
        cur.close()
    
    return redirect(url_for('manage_kills', room_id=room_id))

@app.route('/enroll_team/<int:room_id>', methods=['POST'])
@login_required
def enroll_team(room_id):
    user_team_id = int(request.form['user_team_id'])
    
    cur = mysql.connection.cursor()
    try:
        # Verify team ownership
        cur.execute("SELECT * FROM user_teams WHERE id = %s AND user_id = %s AND is_active = TRUE", 
                   (user_team_id, session['user_id']))
        team = cur.fetchone()
        
        if not team:
            flash('Team not found or inactive', 'danger')
            return redirect(url_for('room_details', room_id=room_id))
        
        # Get room details including max_players and activity status
        cur.execute("SELECT entry_fee, min_team_size, max_team_size, max_players, is_active FROM rooms WHERE id = %s", (room_id,))
        room_info = cur.fetchone()
        
        if not room_info:
            flash('Room not found', 'danger')
            return redirect(url_for('home'))
        
        entry_fee, min_team_size, max_team_size, max_players, is_active = room_info
        
        # Check if room is active
        if not is_active:
            flash('This room is currently disabled by admin', 'danger')
            return redirect(url_for('room_details', room_id=room_id))
        
        # Check if user is blocked from this room
        cur.execute("SELECT id FROM blocked_users WHERE room_id = %s AND user_id = %s", (room_id, session['user_id']))
        if cur.fetchone():
            flash('You have been blocked from joining this room', 'danger')
            return redirect(url_for('room_details', room_id=room_id))
        
        # Check if team is blocked from this room
        cur.execute("SELECT id FROM blocked_teams WHERE room_id = %s AND team_id = %s", (room_id, user_team_id))
        if cur.fetchone():
            flash('This team has been blocked from joining this room', 'danger')
            return redirect(url_for('room_details', room_id=room_id))
        
        # Get team size from user_teams table (more reliable)
        cur.execute("SELECT team_size FROM user_teams WHERE id = %s", (user_team_id,))
        team_size_result = cur.fetchone()
        
        if not team_size_result:
            flash('Team data not found', 'danger')
            return redirect(url_for('room_details', room_id=room_id))
            
        team_size = team_size_result[0]
        
        # Validate team size
        if team_size < min_team_size or team_size > max_team_size:
            flash(f'Team size must be between {min_team_size} and {max_team_size} players', 'danger')
            return redirect(url_for('room_details', room_id=room_id))
        
        # Calculate current enrolled players in the room (using paid teams only)
        cur.execute("""
            SELECT COALESCE(SUM(ut.team_size), 0) as total_players
            FROM room_team_enrollments rte
            JOIN user_teams ut ON rte.user_team_id = ut.id
            WHERE rte.room_id = %s AND rte.payment_status = 'paid'
        """, (room_id,))
        current_total_players = cur.fetchone()[0]
        
        # Check if adding this team would exceed max players
        print(f"=== TEAM ENROLLMENT VALIDATION ===")
        print(f"Room ID: {room_id}")
        print(f"Room Max Players: {max_players}")
        print(f"Current Total Players: {current_total_players}")
        print(f"Team Size to Add: {team_size}")
        print(f"Total After Adding: {current_total_players + team_size}")
        print("===============================")
        
        if current_total_players + team_size > max_players:
            remaining_slots = max_players - current_total_players
            if remaining_slots <= 0:
                flash('Room is full! No more players can be enrolled.', 'danger')
            else:
                flash(f'Cannot enroll team! Only {remaining_slots} player slots remaining, but your team has {team_size} players.', 'danger')
            return redirect(url_for('room_details', room_id=room_id))
        
        # Calculate total entry fee
        total_entry_fee = entry_fee * team_size
        
        # Check if user has enough coins
        cur.execute("SELECT coins FROM users WHERE id = %s", (session['user_id'],))
        user_coins = cur.fetchone()[0]
        
        if user_coins < total_entry_fee:
            flash('Insufficient coins to enroll this team!', 'danger')
            return redirect(url_for('room_details', room_id=room_id))
        
        # Check if team already enrolled
        cur.execute("SELECT id FROM room_team_enrollments WHERE room_id = %s AND user_team_id = %s", 
                   (room_id, user_team_id))
        if cur.fetchone():
            flash('This team is already enrolled in this room', 'warning')
            return redirect(url_for('room_details', room_id=room_id))
        
        # Deduct coins and enroll team
        cur.execute("UPDATE users SET coins = coins - %s WHERE id = %s", (total_entry_fee, session['user_id']))
        
        cur.execute("""
            INSERT INTO room_team_enrollments (room_id, user_team_id, enrolled_by, total_entry_fee, payment_status)
            VALUES (%s, %s, %s, %s, 'paid')
        """, (room_id, user_team_id, session['user_id'], total_entry_fee))
        
        mysql.connection.commit()
        flash('Team enrolled successfully!', 'success')
        return redirect(url_for('room_enrollments', room_id=room_id))
        
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Enrollment failed: {str(e)}', 'danger')
        return redirect(url_for('room_details', room_id=room_id))
    finally:
        cur.close()

# API Routes
@app.route('/api/user_coins')
@login_required
def api_user_coins():
    cur = mysql.connection.cursor()
    try:
        cur.execute("SELECT coins FROM users WHERE id = %s", (session['user_id'],))
        coins = cur.fetchone()[0]
        return jsonify({'coins': coins})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()

@app.route('/api/room/<int:room_id>/teams')
@admin_required
def api_room_teams(room_id):
    cur = mysql.connection.cursor()
    try:
        # Get all active teams (not just enrolled ones) - admins might want to pre-block teams
        cur.execute("""
            SELECT ut.id, ut.team_name, u.username as leader_name, 
                   CASE WHEN rte.id IS NOT NULL THEN 1 ELSE 0 END as is_enrolled
            FROM user_teams ut
            JOIN users u ON ut.user_id = u.id
            LEFT JOIN room_team_enrollments rte ON ut.id = rte.user_team_id AND rte.room_id = %s
            WHERE ut.is_active = 1
            ORDER BY is_enrolled DESC, ut.team_name
        """, (room_id,))
        
        teams = []
        for team in cur.fetchall():
            teams.append({
                'id': team[0],
                'name': team[1],
                'leader': team[2],
                'is_enrolled': bool(team[3])
            })
        
        return jsonify({'teams': teams})
    except Exception as e:
        print(f"API teams error: {e}")  # Debug logging
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()

@app.route('/api/users/suggestions')
@admin_required
def api_user_suggestions():
    cur = mysql.connection.cursor()
    try:
        # Get all usernames for auto-suggestions
        cur.execute("SELECT username FROM users ORDER BY username")
        usernames = [row[0] for row in cur.fetchall()]
        return jsonify({'usernames': usernames})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()

@app.route('/api/room/<int:room_id>/blocked_users')
@admin_required
def api_room_blocked_users(room_id):
    cur = mysql.connection.cursor()
    try:
        # Get blocked users for this room
        cur.execute("""
            SELECT u.username, bu.reason, bu.blocked_at
            FROM blocked_users bu
            JOIN users u ON bu.user_id = u.id
            WHERE bu.room_id = %s
            ORDER BY bu.blocked_at DESC
        """, (room_id,))
        
        blocked_users = []
        for user in cur.fetchall():
            blocked_users.append({
                'username': user[0],
                'reason': user[1] or 'No reason provided',
                'blocked_at': user[2].strftime('%Y-%m-%d %H:%M') if user[2] else 'Unknown'
            })
        
        # Get blocked teams for this room
        cur.execute("""
            SELECT ut.team_name, bt.reason, bt.blocked_at
            FROM blocked_teams bt
            JOIN user_teams ut ON bt.team_id = ut.id
            WHERE bt.room_id = %s
            ORDER BY bt.blocked_at DESC
        """, (room_id,))
        
        blocked_teams = []
        for team in cur.fetchall():
            blocked_teams.append({
                'team_name': team[0],
                'reason': team[1] or 'No reason provided',
                'blocked_at': team[2].strftime('%Y-%m-%d %H:%M') if team[2] else 'Unknown'
            })
        
        return jsonify({
            'blocked_users': blocked_users,
            'blocked_teams': blocked_teams
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()

# Room Controls Routes
@app.route('/admin/toggle_room/<int:room_id>', methods=['POST'])
@admin_required
def toggle_room(room_id):
    cur = mysql.connection.cursor()
    try:
        # Get current status
        cur.execute("SELECT is_active, room_name FROM rooms WHERE id = %s", (room_id,))
        room = cur.fetchone()
        
        if not room:
            flash('Room not found', 'danger')
            return redirect(url_for('admin_dashboard'))
        
        current_status, room_name = room
        new_status = 0 if current_status else 1
        status_text = "enabled" if new_status else "disabled"
        
        # Update room status
        cur.execute("UPDATE rooms SET is_active = %s WHERE id = %s", (new_status, room_id))
        mysql.connection.commit()
        
        flash(f'Room "{room_name}" has been {status_text}', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Failed to toggle room status: {str(e)}', 'danger')
    finally:
        cur.close()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/block_user', methods=['POST'])
@admin_required
def block_user():
    room_id = request.form.get('room_id')
    username = request.form.get('username')
    reason = request.form.get('reason', '')
    
    cur = mysql.connection.cursor()
    try:
        # Get user ID from username
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        user_result = cur.fetchone()
        
        if not user_result:
            flash('User not found', 'danger')
            return redirect(url_for('admin_dashboard'))
        
        user_id = user_result[0]
        
        # Check if user is already blocked
        cur.execute("SELECT id FROM blocked_users WHERE room_id = %s AND user_id = %s", (room_id, user_id))
        if cur.fetchone():
            flash('User is already blocked from this room', 'warning')
            return redirect(url_for('admin_dashboard'))
        
        # Block the user
        cur.execute("""
            INSERT INTO blocked_users (room_id, user_id, blocked_by, reason)
            VALUES (%s, %s, %s, %s)
        """, (room_id, user_id, session['user_id'], reason))
        
        mysql.connection.commit()
        flash(f'User "{username}" has been blocked from the room', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Failed to block user: {str(e)}', 'danger')
    finally:
        cur.close()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/unblock_user', methods=['POST'])
@admin_required
def unblock_user():
    room_id = request.form.get('room_id')
    username = request.form.get('username')
    
    cur = mysql.connection.cursor()
    try:
        # Get user ID from username
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        user_result = cur.fetchone()
        
        if not user_result:
            flash('User not found', 'danger')
            return redirect(url_for('admin_dashboard'))
        
        user_id = user_result[0]
        
        # Unblock the user
        cur.execute("DELETE FROM blocked_users WHERE room_id = %s AND user_id = %s", (room_id, user_id))
        mysql.connection.commit()
        
        flash(f'User "{username}" has been unblocked from the room', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Failed to unblock user: {str(e)}', 'danger')
    finally:
        cur.close()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/block_team', methods=['POST'])
@admin_required
def block_team():
    room_id = request.form.get('room_id')
    team_id = request.form.get('team_id')
    reason = request.form.get('reason', '')
    
    cur = mysql.connection.cursor()
    try:
        # Check if team exists and get team name
        cur.execute("SELECT team_name FROM user_teams WHERE id = %s", (team_id,))
        team_result = cur.fetchone()
        
        if not team_result:
            flash('Team not found', 'danger')
            return redirect(url_for('admin_dashboard'))
        
        team_name = team_result[0]
        
        # Check if team is already blocked
        cur.execute("SELECT id FROM blocked_teams WHERE room_id = %s AND team_id = %s", (room_id, team_id))
        if cur.fetchone():
            flash('Team is already blocked from this room', 'warning')
            return redirect(url_for('admin_dashboard'))
        
        # Block the team
        cur.execute("""
            INSERT INTO blocked_teams (room_id, team_id, blocked_by, reason)
            VALUES (%s, %s, %s, %s)
        """, (room_id, team_id, session['user_id'], reason))
        
        mysql.connection.commit()
        flash(f'Team "{team_name}" has been blocked from the room', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Failed to block team: {str(e)}', 'danger')
    finally:
        cur.close()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/unblock_team', methods=['POST'])
@admin_required
def unblock_team():
    room_id = request.form.get('room_id')
    team_id = request.form.get('team_id')
    
    cur = mysql.connection.cursor()
    try:
        # Get team name
        cur.execute("SELECT team_name FROM user_teams WHERE id = %s", (team_id,))
        team_result = cur.fetchone()
        
        if not team_result:
            flash('Team not found', 'danger')
            return redirect(url_for('admin_dashboard'))
        
        team_name = team_result[0]
        
        # Unblock the team
        cur.execute("DELETE FROM blocked_teams WHERE room_id = %s AND team_id = %s", (room_id, team_id))
        mysql.connection.commit()
        
        flash(f'Team "{team_name}" has been unblocked from the room', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Failed to unblock team: {str(e)}', 'danger')
    finally:
        cur.close()
    
    return redirect(url_for('admin_dashboard'))

# Gaming IDs Management Routes
@app.route('/my_gaming_ids')
@login_required
def my_gaming_ids():
    """Display user's gaming IDs management page"""
    cur = mysql.connection.cursor()
    try:
        # Get user's gaming IDs
        cur.execute("""
            SELECT g.id, g.gaming_platform, g.gaming_username, g.display_name, 
                   g.is_primary, g.is_active, g.created_at,
                   COALESCE(s.total_rooms_joined, 0) as rooms_joined,
                   COALESCE(s.total_kills, 0) as total_kills,
                   COALESCE(s.total_rewards_earned, 0) as rewards_earned
            FROM user_gaming_ids g
            LEFT JOIN user_gaming_id_stats s ON g.id = s.user_gaming_id
            WHERE g.user_id = %s
            ORDER BY g.is_primary DESC, g.created_at DESC
        """, (session['user_id'],))
        gaming_ids = cur.fetchall()
        
        return render_template('my_gaming_ids.html', gaming_ids=gaming_ids)
        
    except Exception as e:
        flash(f'Error loading gaming IDs: {str(e)}', 'danger')
        return redirect(url_for('home'))
    finally:
        cur.close()

@app.route('/add_gaming_id', methods=['GET', 'POST'])
@login_required
def add_gaming_id():
    """Add new gaming ID"""
    if request.method == 'POST':
        gaming_platform = request.form.get('gaming_platform', 'PUBG')
        gaming_username = request.form['gaming_username'].strip()
        display_name = request.form.get('display_name', gaming_username).strip()
        is_primary = request.form.get('is_primary') == 'on'
        
        if not gaming_username:
            flash('Gaming username is required', 'danger')
            return render_template('add_gaming_id.html')
        
        cur = mysql.connection.cursor()
        try:
            # Check if gaming username already exists for this user
            cur.execute("""
                SELECT id FROM user_gaming_ids 
                WHERE user_id = %s AND gaming_username = %s AND gaming_platform = %s
            """, (session['user_id'], gaming_username, gaming_platform))
            
            if cur.fetchone():
                flash(f'{gaming_platform} username "{gaming_username}" already exists in your account', 'warning')
                return render_template('add_gaming_id.html')
            
            # If setting as primary, remove primary from other IDs
            if is_primary:
                cur.execute("""
                    UPDATE user_gaming_ids 
                    SET is_primary = FALSE 
                    WHERE user_id = %s
                """, (session['user_id'],))
            
            # Insert new gaming ID
            cur.execute("""
                INSERT INTO user_gaming_ids (user_id, gaming_platform, gaming_username, display_name, is_primary)
                VALUES (%s, %s, %s, %s, %s)
            """, (session['user_id'], gaming_platform, gaming_username, display_name, is_primary))
            
            # Create stats record
            gaming_id = cur.lastrowid
            cur.execute("""
                INSERT INTO user_gaming_id_stats (user_gaming_id)
                VALUES (%s)
            """, (gaming_id,))
            
            mysql.connection.commit()
            flash(f'Gaming ID "{display_name}" added successfully!', 'success')
            return redirect(url_for('my_gaming_ids'))
            
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error adding gaming ID: {str(e)}', 'danger')
        finally:
            cur.close()
    
    return render_template('add_gaming_id.html')

@app.route('/edit_gaming_id/<int:gaming_id>', methods=['GET', 'POST'])
@login_required
def edit_gaming_id(gaming_id):
    """Edit gaming ID"""
    cur = mysql.connection.cursor()
    
    # Verify ownership
    cur.execute("""
        SELECT * FROM user_gaming_ids 
        WHERE id = %s AND user_id = %s
    """, (gaming_id, session['user_id']))
    gaming_id_data = cur.fetchone()
    
    if not gaming_id_data:
        flash('Gaming ID not found or access denied', 'danger')
        return redirect(url_for('my_gaming_ids'))
    
    if request.method == 'POST':
        gaming_platform = request.form.get('gaming_platform', 'PUBG')
        gaming_username = request.form['gaming_username'].strip()
        display_name = request.form.get('display_name', gaming_username).strip()
        is_primary = request.form.get('is_primary') == 'on'
        is_active = request.form.get('is_active') == 'on'
        
        try:
            # If setting as primary, remove primary from other IDs
            if is_primary:
                cur.execute("""
                    UPDATE user_gaming_ids 
                    SET is_primary = FALSE 
                    WHERE user_id = %s AND id != %s
                """, (session['user_id'], gaming_id))
            
            # Update gaming ID
            cur.execute("""
                UPDATE user_gaming_ids 
                SET gaming_platform = %s, gaming_username = %s, display_name = %s, 
                    is_primary = %s, is_active = %s, updated_at = NOW()
                WHERE id = %s
            """, (gaming_platform, gaming_username, display_name, is_primary, is_active, gaming_id))
            
            mysql.connection.commit()
            flash('Gaming ID updated successfully!', 'success')
            return redirect(url_for('my_gaming_ids'))
            
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error updating gaming ID: {str(e)}', 'danger')
        finally:
            cur.close()
    
    return render_template('edit_gaming_id.html', gaming_id_data=gaming_id_data)

@app.route('/set_primary_gaming_id/<int:gaming_id>', methods=['POST'])
@login_required
def set_primary_gaming_id(gaming_id):
    """Set gaming ID as primary"""
    cur = mysql.connection.cursor()
    try:
        # Verify ownership
        cur.execute("""
            SELECT id FROM user_gaming_ids 
            WHERE id = %s AND user_id = %s
        """, (gaming_id, session['user_id']))
        
        if not cur.fetchone():
            return jsonify({'success': False, 'message': 'Gaming ID not found'})
        
        # Remove primary from all other IDs
        cur.execute("""
            UPDATE user_gaming_ids 
            SET is_primary = FALSE 
            WHERE user_id = %s
        """, (session['user_id'],))
        
        # Set new primary
        cur.execute("""
            UPDATE user_gaming_ids 
            SET is_primary = TRUE 
            WHERE id = %s
        """, (gaming_id,))
        
        mysql.connection.commit()
        return jsonify({'success': True, 'message': 'Primary gaming ID updated'})
        
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cur.close()

@app.route('/room/<int:room_id>/join_with_gaming_ids', methods=['GET', 'POST'])
@login_required
def join_room_with_gaming_ids(room_id):
    """New room joining logic with gaming ID selection"""
    cur = mysql.connection.cursor()
    
    try:
        # Get room details
        cur.execute("SELECT * FROM rooms WHERE id = %s", (room_id,))
        room = cur.fetchone()
        
        if not room:
            flash('Room not found', 'danger')
            return redirect(url_for('home'))
        
        room_active = room[20] if len(room) > 20 and room[20] is not None else 1
        if not room_active:
            flash('This room is currently disabled by admin', 'danger')
            return redirect(url_for('room_details', room_id=room_id))
        
        # Check if user is blocked
        cur.execute("SELECT id FROM blocked_users WHERE room_id = %s AND user_id = %s", (room_id, session['user_id']))
        if cur.fetchone():
            flash('You have been blocked from joining this room', 'danger')
            return redirect(url_for('room_details', room_id=room_id))
        
        # Check if already enrolled
        cur.execute("""
            SELECT id FROM room_user_enrollments 
            WHERE room_id = %s AND user_id = %s AND is_active = TRUE
        """, (room_id, session['user_id']))
        if cur.fetchone():
            flash('You are already enrolled in this room', 'warning')
            return redirect(url_for('room_details', room_id=room_id))
        
        # Get user's gaming IDs
        cur.execute("""
            SELECT id, gaming_platform, gaming_username, display_name, is_primary
            FROM user_gaming_ids
            WHERE user_id = %s AND is_active = TRUE
            ORDER BY is_primary DESC, gaming_platform, display_name
        """, (session['user_id'],))
        user_gaming_ids = cur.fetchall()
        
        if not user_gaming_ids:
            flash('You need to add at least one gaming ID before joining tournaments', 'warning')
            return redirect(url_for('add_gaming_id'))
        
        # Calculate current players in room
        cur.execute("""
            SELECT COALESCE(SUM(gaming_ids_count), 0) as total_players
            FROM room_user_enrollments
            WHERE room_id = %s AND payment_status = 'paid' AND is_active = TRUE
        """, (room_id,))
        current_players = cur.fetchone()[0]
        available_slots = room[5] - current_players  # room[5] = max_players
        
        if request.method == 'POST':
            selected_gaming_ids = request.form.getlist('selected_gaming_ids')
            
            if not selected_gaming_ids:
                flash('Please select at least one gaming ID', 'danger')
                return render_template('join_room_gaming_ids.html', 
                                     room=room, user_gaming_ids=user_gaming_ids,
                                     current_players=current_players, available_slots=available_slots)
            
            # Validate selections - use max_team_size as the limit for gaming IDs per user
            max_team_size = room[12] if len(room) > 12 and room[12] else 4  # room[12] = max_team_size
            if len(selected_gaming_ids) > max_team_size:
                flash(f'You can only select up to {max_team_size} gaming IDs for this room (team size limit)', 'danger')
                return render_template('join_room_gaming_ids.html', 
                                     room=room, user_gaming_ids=user_gaming_ids,
                                     current_players=current_players, available_slots=available_slots)
            
            # Check available slots
            if len(selected_gaming_ids) > available_slots:
                flash(f'Not enough slots available. You selected {len(selected_gaming_ids)} IDs but only {available_slots} slots remain', 'danger')
                return render_template('join_room_gaming_ids.html', 
                                     room=room, user_gaming_ids=user_gaming_ids,
                                     current_players=current_players, available_slots=available_slots)
            
            # ROOM-LEVEL GAMING ID DUPLICATE PREVENTION
            if selected_gaming_ids:
                # Validation 1: Check if any of the selected gaming IDs are already enrolled in this room
                gaming_ids_placeholders = ','.join(['%s'] * len(selected_gaming_ids))
                cur.execute(f"""
                    SELECT ug.gaming_username, ug.gaming_platform, u.username, u.id as enrolled_by_user_id
                    FROM room_gaming_ids rgi
                    JOIN room_user_enrollments rue ON rgi.room_user_enrollment_id = rue.id
                    JOIN user_gaming_ids ug ON rgi.user_gaming_id = ug.id
                    JOIN users u ON rue.user_id = u.id
                    WHERE rue.room_id = %s 
                    AND rue.is_active = TRUE 
                    AND rgi.user_gaming_id IN ({gaming_ids_placeholders})
                """, [room_id] + [int(gid) for gid in selected_gaming_ids])
                
                already_enrolled = cur.fetchall()
                if already_enrolled:
                    enrolled_details = []
                    for enrolled in already_enrolled:
                        if enrolled[3] == session['user_id']:
                            enrolled_details.append(f"{enrolled[0]} ({enrolled[1]}) - already enrolled by you")
                        else:
                            enrolled_details.append(f"{enrolled[0]} ({enrolled[1]}) - already enrolled by {enrolled[2]}")
                    
                    flash(f'⚠️ Gaming ID(s) already enrolled in this room: {", ".join(enrolled_details)}', 'danger')
                    return render_template('join_room_gaming_ids.html', 
                                         room=room, user_gaming_ids=user_gaming_ids,
                                         current_players=current_players, available_slots=available_slots)
                
                # Validation 2: Check for duplicate gaming usernames in this room (room-level uniqueness)
                # This prevents the same gaming username from being enrolled by different users in the same room
                selected_gaming_ids_int = [int(gid) for gid in selected_gaming_ids]
                gaming_ids_placeholders = ','.join(['%s'] * len(selected_gaming_ids_int))
                
                # Get the gaming usernames and platforms for selected IDs
                cur.execute(f"""
                    SELECT gaming_username, gaming_platform 
                    FROM user_gaming_ids 
                    WHERE id IN ({gaming_ids_placeholders})
                """, selected_gaming_ids_int)
                selected_gaming_info = cur.fetchall()
                
                # Check if any of these gaming username+platform combinations are already in this room
                conflicts = []
                for gaming_username, gaming_platform in selected_gaming_info:
                    cur.execute("""
                        SELECT u.username, ug.gaming_username, ug.gaming_platform
                        FROM room_gaming_ids rgi
                        JOIN room_user_enrollments rue ON rgi.room_user_enrollment_id = rue.id
                        JOIN user_gaming_ids ug ON rgi.user_gaming_id = ug.id
                        JOIN users u ON rue.user_id = u.id
                        WHERE rue.room_id = %s 
                        AND rue.is_active = TRUE
                        AND ug.gaming_username = %s 
                        AND ug.gaming_platform = %s
                        AND rue.user_id != %s
                    """, (room_id, gaming_username, gaming_platform, session['user_id']))
                    
                    conflict = cur.fetchone()
                    if conflict:
                        conflicts.append(f"{conflict[1]} ({conflict[2]}) - already used by {conflict[0]} in this room")
                
                if conflicts:
                    flash(f'⚠️ Gaming username conflicts in this room: {", ".join(conflicts)}. The same gaming username cannot be used by multiple users in the same room.', 'danger')
                    return render_template('join_room_gaming_ids.html', 
                                         room=room, user_gaming_ids=user_gaming_ids,
                                         current_players=current_players, available_slots=available_slots)
            
            # Calculate entry fee
            entry_fee = room[3]  # room[3] = entry_fee
            total_entry_fee = entry_fee * len(selected_gaming_ids)
            
            # Check user coins
            cur.execute("SELECT coins FROM users WHERE id = %s", (session['user_id'],))
            user_coins = cur.fetchone()[0]
            
            if user_coins < total_entry_fee:
                flash('Insufficient coins to join this room', 'danger')
                return render_template('join_room_gaming_ids.html', 
                                     room=room, user_gaming_ids=user_gaming_ids,
                                     current_players=current_players, available_slots=available_slots)
            
            # Process enrollment
            try:
                # Deduct coins
                cur.execute("""
                    UPDATE users SET coins = coins - %s WHERE id = %s
                """, (total_entry_fee, session['user_id']))
                
                # Create enrollment
                cur.execute("""
                    INSERT INTO room_user_enrollments 
                    (room_id, user_id, total_entry_fee, gaming_ids_count, payment_status)
                    VALUES (%s, %s, %s, %s, 'paid')
                """, (room_id, session['user_id'], total_entry_fee, len(selected_gaming_ids)))
                
                enrollment_id = cur.lastrowid
                
                # Add selected gaming IDs
                for gaming_id in selected_gaming_ids:
                    cur.execute("""
                        INSERT INTO room_gaming_ids (room_user_enrollment_id, user_gaming_id)
                        VALUES (%s, %s)
                    """, (enrollment_id, int(gaming_id)))
                
                # Update gaming ID stats
                for gaming_id in selected_gaming_ids:
                    cur.execute("""
                        UPDATE user_gaming_id_stats 
                        SET total_rooms_joined = total_rooms_joined + 1
                        WHERE user_gaming_id = %s
                    """, (int(gaming_id),))
                
                mysql.connection.commit()
                flash(f'Successfully joined the tournament with {len(selected_gaming_ids)} gaming IDs!', 'success')
                return redirect(url_for('room_details', room_id=room_id))
                
            except Exception as e:
                mysql.connection.rollback()
                flash(f'Error joining room: {str(e)}', 'danger')
        
        return render_template('join_room_gaming_ids.html', 
                             room=room, user_gaming_ids=user_gaming_ids,
                             current_players=current_players, available_slots=available_slots)
    
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('room_details', room_id=room_id))
    finally:
        cur.close()

# =============================================================================
# WINNER SELECTION AND PERFORMANCE REWARD ROUTES
# =============================================================================

@app.route('/admin/winners')
@admin_required
def manage_winners():
    """Admin interface to view and manage winners for all rooms"""
    cur = mysql.connection.cursor()
    try:
        # Get all rooms with their winner status
        cur.execute("""
            SELECT r.id, r.room_name, r.entry_fee, r.max_players,
                   COUNT(DISTINCT rgi.user_gaming_id) as enrolled_players,
                   COUNT(DISTINCT rw.id) as selected_winners,
                   CASE 
                       WHEN COUNT(DISTINCT rw.id) > 0 THEN 'selected'
                       ELSE 'pending'
                   END as winner_status
            FROM rooms r
            LEFT JOIN room_user_enrollments rue ON r.id = rue.room_id AND rue.payment_status = 'paid'
            LEFT JOIN room_gaming_ids rgi ON rue.id = rgi.room_user_enrollment_id
            LEFT JOIN room_winners rw ON r.id = rw.room_id
            GROUP BY r.id, r.room_name, r.entry_fee, r.max_players
            ORDER BY r.id DESC
        """)
        rooms = cur.fetchall()
        
        return render_template('admin_winners.html', rooms=rooms)
    
    except Exception as e:
        flash(f'Error loading winner management: {str(e)}', 'danger')
        return redirect(url_for('admin_dashboard'))
    finally:
        cur.close()

@app.route('/admin/winners/room/<int:room_id>')
@admin_required
def room_winner_selection(room_id):
    """Admin interface to select winners for a specific room"""
    cur = mysql.connection.cursor()
    try:
        # Get room details
        cur.execute("SELECT * FROM rooms WHERE id = %s", (room_id,))
        room = cur.fetchone()
        if not room:
            flash('Room not found', 'danger')
            return redirect(url_for('manage_winners'))
        
        # Get all players in this room with their kill stats
        cur.execute("""
            SELECT rue.user_id, u.username, ugi.gaming_username, 
                   ugi.display_name as team_name,
                   COALESCE(girs.kills_count, 0) as kills_count,
                   COALESCE(girs.reward_earned, 0) as current_reward,
                   COALESCE(girs.reward_status, 'pending') as reward_status,
                   ugi.id as gaming_id,
                   rw.position as winner_position,
                   rw.reward_amount as winner_reward
            FROM room_user_enrollments rue
            JOIN users u ON rue.user_id = u.id
            JOIN room_gaming_ids rgi ON rue.id = rgi.room_user_enrollment_id
            JOIN user_gaming_ids ugi ON rgi.user_gaming_id = ugi.id
            LEFT JOIN gaming_id_room_stats girs ON girs.user_gaming_id = ugi.id AND girs.room_id = %s
            LEFT JOIN room_winners rw ON rw.user_gaming_id = ugi.id AND rw.room_id = %s
            WHERE rue.room_id = %s AND rue.payment_status = 'paid'
            ORDER BY COALESCE(girs.kills_count, 0) DESC, u.username
        """, (room_id, room_id, room_id))
        players = cur.fetchall()
        
        # Get reward settings for this room
        cur.execute("""
            SELECT position, base_reward, kill_bonus_per_kill, max_kill_bonus
            FROM room_reward_settings
            WHERE room_id = %s
            ORDER BY position
        """, (room_id,))
        reward_settings = cur.fetchall()
        
        # If no reward settings exist, this means it's an old room - create basic defaults
        if not reward_settings:
            flash('This room was created without reward settings. Please contact admin to configure rewards.', 'warning')
            # Create minimal default settings as fallback
            total_players = len(players)
            entry_fee = float(room[3]) if room[3] is not None else 0
            total_prize_pool = total_players * entry_fee * 0.8 if total_players > 0 else 1000
            
            default_rewards = [
                (1, total_prize_pool * 0.50, 5.0, 100.0),   # 1st: 50%
                (2, total_prize_pool * 0.30, 3.0, 75.0),    # 2nd: 30%
                (3, total_prize_pool * 0.20, 2.0, 50.0),    # 3rd: 20%
            ]
            
            for position, base_reward, kill_bonus, max_kill_bonus in default_rewards:
                cur.execute("""
                    INSERT INTO room_reward_settings 
                    (room_id, position, base_reward, kill_bonus_per_kill, max_kill_bonus)
                    VALUES (%s, %s, %s, %s, %s)
                """, (room_id, position, base_reward, kill_bonus, max_kill_bonus))
            
            mysql.connection.commit()
            reward_settings = default_rewards
        
        return render_template('admin_room_winners.html', 
                             room=room, players=players, reward_settings=reward_settings)
    
    except Exception as e:
        flash(f'Error loading room winner selection: {str(e)}', 'danger')
        return redirect(url_for('manage_winners'))
    finally:
        cur.close()

@app.route('/admin/select_winner', methods=['POST'])
@admin_required
def select_winner():
    """Admin action to select a winner for a specific position in a room"""
    cur = mysql.connection.cursor()
    try:
        room_id = int(request.form['room_id'])
        gaming_id = int(request.form['gaming_id'])
        position = int(request.form['position'])
        notes = request.form.get('notes', '')
        
        # Get player's kill count
        cur.execute("""
            SELECT COALESCE(kills_count, 0) 
            FROM gaming_id_room_stats 
            WHERE user_gaming_id = %s AND room_id = %s
        """, (gaming_id, room_id))
        kills_result = cur.fetchone()
        kills_count = kills_result[0] if kills_result else 0
        
        # Get reward settings for this position
        cur.execute("""
            SELECT base_reward, kill_bonus_per_kill, max_kill_bonus
            FROM room_reward_settings
            WHERE room_id = %s AND position = %s
        """, (room_id, position))
        reward_setting = cur.fetchone()
        
        if not reward_setting:
            flash('Reward settings not found for this position', 'danger')
            return redirect(url_for('room_winner_selection', room_id=room_id))
        
        base_reward, kill_bonus_per_kill, max_kill_bonus = reward_setting
        
        # Calculate performance-based reward
        kill_bonus = min(kills_count * kill_bonus_per_kill, max_kill_bonus)
        total_reward = base_reward + kill_bonus
        performance_score = (kills_count * 10) + (position == 1 and 50 or position == 2 and 30 or 20)
        
        # Check if winner already selected for this position
        cur.execute("""
            SELECT id FROM room_winners 
            WHERE room_id = %s AND position = %s
        """, (room_id, position))
        existing_winner = cur.fetchone()
        
        if existing_winner:
            # Update existing winner
            cur.execute("""
                UPDATE room_winners 
                SET user_gaming_id = %s, kills_count = %s, performance_score = %s, 
                    reward_amount = %s, selected_by = %s, selected_at = NOW(), notes = %s
                WHERE room_id = %s AND position = %s
            """, (gaming_id, kills_count, performance_score, total_reward, 
                  session['user_id'], notes, room_id, position))
        else:
            # Insert new winner
            cur.execute("""
                INSERT INTO room_winners 
                (room_id, user_gaming_id, position, kills_count, performance_score, 
                 reward_amount, selected_by, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (room_id, gaming_id, position, kills_count, performance_score, 
                  total_reward, session['user_id'], notes))
        
        # Log the action
        cur.execute("""
            INSERT INTO winner_selection_history 
            (room_id, action_type, user_gaming_id, position, reward_amount, admin_user_id, details)
            VALUES (%s, 'winner_selected', %s, %s, %s, %s, %s)
        """, (room_id, gaming_id, position, total_reward, session['user_id'], 
              f'Selected for position {position} with {kills_count} kills. Reward: {total_reward} coins'))
        
        mysql.connection.commit()
        
        # Get player info for flash message
        cur.execute("""
            SELECT ugi.gaming_username, u.username 
            FROM user_gaming_ids ugi 
            JOIN users u ON ugi.user_id = u.id 
            WHERE ugi.id = %s
        """, (gaming_id,))
        player_info = cur.fetchone()
        
        position_names = {1: '1st', 2: '2nd', 3: '3rd'}
        position_name = position_names.get(position, f'{position}th')
        
        flash(f'Selected {player_info[1]} ({player_info[0]}) as {position_name} place winner with {total_reward:.2f} coins reward!', 'success')
        
        return redirect(url_for('room_winner_selection', room_id=room_id))
    
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error selecting winner: {str(e)}', 'danger')
        return redirect(url_for('room_winner_selection', room_id=room_id))
    finally:
        cur.close()

@app.route('/admin/distribute_rewards/<int:room_id>')
@admin_required
def distribute_rewards(room_id):
    """Admin action to distribute all rewards for a room's winners"""
    cur = mysql.connection.cursor()
    try:
        # Get all winners for this room who haven't received rewards yet
        cur.execute("""
            SELECT rw.id, rw.user_gaming_id, rw.position, rw.reward_amount, ugi.user_id, u.username, ugi.gaming_username
            FROM room_winners rw
            JOIN user_gaming_ids ugi ON rw.user_gaming_id = ugi.id
            JOIN users u ON ugi.user_id = u.id
            WHERE rw.room_id = %s AND rw.reward_distributed = FALSE AND rw.reward_amount > 0
        """, (room_id,))
        winners = cur.fetchall()
        
        if not winners:
            flash('No pending rewards to distribute for this room', 'info')
            return redirect(url_for('room_winner_selection', room_id=room_id))
        
        total_distributed = 0
        distributed_count = 0
        
        for winner in winners:
            winner_id, gaming_id, position, reward_amount, user_id, username, gaming_username = winner
            
            # Add coins to user's account
            cur.execute("""
                UPDATE users SET coins = coins + %s WHERE id = %s
            """, (reward_amount, user_id))
            
            # Mark reward as distributed
            cur.execute("""
                UPDATE room_winners 
                SET reward_distributed = TRUE, distributed_at = NOW()
                WHERE id = %s
            """, (winner_id,))
            
            # Log the distribution
            cur.execute("""
                INSERT INTO winner_selection_history 
                (room_id, action_type, user_gaming_id, position, reward_amount, admin_user_id, details)
                VALUES (%s, 'reward_distributed', %s, %s, %s, %s, %s)
            """, (room_id, gaming_id, position, reward_amount, session['user_id'], 
                  f'Distributed {reward_amount} coins to {username} ({gaming_username})'))
            
            total_distributed += reward_amount
            distributed_count += 1
        
        mysql.connection.commit()
        flash(f'Successfully distributed {total_distributed:.2f} coins to {distributed_count} winners!', 'success')
        
        return redirect(url_for('room_winner_selection', room_id=room_id))
    
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error distributing rewards: {str(e)}', 'danger')
        return redirect(url_for('room_winner_selection', room_id=room_id))
    finally:
        cur.close()

@app.route('/admin/winner_history/<int:room_id>')
@admin_required
def winner_history(room_id):
    """View winner selection and reward distribution history for a room"""
    cur = mysql.connection.cursor()
    try:
        # Get room details
        cur.execute("SELECT room_name FROM rooms WHERE id = %s", (room_id,))
        room = cur.fetchone()
        if not room:
            flash('Room not found', 'danger')
            return redirect(url_for('manage_winners'))
        
        # Get history
        cur.execute("""
            SELECT wsh.action_type, wsh.position, wsh.reward_amount, wsh.action_timestamp, 
                   wsh.details, u.username as admin_username,
                   ugi.gaming_username, player_u.username as player_username
            FROM winner_selection_history wsh
            JOIN users u ON wsh.admin_user_id = u.id
            LEFT JOIN user_gaming_ids ugi ON wsh.user_gaming_id = ugi.id
            LEFT JOIN users player_u ON ugi.user_id = player_u.id
            WHERE wsh.room_id = %s
            ORDER BY wsh.action_timestamp DESC
        """, (room_id,))
        history = cur.fetchall()
        
        return render_template('admin_winner_history.html', room=room, history=history, room_id=room_id)
    
    except Exception as e:
        flash(f'Error loading winner history: {str(e)}', 'danger')
        return redirect(url_for('manage_winners'))
    finally:
        cur.close()

if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.getenv('PORT', 5000))
    # Get host from environment variable or default to localhost
    host = os.getenv('HOST', '0.0.0.0' if os.getenv('FLASK_ENV') == 'production' else '127.0.0.1')
    
    app.run(host=host, port=port, debug=(os.getenv('FLASK_ENV') != 'production'))