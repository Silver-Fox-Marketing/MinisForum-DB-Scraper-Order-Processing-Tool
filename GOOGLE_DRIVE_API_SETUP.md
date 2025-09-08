# Google Drive API Setup Guide for Enhanced Order Form

## 🎯 Complete Setup Instructions

### Step 1: Create Google Cloud Project

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Sign in with your Google account (preferably the Silver Fox Marketing account)

2. **Create New Project**
   - Click "Select a project" dropdown at the top
   - Click "NEW PROJECT"
   - Project name: `Silver-Fox-Order-Form`
   - Click "CREATE"

### Step 2: Enable Google Drive API

1. **Enable the API**
   - In the left sidebar, click "APIs & Services" > "Library"
   - Search for "Google Drive API"
   - Click on it and press "ENABLE"

### Step 3: Create OAuth 2.0 Credentials

1. **Configure OAuth Consent Screen**
   - Go to "APIs & Services" > "OAuth consent screen"
   - Choose "External" (unless you have Google Workspace)
   - Click "CREATE"
   
2. **Fill in App Information**
   - App name: `Silver Fox Order Form`
   - User support email: (your email)
   - App logo: (optional - can upload Silver Fox logo)
   - Application home page: `https://silver-fox-marketing.github.io/enhanced-order-form-v2.0/`
   - Authorized domains: `silver-fox-marketing.github.io`
   - Developer contact: (your email)
   - Click "SAVE AND CONTINUE"

3. **Add Scopes**
   - Click "ADD OR REMOVE SCOPES"
   - Search and select: `https://www.googleapis.com/auth/drive.file`
   - This allows the app to create and manage its own files
   - Click "UPDATE" then "SAVE AND CONTINUE"

4. **Add Test Users** (if in testing mode)
   - Add your email and any team members who need access
   - Click "SAVE AND CONTINUE"

### Step 4: Create API Credentials

1. **Create OAuth Client ID**
   - Go to "APIs & Services" > "Credentials"
   - Click "+ CREATE CREDENTIALS" > "OAuth client ID"
   
2. **Configure OAuth Client**
   - Application type: **Web application**
   - Name: `Silver Fox Order Form Client`
   
3. **Add Authorized JavaScript Origins**
   Add ALL of these:
   ```
   http://localhost
   http://localhost:8080
   http://127.0.0.1
   http://127.0.0.1:8080
   https://silver-fox-marketing.github.io
   ```
   
4. **Add Authorized Redirect URIs**
   Add these:
   ```
   http://localhost
   http://localhost:8080
   http://127.0.0.1
   http://127.0.0.1:8080
   https://silver-fox-marketing.github.io/enhanced-order-form-v2.0
   ```

5. **Save and Copy Credentials**
   - Click "CREATE"
   - **IMPORTANT**: Copy your Client ID (looks like: xxxxx.apps.googleusercontent.com)
   - Keep this window open or save the Client ID

### Step 5: Create API Key (Optional but Recommended)

1. **Create API Key**
   - Click "+ CREATE CREDENTIALS" > "API key"
   - Copy the API key
   - Click "RESTRICT KEY"
   
2. **Restrict the API Key**
   - Name: `Silver Fox Order Form API Key`
   - Application restrictions: "HTTP referrers"
   - Add these referrers:
   ```
   https://silver-fox-marketing.github.io/*
   http://localhost/*
   http://127.0.0.1/*
   ```
   - API restrictions: "Restrict key"
   - Select: "Google Drive API"
   - Click "SAVE"

### Step 6: Update Your Order Form

1. **Open enhanced-order-form-v2.html** in a text editor

2. **Find these lines** (around line 567-569):
   ```javascript
   // Google API Configuration
   const CLIENT_ID = 'YOUR_CLIENT_ID.apps.googleusercontent.com';
   const API_KEY = 'YOUR_API_KEY'; // Optional but recommended
   ```

3. **Replace with your actual credentials**:
   ```javascript
   // Google API Configuration
   const CLIENT_ID = 'paste-your-client-id-here.apps.googleusercontent.com';
   const API_KEY = 'paste-your-api-key-here'; // Optional but recommended
   ```

4. **Save the file**

### Step 7: Test the Integration

1. **Open the form in your browser**
   - Open enhanced-order-form-v2.html
   
2. **Look for Google Drive Status**
   - Top right corner should show "Google Drive: Not Connected"
   - Click "Sign in with Google" button (if visible)
   
3. **Authorize the App**
   - Sign in with your Google account
   - Grant permissions when prompted
   - Status should change to "Google Drive: Connected"

4. **Test CSV Upload**
   - Fill out a test order
   - Check "Auto-upload to Google Drive"
   - Click "Export to CSV"
   - Check your Google Drive for the uploaded file

## 🔧 Troubleshooting

### Common Issues:

1. **"Invalid Client" Error**
   - Double-check CLIENT_ID is copied correctly
   - Ensure no extra spaces or characters

2. **"Origin not allowed" Error**
   - Add your current URL to authorized JavaScript origins
   - Wait 5-10 minutes for changes to propagate

3. **"Redirect URI mismatch" Error**
   - Add the exact URL you're using to authorized redirect URIs
   - Include both with and without trailing slashes

4. **Files not appearing in Drive**
   - Check browser console for errors (F12)
   - Ensure you granted Drive permissions
   - Try signing out and back in

### Testing Locally:

If testing locally, you can use Python's simple HTTP server:
```bash
# Navigate to your form directory
cd C:\Users\Workstation_1\Documents\Tools\ClaudeCode

# For Python 3:
python -m http.server 8080

# Then open: http://localhost:8080/enhanced-order-form-v2.html
```

## 📁 Where Files Are Saved in Google Drive

- Files are saved in the root of your Google Drive
- File naming: `silver-fox-order-YYYY-MM-DD-HH-MM-SS.csv`
- You can create a folder in Drive and modify the code to save there

## 🔒 Security Notes

- Never share your Client Secret (though we don't use it in client-side apps)
- API keys are visible in the source code, so always restrict them
- Only grant minimum necessary permissions
- Regularly review authorized users in Google Cloud Console

## 📞 Need Help?

- Check browser console (F12) for detailed error messages
- Google Cloud Console: https://console.cloud.google.com
- API Dashboard: Check quotas and usage
- Test with a simple HTML file first if having issues

---

Ready to integrate! Once set up, your order forms will automatically upload to Google Drive! 🎊