# Theme Management Guide

## Overview
This Django CMS supports multiple themes that can be switched easily. Themes are stored in the `themes/` directory and contain templates and static files.

## Available Themes
- **default** - The default theme with basic styling
- **modern** - Modern theme with updated UI components

## Theme Installation

### Installing a New Theme

1. **Extract theme to themes folder:**
   ```bash
   # From backup zip
   powershell "Expand-Archive -Path 'default_theme_backup.zip' -DestinationPath 'themes' -Force"

   # Or create new theme manually
   mkdir themes/mytheme
   ```

2. **Required theme structure:**
   ```
   themes/
   └── your_theme_name/
       ├── base.html              # Main layout template
       ├── users/
       │   ├── login.html
       │   ├── signup.html
       │   └── profile.html
       ├── catalog/
       │   ├── product_list.html
       │   └── product_detail.html
       ├── orders/
       │   └── order_list.html
       └── static/               # Optional CSS/JS files
           ├── site.css
           └── custom.js
   ```

3. **Theme must contain:**
   - `base.html` (main template)
   - Template files matching your apps structure
   - Optional `static/` folder for CSS/JS/images

## Switching Active Theme

### Method 1: Environment Variable (Recommended)
```bash
# Windows
set THEME=modern
python manage.py runserver

# Linux/Mac
export THEME=modern
python manage.py runserver
```

### Method 2: Edit settings.py
Edit `config/settings.py` line 31:
```python
THEME = os.getenv("THEME", "modern")  # Change default theme name
```

### Method 3: Create .env file
Create a `.env` file in project root:
```bash
echo THEME=modern > .env
```

## Theme Development

### Creating a Custom Theme

1. **Copy existing theme:**
   ```bash
   cp -r themes/default themes/my_custom_theme
   ```

2. **Modify templates as needed:**
   - Update `base.html` for layout changes
   - Customize individual page templates
   - Add custom CSS in `static/site.css`

3. **Switch to your theme:**
   ```bash
   set THEME=my_custom_theme
   ```

### Template Context Variables
All themes have access to:
- `SITE_NAME` - Site name from settings
- `THEME` - Current active theme name
- Django's default context (user, messages, etc.)

## Backup and Restore

### Creating Theme Backup
```bash
powershell "Compress-Archive -Path 'themes\default' -DestinationPath 'theme_backup.zip' -Force"
```

### Restoring Theme
```bash
# Delete current theme
rmdir /s themes\default

# Restore from backup
powershell "Expand-Archive -Path 'theme_backup.zip' -DestinationPath 'themes' -Force"
```

## Troubleshooting

### Theme Not Loading
1. Check theme name spelling in environment variable
2. Verify theme folder exists in `themes/` directory
3. Ensure `base.html` exists in theme folder
4. Restart Django development server

### Missing Templates
- Ensure all required templates exist in theme folder
- Check Django error messages for missing template names
- Copy missing templates from `default` theme as starting point

### Static Files Not Loading
1. Run `python manage.py collectstatic` if using production setup
2. Check `STATICFILES_DIRS` includes theme static folder
3. Verify static files exist in `themes/{theme}/static/`

## Technical Details

The theme system works by:
1. Reading `THEME` environment variable (default: "default")
2. Setting template directory to `themes/{THEME}/` in settings.py
3. Django loads templates from this directory first
4. Falls back to app-specific templates if not found in theme