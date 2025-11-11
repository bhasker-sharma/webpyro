-- Migration: Add Y-axis limit columns to device_settings table
-- Date: 2025-11-11
-- Description: Adds graph_y_min and graph_y_max columns to allow users to set fixed Y-axis limits for graphs
-- These settings are applied to ALL devices (common configuration) since all devices show on the same graph

-- Step 1: Add graph_y_min column with default value of 600
ALTER TABLE device_settings
ADD COLUMN IF NOT EXISTS graph_y_min FLOAT DEFAULT 600.0;

-- Step 2: Add graph_y_max column with default value of 2000
ALTER TABLE device_settings
ADD COLUMN IF NOT EXISTS graph_y_max FLOAT DEFAULT 2000.0;

-- Step 3: Update existing devices to have the default values if they are NULL
UPDATE device_settings
SET graph_y_min = 600.0
WHERE graph_y_min IS NULL;

UPDATE device_settings
SET graph_y_max = 2000.0
WHERE graph_y_max IS NULL;

-- Step 4: Make columns NOT NULL now that all rows have values
ALTER TABLE device_settings
ALTER COLUMN graph_y_min SET NOT NULL;

ALTER TABLE device_settings
ALTER COLUMN graph_y_max SET NOT NULL;

-- Step 5: Add comments to the columns for documentation
COMMENT ON COLUMN device_settings.graph_y_min IS 'Minimum Y-axis value (temperature) for graph display in degrees Celsius. Applied to all devices (common config).';
COMMENT ON COLUMN device_settings.graph_y_max IS 'Maximum Y-axis value (temperature) for graph display in degrees Celsius. Applied to all devices (common config).';
