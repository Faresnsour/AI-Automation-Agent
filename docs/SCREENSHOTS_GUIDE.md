# 📸 Screenshots Guide

This guide explains how to add screenshots to your GitHub repository.

## Required Screenshots

You need to create 4 screenshots:

1. **dashboard.png** - Main dashboard/home page
2. **processing.png** - Email processing page
3. **analytics.png** - Analytics page  
4. **tasks.png** - Tasks management page

## How to Take Screenshots

### Step 1: Start the Dashboard

```bash
# Terminal 1: Start API
python api/server.py

# Terminal 2: Start Dashboard
streamlit run dashboard/dashboard.py
```

### Step 2: Open Dashboard

Open `http://localhost:8501` in your browser.

### Step 3: Take Screenshots

1. **Dashboard Overview (dashboard.png)**
   - Go to "🏠 Home" page
   - Take a screenshot of the main dashboard
   - Save as `docs/images/dashboard.png`

2. **Email Processing (processing.png)**
   - Go to "📧 Process Email" page
   - Fill in a sample email (or leave it empty)
   - Take a screenshot
   - Save as `docs/images/processing.png`

3. **Analytics (analytics.png)**
   - Go to "📊 Analytics" page
   - Take a screenshot of the charts and statistics
   - Save as `docs/images/analytics.png`

4. **Task Management (tasks.png)**
   - Go to "✅ Tasks" page
   - Take a screenshot
   - Save as `docs/images/tasks.png`

## Screenshot Tips

- **Resolution**: Use at least 1920x1080 for good quality
- **Format**: PNG format is recommended
- **Browser**: Use Chrome or Firefox for best results
- **Full Page**: Take full page screenshots (not just visible area)
- **Clean UI**: Make sure the dashboard looks clean and professional

## Tools for Screenshots

### Linux:
- **Built-in**: Use `Print Screen` or `Shift + Print Screen`
- **Flameshot**: `sudo apt install flameshot` (recommended)
- **GNOME Screenshot**: Built-in on GNOME

### Mac:
- **Built-in**: `Cmd + Shift + 4` for selection
- **Full page**: Use browser extensions

### Windows:
- **Snipping Tool**: Built-in
- **Windows + Shift + S**: Quick screenshot

## Browser Extensions (Recommended)

- **Full Page Screen Capture** (Chrome/Firefox)
- **Awesome Screenshot** (Chrome/Firefox)
- **Nimbus Screenshot** (Chrome/Firefox)

## After Taking Screenshots

1. Save all screenshots in `docs/images/` folder
2. Make sure filenames match exactly:
   - `dashboard.png`
   - `processing.png`
   - `analytics.png`
   - `tasks.png`

3. Add to git:
```bash
git add docs/images/*.png
git commit -m "Add dashboard screenshots"
git push
```

## Alternative: Use Placeholder Images

If you don't have screenshots yet, you can:
1. Use placeholder images from [placeholder.com](https://via.placeholder.com)
2. Or remove the Screenshots section from README temporarily
3. Add real screenshots later

## Example Screenshot Dimensions

Recommended sizes:
- **Width**: 1200-1920 pixels
- **Height**: 600-1080 pixels
- **Aspect Ratio**: 16:9 or 2:1

