# Gaming ID Room-Level Duplicate Prevention System

## Overview
This document describes the gaming ID enrollment logic that prevents duplicate gaming usernames within individual tournament rooms while allowing users to add duplicate gaming IDs globally on the website.

## Key Requirements Met

### 1. Multiple Gaming ID Support
- Users can register multiple gaming IDs per platform (PUBG, FreeFire, etc.)
- Users can select multiple gaming IDs when joining tournaments
- Maximum gaming IDs per room enrollment limited by room's `max_team_size` setting
- **Global duplicates allowed**: Users can add gaming IDs that already exist on the platform

### 2. Room-Level Duplicate Prevention Logic
- **Room-Specific Uniqueness**: Same gaming username cannot be enrolled in the same room by different users
- **Gaming ID Record Protection**: Specific gaming ID records cannot be enrolled multiple times in the same room
- **No Global Restrictions**: Users can freely add gaming usernames that other users have

## Implementation Details

### Database Structure
```sql
-- User gaming IDs table (allows duplicate gaming_username globally)
user_gaming_ids:
- id (primary key)
- user_id (foreign key to users)
- gaming_platform (PUBG, FreeFire, etc.)
- gaming_username (the actual game username - duplicates allowed globally)
- display_name (user-friendly name)
- is_primary (boolean)
- is_active (boolean)

-- Room enrollments
room_user_enrollments:
- id (primary key)
- room_id (foreign key)
- user_id (foreign key)
- gaming_ids_count (number of gaming IDs used)
- total_entry_fee (calculated based on count)

-- Gaming ID selections for rooms
room_gaming_ids:
- room_user_enrollment_id (foreign key)
- user_gaming_id (foreign key)
```

### Validation Layers

#### Layer 1: User's Own Gaming ID Duplication Check
```python
# Prevents user from adding same gaming username multiple times to their account
cur.execute("""
    SELECT id FROM user_gaming_ids 
    WHERE user_id = %s AND gaming_username = %s AND gaming_platform = %s
""", (session['user_id'], gaming_username, gaming_platform))
```

#### Layer 2: Gaming ID Record Validation (Room-Level)
```python
# Check if specific gaming ID records are already enrolled in THIS room
cur.execute("""
    SELECT ug.gaming_username, ug.gaming_platform, u.username, u.id as enrolled_by_user_id
    FROM room_gaming_ids rgi
    JOIN room_user_enrollments rue ON rgi.room_user_enrollment_id = rue.id
    JOIN user_gaming_ids ug ON rgi.user_gaming_id = ug.id
    JOIN users u ON rue.user_id = u.id
    WHERE rue.room_id = %s AND rue.is_active = TRUE 
    AND rgi.user_gaming_id IN (%s, %s, ...)
""", [room_id] + selected_gaming_ids)
```

#### Layer 3: Gaming Username Conflict Detection (Room-Level Only)
```python
# Check for gaming username conflicts within the specific room only
for gaming_username, gaming_platform in selected_gaming_info:
    cur.execute("""
        SELECT u.username, ug.gaming_username, ug.gaming_platform
        FROM room_gaming_ids rgi
        JOIN room_user_enrollments rue ON rgi.room_user_enrollment_id = rue.id
        JOIN user_gaming_ids ug ON rgi.user_gaming_id = ug.id
        JOIN users u ON rue.user_id = u.id
        WHERE rue.room_id = %s AND rue.is_active = TRUE
        AND ug.gaming_username = %s AND ug.gaming_platform = %s
        AND rue.user_id != %s
    """, (room_id, gaming_username, gaming_platform, current_user_id))
```

## User Journey

### Gaming ID Management
1. **Add Gaming ID**: User adds gaming username (validated for global uniqueness)
2. **Edit Gaming ID**: User can modify gaming username (re-validated for conflicts)
3. **Set Primary**: User can mark one gaming ID as primary per platform

### Tournament Enrollment
1. **Select Gaming IDs**: User chooses from their active gaming IDs
2. **Validation**: System checks for duplicates and conflicts
3. **Team Size Limit**: Maximum selections limited by room's `max_team_size`
4. **Payment**: Entry fee calculated as `count * room_entry_fee`

## Error Messages

### Global Uniqueness Violations
```
### Error Messages

#### User's Own Duplicate Prevention
```
"PUBG username 'PlayerX123' already exists in your account"
```

#### Room Enrollment Conflicts
```
"⚠️ Gaming ID(s) already enrolled in this room: PlayerX123 (PUBG) - already enrolled by alice_smith"
```

#### Room-Level Gaming Username Conflicts
```
"⚠️ Gaming username conflicts in this room: PlayerX123 (PUBG) - already used by bob_wilson in this room."
```

## Benefits

### For Players
- **Freedom to add any gaming username** - No global restrictions
- **Can use multiple gaming accounts** in tournaments
- **Only room-level conflicts prevented** - Reduces friction
- **Clear error messages** for room-specific conflicts

### For Administrators
- **Room-level gaming username tracking** - Prevents disputes within tournaments
- **No global username restrictions** - Easier user onboarding
- **Audit trail for room enrollments** - Easy conflict resolution
- **Flexible gaming ID management** - Users can freely manage their accounts

### For Platform
- **Reduced registration friction** - Users don't need unique global gaming usernames
- **Room-level data integrity** - Ensures fair competition per tournament
- **Scalable multi-gaming-ID support** - No global uniqueness bottlenecks
- **Clear business rules** - Room-specific validation only

## Configuration

### Room Settings
```python
# Room configuration affects gaming ID limits
max_team_size = 4  # Maximum gaming IDs per user per room
entry_fee = 50     # Fee per gaming ID
max_players = 100  # Total players in room
```

### Gaming Platforms Supported
- PUBG Mobile
- FreeFire
- Call of Duty Mobile
- (Extensible for future platforms)

## Key Differences from Global Uniqueness Approach

### What's Allowed Now
✅ **Multiple users can have same gaming username globally**
✅ **Users can freely add any gaming username to their account**
✅ **No global validation when adding/editing gaming IDs**
✅ **Same gaming username can be used across different rooms**

### What's Still Prevented
❌ **Same gaming username in the same room by different users**
❌ **Same gaming ID record enrolled multiple times in same room**
❌ **User adding duplicate gaming username to their own account**

## Testing

### Validation Test Scenarios
1. **Multiple Users Same Gaming Username**: Different users can add "PlayerX123" globally
2. **Room-Level Conflicts**: User A and User B with same gaming username cannot join same room
3. **Cross-Room Usage**: Same gaming username can be used in different rooms
4. **User Account Duplicates**: User cannot add same gaming username twice to their account
5. **Gaming ID Record Duplicates**: Same gaming ID record cannot be enrolled twice in same room

## Future Enhancements

### Potential Improvements
1. **Gaming ID Verification**: Screenshot/proof requirements for disputed usernames
2. **Room-Level Gaming Username History**: Track gaming username usage per room
3. **Advanced Conflict Resolution**: Admin tools to resolve gaming username disputes
4. **Gaming Username Aliases**: Allow users to set display names different from gaming usernames
5. **Platform Integration**: Direct verification with game APIs for room enrollments

This approach provides **maximum flexibility** for users while ensuring **room-level tournament integrity**. Users can freely manage their gaming IDs without global restrictions, but conflicts are prevented within individual tournaments where it matters most.
```

### Room Enrollment Conflicts
```
"⚠️ Gaming ID(s) already enrolled in this room: PlayerX123 (PUBG) - already enrolled by alice_smith"
```

### Gaming Username Conflicts
```
"⚠️ Gaming username conflicts detected: PlayerX123 (PUBG) - already used by bob_wilson. The same gaming username cannot be used by multiple users in the same room."
```

## Benefits

### For Players
- Can use multiple gaming accounts in tournaments
- Prevents gaming username conflicts and disputes
- Clear error messages for conflicts
- Flexible team size options

### For Administrators
- Complete gaming username tracking
- Prevents cheating through duplicate accounts
- Audit trail for all gaming ID usage
- Easy conflict resolution

### For Platform
- Data integrity enforcement
- Scalable multi-gaming-ID support
- Prevents tournament disputes
- Clear business rules

## Configuration

### Room Settings
```python
# Room configuration affects gaming ID limits
max_team_size = 4  # Maximum gaming IDs per user per room
entry_fee = 50     # Fee per gaming ID
max_players = 100  # Total players in room
```

### Gaming Platforms Supported
- PUBG Mobile
- FreeFire
- Call of Duty Mobile
- (Extensible for future platforms)

## Testing

### Validation Test Script
Run `test_gaming_id_validation.py` to verify:
- Global gaming username uniqueness
- Room-level conflict detection
- Team size limit enforcement
- Data integrity checks

### Test Scenarios
1. **Single User Multiple IDs**: User joins with 2-4 gaming IDs
2. **Duplicate Prevention**: User tries to add existing gaming username
3. **Room Conflicts**: Different users with same gaming username attempt enrollment
4. **Team Size Limits**: User exceeds maximum gaming IDs per room
5. **Cross-Platform**: Same username on different platforms (allowed)

## Future Enhancements

### Potential Improvements
1. **Case-Insensitive Validation**: Prevent "PlayerX" and "playerx" conflicts
2. **Gaming ID Verification**: Screenshot/proof requirements
3. **Platform Integration**: Direct verification with game APIs
4. **Advanced Fraud Detection**: Pattern analysis for suspicious accounts
5. **Gaming ID History**: Track gaming username changes over time

### Performance Optimizations
1. **Database Indexing**: Optimize validation queries
2. **Caching**: Cache frequently accessed gaming ID data
3. **Batch Validation**: Optimize multi-gaming-ID validations
4. **Connection Pooling**: Improve database performance

## Maintenance

### Regular Checks
- Run validation script weekly
- Monitor for data integrity issues
- Check for orphaned records
- Validate gaming username uniqueness

### Data Cleanup
- Remove inactive gaming IDs after 6 months
- Archive old room enrollment data
- Clean up duplicate gaming username attempts
- Maintain audit logs

## Security Considerations

### Validation Security
- Server-side validation only (client-side validation is supplementary)
- SQL injection prevention through parameterized queries
- Input sanitization for gaming usernames
- Rate limiting for gaming ID additions

### Access Control
- Users can only modify their own gaming IDs
- Admins can view all gaming IDs for conflict resolution
- Audit logs for all gaming ID changes
- Session validation for all operations

This enhanced system ensures tournament integrity while providing flexibility for players to use multiple gaming accounts legitimately.