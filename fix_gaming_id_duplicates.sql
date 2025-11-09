-- Fix Gaming ID Duplicate Enrollment Vulnerability
-- This script adds constraints to prevent users from enrolling the same gaming ID multiple times in the same room

USE gaming_platform;

-- First, let's check if there are any existing duplicate gaming IDs in the same room
SELECT 
    r.room_name,
    ug.gaming_username,
    ug.gaming_platform,
    COUNT(*) as enrollment_count,
    GROUP_CONCAT(u.username) as users
FROM room_gaming_ids rgi
JOIN room_user_enrollments rue ON rgi.room_user_enrollment_id = rue.id
JOIN user_gaming_ids ug ON rgi.user_gaming_id = ug.id
JOIN users u ON rue.user_id = u.id
JOIN rooms r ON rue.room_id = r.id
WHERE rue.is_active = TRUE
GROUP BY rue.room_id, rgi.user_gaming_id
HAVING COUNT(*) > 1;

-- Add unique constraint to prevent same gaming ID from being enrolled in same room multiple times
-- This creates a composite unique key on room_id + user_gaming_id
ALTER TABLE room_gaming_ids 
ADD CONSTRAINT unique_gaming_id_per_room 
UNIQUE KEY (
    (SELECT room_id FROM room_user_enrollments WHERE id = room_user_enrollment_id), 
    user_gaming_id
);

-- Alternative approach using a composite unique index (more reliable)
-- First drop the constraint if it exists
ALTER TABLE room_gaming_ids DROP INDEX IF EXISTS unique_gaming_id_per_room;

-- Create a unique constraint using a more direct approach
-- We'll need to create a new table structure that directly includes room_id for better constraint enforcement

-- Let's first create a view to check current enrollments
CREATE OR REPLACE VIEW gaming_id_enrollment_check AS
SELECT 
    rue.room_id,
    rgi.user_gaming_id,
    ug.gaming_username,
    ug.gaming_platform,
    u.username as enrolled_by,
    rue.enrolled_at,
    rgi.room_user_enrollment_id
FROM room_gaming_ids rgi
JOIN room_user_enrollments rue ON rgi.room_user_enrollment_id = rue.id
JOIN user_gaming_ids ug ON rgi.user_gaming_id = ug.id
JOIN users u ON rue.user_id = u.id
WHERE rue.is_active = TRUE;

-- Add a better constraint by modifying the room_gaming_ids table
-- Add room_id directly to room_gaming_ids for better constraint enforcement
ALTER TABLE room_gaming_ids ADD COLUMN room_id INT;

-- Update the room_id column with values from room_user_enrollments
UPDATE room_gaming_ids rgi
JOIN room_user_enrollments rue ON rgi.room_user_enrollment_id = rue.id
SET rgi.room_id = rue.room_id;

-- Add foreign key constraint
ALTER TABLE room_gaming_ids 
ADD CONSTRAINT fk_room_gaming_ids_room 
FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE;

-- Now add the unique constraint we really want
ALTER TABLE room_gaming_ids 
ADD CONSTRAINT unique_gaming_id_per_room 
UNIQUE KEY (room_id, user_gaming_id);

-- Create index for better performance
CREATE INDEX idx_room_gaming_ids_lookup ON room_gaming_ids (room_id, user_gaming_id);