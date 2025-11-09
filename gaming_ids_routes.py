# Gaming IDs Management Routes
# Add these routes to app.py for the new gaming IDs functionality

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
            
            # Validate selections
            max_ids_per_user = room[13] if len(room) > 13 and room[13] else 1  # max_gaming_ids_per_user
            if len(selected_gaming_ids) > max_ids_per_user:
                flash(f'You can only select up to {max_ids_per_user} gaming IDs for this room', 'danger')
                return render_template('join_room_gaming_ids.html', 
                                     room=room, user_gaming_ids=user_gaming_ids,
                                     current_players=current_players, available_slots=available_slots)
            
            # Check available slots
            if len(selected_gaming_ids) > available_slots:
                flash(f'Not enough slots available. You selected {len(selected_gaming_ids)} IDs but only {available_slots} slots remain', 'danger')
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

@app.route('/api/room/<int:room_id>/gaming_ids_enrollments')
@login_required
def get_room_gaming_ids_enrollments(room_id):
    """API endpoint to get room enrollments with gaming IDs"""
    cur = mysql.connection.cursor()
    try:
        cur.execute("""
            SELECT rue.id, rue.user_id, u.username, rue.gaming_ids_count, 
                   rue.total_entry_fee, rue.enrolled_at,
                   GROUP_CONCAT(CONCAT(ug.display_name, ' (', ug.gaming_platform, ')') SEPARATOR ', ') as gaming_ids,
                   GROUP_CONCAT(rg.kills_count SEPARATOR ', ') as kills_list,
                   SUM(rg.reward_earned) as total_rewards
            FROM room_user_enrollments rue
            JOIN users u ON rue.user_id = u.id
            LEFT JOIN room_gaming_ids rg ON rue.id = rg.room_user_enrollment_id
            LEFT JOIN user_gaming_ids ug ON rg.user_gaming_id = ug.id
            WHERE rue.room_id = %s AND rue.payment_status = 'paid' AND rue.is_active = TRUE
            GROUP BY rue.id
            ORDER BY rue.enrolled_at ASC
        """, (room_id,))
        
        enrollments = cur.fetchall()
        return jsonify({
            'success': True,
            'enrollments': [
                {
                    'id': e[0],
                    'user_id': e[1],
                    'username': e[2],
                    'gaming_ids_count': e[3],
                    'total_entry_fee': e[4],
                    'enrolled_at': e[5].isoformat() if e[5] else None,
                    'gaming_ids': e[6] or '',
                    'kills_list': e[7] or '',
                    'total_rewards': float(e[8] or 0)
                }
                for e in enrollments
            ]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        cur.close()