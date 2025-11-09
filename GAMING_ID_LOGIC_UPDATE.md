# Gaming ID Limit Logic Update

## Summary
Changed the gaming ID selection limit for users joining tournaments from using `max_gaming_ids_per_user` to using `max_team_size`.

## Changes Made

### 1. Backend Logic (`app.py`)
**File:** `app.py` line ~1966
**Before:**
```python
max_ids_per_user = room[13] if len(room) > 13 and room[13] else 1  # max_gaming_ids_per_user
if len(selected_gaming_ids) > max_ids_per_user:
    flash(f'You can only select up to {max_ids_per_user} gaming IDs for this room', 'danger')
```

**After:**
```python
max_team_size = room[12] if len(room) > 12 and room[12] else 4  # room[12] = max_team_size
if len(selected_gaming_ids) > max_team_size:
    flash(f'You can only select up to {max_team_size} gaming IDs for this room (team size limit)', 'danger')
```

### 2. Template Updates

#### `join_room_gaming_ids.html`
- Updated display logic to show team size limit instead of gaming ID limit
- Updated JavaScript validation to use team size
- Updated info messages to clarify this is a team size limit

**Before:**
```html
{% set max_ids = room[13] if room|length > 13 and room[13] else 1 %}
<p><strong>Max IDs per User:</strong> {{ max_ids }}</p>
```

**After:**
```html
{% set max_ids = room[12] if room|length > 12 and room[12] else 4 %}
<p><strong>Max IDs per User:</strong> {{ max_ids }} (team size limit)</p>
```

#### `room_details.html`
- Updated room information display to show team size-based limit

**Before:**
```html
{% set max_ids = room[13] if room|length > 13 and room[13] else 1 %}
<li><strong>Max Gaming IDs:</strong> {{ max_ids }} per user</li>
```

**After:**
```html
{% set max_ids = room[12] if room|length > 12 and room[12] else 4 %}
<li><strong>Max Gaming IDs:</strong> {{ max_ids }} per user (team size)</li>
```

## Database Column Mapping
- `room[11]` = `min_team_size` (minimum players per team)
- `room[12]` = `max_team_size` (maximum players per team) ← **Now used for gaming ID limit**
- `room[13]` = `max_gaming_ids_per_user` (old limit, no longer used for validation)

## Impact

### Before the Change:
- Users were limited by `max_gaming_ids_per_user` (typically 1)
- Very restrictive - most users could only use 1 gaming ID per room
- Not related to the actual team structure of tournaments

### After the Change:
- Users can select up to `max_team_size` gaming IDs (typically 4)
- More flexible and allows users to participate with multiple gaming identities
- Aligns with the team-based nature of tournaments
- Respects the tournament's team size configuration

## Example Scenarios

**Room with team size 1-4:**
- Before: User could select max 1 gaming ID
- After: User can select up to 4 gaming IDs

**Room with team size 1-2:**
- Before: User could select max 1 gaming ID  
- After: User can select up to 2 gaming IDs

## Benefits
1. **More Flexible:** Users can participate with multiple gaming identities
2. **Better Team Integration:** Limit aligns with actual team structure
3. **User-Friendly:** Allows users to maximize their participation within team constraints
4. **Consistent Logic:** Uses existing team size configuration rather than separate gaming ID limits

## Testing
✅ Backend validation updated
✅ Frontend display updated  
✅ JavaScript validation updated
✅ User feedback messages updated
✅ Flask application runs without errors
✅ Template rendering works correctly

The system now allows users to join tournaments with multiple gaming IDs up to the maximum team size limit, providing more flexibility while maintaining tournament structure integrity.