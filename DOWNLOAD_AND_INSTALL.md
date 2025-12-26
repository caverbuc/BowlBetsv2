# BowlBets - Download and Installation Guide

## For Mac Users

### Step 1: Download
1. Download the `BowlBets.app.zip` file from the release
2. Find the file in your Downloads folder
3. Double-click the .zip file to unzip it

### Step 2: Install
1. Drag `BowlBets.app` to your Applications folder
   - Or just leave it in Downloads if you prefer

### Step 3: First Time Opening
**IMPORTANT:** The first time you open the app, macOS will show a security warning because the app isn't from the App Store.

Here's how to open it the first time:
1. **Right-click** (or Control+click) on `BowlBets.app`
2. Click **"Open"** from the menu
3. Click **"Open"** again in the security dialog
4. The app will start!

**After the first time**, you can just double-click the app normally.

### Step 4: Get Your API Key
Before you can use BowlBets, you need a free API key:

1. Visit: https://collegefootballdata.com
2. Click **"Get API Key"** or **"Sign Up"**
3. Create a free account
4. Copy your API key (it will look like a long string of letters and numbers)
5. In BowlBets, go to **File → Settings**
6. Paste your API key and click outside the box to save

### Step 5: Start Using BowlBets!
1. Go to **Series → New Series** to create your betting series
2. Follow the wizard to set up the season and participants
3. Click **"Sync from APIs"** to load all the bowl games
4. Start making picks!

## Need Help?
- Click **Help → About BowlBets** in the app to see the full user guide
- The user guide explains how to make picks, manage odds, and track results

## Troubleshooting

### "BowlBets.app is damaged and can't be opened"
This happens because the app isn't code-signed. Here's how to fix it:

1. Open **Terminal** (in Applications → Utilities)
2. Type this command and press Enter:
   ```
   xattr -cr ~/Downloads/BowlBets.app
   ```
   (If you moved it to Applications, use: `xattr -cr /Applications/BowlBets.app`)
3. Close Terminal and try opening the app again

### "No games showing up"
- Make sure you've entered your API key in Settings
- Click the **"Sync from APIs"** button to load games

### "Odds not available yet"
- Betting lines usually appear a few weeks before bowl season
- You can manually enter odds using the edit button (✎) if needed

## Sharing Your Series
Want to share your picks with a friend?
1. Go to **Series → Export Series**
2. Save the file and send it to your friend
3. They can import it using **Series → Import Series**

---

**Enjoy your bowl season betting! 🏈**
