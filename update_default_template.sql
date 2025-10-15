-- First, let's see what templates exist
SELECT id, template_name, is_system_default, is_active
FROM template_configs
ORDER BY id;

-- Update: Remove system default flag from "Default Shortcut Pack"
UPDATE template_configs
SET is_system_default = false
WHERE template_name = 'Default Shortcut Pack';

-- Update: Set "ShortCut Pack" as the new system default
UPDATE template_configs
SET is_system_default = true
WHERE template_name = 'ShortCut Pack';

-- Verify the changes
SELECT id, template_name, is_system_default, is_active
FROM template_configs
ORDER BY id;
