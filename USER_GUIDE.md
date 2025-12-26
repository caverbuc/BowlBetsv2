# BowlBets User Guide

## Welcome to BowlBets!

BowlBets is a college football bowl game betting tracker for two people. This guide will walk you through everything you need to know to use the application.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Setting Up Your First Series](#setting-up-your-first-series)
3. [Syncing Game Data](#syncing-game-data)
4. [Making Picks](#making-picks)
5. [Managing Odds](#managing-odds)
6. [Tracking Results](#tracking-results)
7. [Series Management](#series-management)
8. [Import/Export](#importexport)
9. [Tips & Tricks](#tips--tricks)

---

## Getting Started

### Configuring Your API Key

Before you can use BowlBets, you need to configure your College Football Data API key:

1. **Get an API Key**: Visit [collegefootballdata.com](https://collegefootballdata.com) and sign up for a free API key
2. **Open Settings**: Go to **File → Settings**
3. **Enter API Key**: Paste your API key in the "CFD API Key" field
4. **Save**: Click outside the field to save

The API key is stored securely and used to fetch game schedules, scores, and betting lines.

---

## Setting Up Your First Series

A **betting series** is a season-long competition between two people betting on bowl games.

### Creating a New Series

1. Click **Series → New Series** or the **+ Add Series** button in the sidebar
2. The Series Wizard will guide you through three steps:

#### Step 1: Select Season
- Choose the bowl season year (e.g., "2025" for the 2025-2026 bowl season)
- Or create a new season if it doesn't exist

#### Step 2: Choose Participants
- Enter the names of both participants (Person 1 and Person 2)
- These can be existing people or new names

#### Step 3: Set Betting Amounts
- **Regular Bowl Games**: Default bet amount for most bowl games
- **CFP Semi-Finals/Quarterfinals**: Higher stakes for playoff games
- **CFP Championship**: Highest stakes for the championship game

Click **Finish** to create your series!

---

## Syncing Game Data

### Initial Sync

After creating a series, you need to sync game data:

1. Click **Sync from APIs (Update Games & Odds)** button
2. The app will fetch:
   - All bowl games for the current season
   - Team information and logos
   - Betting lines (spreads and over/under totals)
   - Venue and broadcast information

This process takes 30-60 seconds. You'll see progress updates in the status bar.

### When to Sync

- **Before the season starts**: Get the initial game schedule
- **Throughout the season**: Update scores and odds
- **After games complete**: Get final scores for result calculation

**Tip**: Sync daily during bowl season to keep odds and scores current!

---

## Making Picks

### Understanding the Picker System

For each game, one person is designated as the **Picker** (shown with a blue label). The picker makes the first choice, and their opponent automatically gets the opposite side.

### Quick Pick: Spread Betting

1. **Select Your Team**: Click on a team name to pick them with the current spread
   - Example: Clicking "Ohio State (-9.5)" means you bet on Ohio State giving 9.5 points
   - Your opponent automatically gets "Notre Dame (+9.5)"

2. **Automatic Mirror**: Both picks are saved instantly - no need for your opponent to confirm

### Quick Pick: Over/Under

1. **Click Over or Under**: Next to the O/U line (e.g., "O/U: 52.5")
   - Click "Over" if you think the total score will be MORE than 52.5
   - Click "Under" if you think it will be LESS than 52.5

2. **Automatic Mirror**: Your opponent gets the opposite side automatically

### Detailed Pick Dialog

For more control, click the **Pick** button on any game to open the detailed picker:

1. Choose **Spread** or **Over/Under**
2. For spreads: Select your team and adjust the line if needed
3. For O/U: Choose Over or Under and adjust the total if needed
4. Set your bet amount (defaults are based on game tier)
5. Click **Save**

### Changing the Picker

- **Click the Picker Label** to toggle between Person 1 and Person 2
- **First Game Only**: If you change the picker on the first game, ALL subsequent games alternate from that choice

---

## Managing Odds

### Accepting New Odds

When you sync and odds have changed, you'll see "New Spread" notifications:

1. **Review the Change**: New spread is shown with comparison to current (e.g., "New Spread: -7.5 (vs -9.5)")
2. **Warning Icon** ⚠️: Appears if spread changed by more than 3 points
3. **Accept**: Click the "Accept" button to update the odds in your database
4. **Accept All**: Click "Accept All New Spreads" to accept all changes at once

**Important**: New odds are NOT automatically applied - you must accept them!

### Manual Odds Entry

You can manually enter or adjust odds for any game:

#### Edit Spread
1. Click the large **✎** button in the upper right of the game card
2. Enter the spread for Team 1 (negative means Team 1 is favored)
3. Click OK

#### Edit Over/Under
1. Click the small **✎** button next to the O/U line
2. Enter the total points line
3. Click OK

**Use Case**: Enter odds before the API has them available, or override API odds with your preferred lines.

---

## Tracking Results

### Leaderboard

The leaderboard at the top shows current standings:
- **Wins/Losses/Pushes** for each person
- **Total Profit/Loss** in dollars
- **Win Percentage**

Updates automatically after each game completes!

### Game Results

When games finish, you'll see results next to each pick:
- **(W)** in green = Win
- **(L)** in red = Loss
- **(P)** in gray = Push (tie)

### Profit/Loss Calculation

- **Win**: You receive your bet amount × (100/odds if negative, or odds/100 if positive)
- **Loss**: You lose your bet amount
- **Push**: No money changes hands

**Example**: $50 bet at -110 odds → Win $45.45, Lose $50, or Push $0

### Review Picks

Click **Review / Edit Picks** to see a detailed breakdown:
- All picks for the series
- Current status of each pick
- Profit/loss per game
- Ability to edit or delete picks

---

## Series Management

### Viewing Series

All your series are organized in the left sidebar by season:
- Click any series to make it active
- Active series shows highlighted
- Games and picks update to match the selected series

### Editing a Series

1. **Right-click** on a series in the sidebar
2. Select **Edit Series...**
3. Update participant names or default bet amounts
4. Click **Finish**

**Note**: Editing default amounts only affects FUTURE picks, not existing ones.

### Deleting a Series

1. **Right-click** on a series in the sidebar
2. Select **Delete Series...**
3. Confirm deletion

**Warning**: This permanently deletes the series and ALL associated picks!

---

## Import/Export

Share your series with friends or backup your data using Import/Export.

### Exporting a Series

1. Select the series you want to export
2. Go to **Series → Export Series**
3. Choose a location and filename (e.g., `my-series.json`)
4. Click Save

The exported file contains:
- Series configuration
- All picks with bet amounts and odds
- Links to games via API IDs (portable across databases)

### Importing a Series

1. Go to **Series → Import Series**
2. Select the JSON file to import
3. Click Open

The app will:
- Create a new series with a new ID
- Link picks to games in your database via API IDs
- Preserve all pick data including who originated each pick

**Use Case**: Share your picks with a friend, or restore from backup.

---

## Tips & Tricks

### Bet Amount Management

**Quick Edit**: Click the bet amount (green dollar value) to change it for a specific game.

**Default Amounts**: Set different defaults for:
- Regular bowls (e.g., $20)
- CFP Playoffs (e.g., $50)
- Championship (e.g., $100)

Games automatically use the appropriate default based on their tier!

### Keyboard Shortcuts

- **Ctrl+S**: Settings (when implemented)
- **F5**: Sync data (when implemented)
- **Ctrl+E**: Export series (when implemented)

### Game Status

Watch for status indicators:
- **Gray**: Scheduled (game hasn't started)
- **Yellow**: In Progress (game is being played)
- **Green**: Final/Completed (scoring is final)

Only games marked as "Final" or "Completed" will be scored!

### Venue and Media Info

Each game card shows:
- 📍 **Venue**: Where the game is being played
- 📺 **Media**: What network is broadcasting

This helps you plan which games to watch!

### Best Practices

1. **Sync Regularly**: Check for score updates after each game day
2. **Review Before Accepting**: Always check new odds before accepting changes
3. **Lock Picks Early**: Make your picks before games start to avoid disputes
4. **Export Backups**: Export your series periodically as backup
5. **Use Manual Entry**: For early-season planning before official odds are available

---

## Troubleshooting

### No Games Showing Up

- **Solution**: Make sure you've synced data (click "Sync from APIs")
- **Check**: Your API key is correctly entered in Settings

### Odds Not Updating

- **Solution**: Betting lines may not be available yet - use manual entry
- **Check**: Sync again closer to game time

### Scores Not Calculating

- **Check**: Game status must be "Final" or "Completed"
- **Solution**: Sync again to get final scores
- **Manual**: Use Review/Edit Picks to manually update if needed

### Can't Accept New Odds

- **Check**: Make sure you have an active series selected
- **Solution**: Click on a series in the sidebar to activate it

---

## Support

For bugs, feature requests, or questions:

1. **GitHub Issues**: [github.com/anthropics/bowlbets](https://github.com/anthropics/bowlbets) (example)
2. **Check Logs**: Review `bowlbets.log` for error details
3. **API Status**: Verify College Football Data API is operational

---

## Version Information

**BowlBets Version**: 2.0
**Last Updated**: December 2024

---

**Enjoy your bowl season betting! May your picks be sharp and your profits be high!** 🏈💰
