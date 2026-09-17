# FightIQ

FightIQ is a multi-user MMA prediction, betting tracker, and analytics dashboard built with Django.

The project started as a personal prediction tracker and has evolved into a general-purpose web application where users can research fights, record predictions, track bets, and review their performance over time.

## Features

### User accounts
- Secure Django authentication
- User registration, login, and logout
- Private user-owned predictions, bets, and historical records
- Shared MMA data such as fighters, events, fights, and results
- Users cannot view or edit another user's private betting or prediction data

### MMA events and fights
- Create and manage promotions, events, fighters, and fight cards
- Reuse fighter records across multiple events
- Store fight information including weight class, fight order, fighter odds, and notes
- Shared fight results are used throughout the application

### Fight predictions
Users can make predictions directly from an event fight card.

Each prediction can contain:
- Predicted winner
- Method of victory
- Confidence level
- Striking notes
- Grappling notes
- Cardio notes
- Durability notes
- Betting notes
- Final reasoning

Predictions can be edited before a fight has a result. Once a result has been recorded, the prediction is locked to protect the integrity of the user's prediction history.

### Bet tracking
Users can track their own bets without using Django Admin.

Currently supported single-bet markets include:
- Fight Winner
- Method of Victory
- Goes the Distance / Does Not Go the Distance

Each bet can store:
- Fight
- Market
- Selection
- Decimal odds
- Stake in units
- Outcome
- Notes

Pending bets can be edited or deleted by their owner. Settled bets are locked.

### Automatic bet settlement
FightIQ automatically settles supported bets from the official fight result.

Examples:
- Fight Winner bet -> checks the winning fighter
- Method of Victory bet -> checks both fighter and method
- Goes the Distance -> checks whether the result was a decision

The settlement system also handles result changes correctly:

```text
No result
   ↓
PENDING

Result added
   ↓
WON / LOST / VOID

Result deleted
   ↓
PENDING

Corrected result added
   ↓
WON / LOST / VOID
```

A No Contest voids supported markets.

### Personal dashboard
Each logged-in user has a personalised dashboard showing information such as:
- Betting profit/loss
- Bet win rate
- Total bets
- Prediction accuracy
- Recent bets
- Recent predictions
- Upcoming events
- Personal record summary

Shared upcoming events are visible to all users, while personal statistics remain private.

### Analytics
FightIQ includes analytics for both historical picks and predictions created inside the application.

Analytics include:
- Total picks
- Wins and losses
- Win rate
- Profit/loss in units
- Prediction accuracy
- Promotion filtering
- Historical + current FightIQ data

Method prediction accuracy is tracked separately from winner-based betting profit/loss.

### Historical spreadsheet import
Historical prediction data can be imported from `.xlsx` files using a Django management command.

Example:

```bash
python manage.py import_historical_picks my_picks.xlsx \
    --promotion "UFC" \
    --username kasper
```

Historical records are linked to the selected user and can be included in analytics.

There is also a utility for creating fighter records from historical picks.

## Tech Stack

- Python
- Django 5.2
- SQLite for local development
- HTML
- CSS
- JavaScript
- openpyxl for spreadsheet imports
- Git / GitHub

The application is currently developed locally on Linux.

## Project Structure

```text
FightIQ/
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── ...
│
├── predictions/
│   ├── management/
│   │   └── commands/
│   ├── migrations/
│   ├── static/
│   │   └── predictions/
│   │       └── js/
│   ├── templates/
│   │   ├── predictions/
│   │   └── registration/
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── signals.py
│   ├── urls.py
│   └── views.py
│
├── manage.py
└── README.md
```

## Core Data Model

FightIQ separates shared MMA information from private user information.

### Shared data
- `Fighter`
- `Event`
- `Fight`
- `Result`

### User-owned data
- `Prediction`
- `HistoricalPick`
- `Bet`
- `BetSelection`

This allows multiple users to analyse the same fight card while keeping their predictions, betting history, and analytics private.

## Local Installation

### 1. Clone the repository

```bash
git clone git@github.com:kasper7001/FightIQ.git
cd FightIQ
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

If a `requirements.txt` file is present:

```bash
pip install -r requirements.txt
```

Otherwise install the current main dependencies:

```bash
pip install django openpyxl
```

### 4. Apply migrations

```bash
python manage.py migrate
```

### 5. Create an administrator account

```bash
python manage.py createsuperuser
```

### 6. Start the development server

```bash
python manage.py runserver
```

Then open:

```text
http://127.0.0.1:8000/
```

## Useful Development Commands

Check the Django project:

```bash
python manage.py check
```

Create migrations:

```bash
python manage.py makemigrations
```

Apply migrations:

```bash
python manage.py migrate
```

Run the server:

```bash
python manage.py runserver
```

Create an admin account:

```bash
python manage.py createsuperuser
```

Reset a user's password:

```bash
python manage.py changepassword <username>
```

## Current User Flow

### Predictions

```text
Login
  ↓
Events
  ↓
Choose Event
  ↓
Choose Fight
  ↓
Make / Edit Prediction
  ↓
Fight Result
  ↓
Prediction Analytics
```

### Bets

```text
Login
  ↓
Bets
  ↓
Add Bet
  ↓
Select Fight + Market + Odds
  ↓
Pending Bet
  ↓
Fight Result
  ↓
Automatic Settlement
  ↓
Personal P/L
```

## Security and Data Integrity

FightIQ currently includes several protections designed to keep multi-user data separated and historical records trustworthy.

Examples include:
- Login required for private pages
- User-specific database filtering
- Ownership checks when editing/deleting bets
- Cross-user URLs return 404 rather than exposing private objects
- Predictions locked after a fight result exists
- Settled bets cannot be edited or deleted
- Selection validation ensures a chosen fighter belongs to the selected fight
- Backend validation is used in addition to JavaScript
- CSRF protection through Django forms
- Automatic re-settlement when fight results change
- Bets reset to pending when a fight result is deleted

## Current Development Status

The core multi-user system is working.

Completed areas include:
- Authentication
- Shared MMA database
- Event and fight pages
- User predictions
- User betting tracker
- Multiple betting markets
- Automatic settlement
- Bet editing and deletion
- Historical spreadsheet import
- Promotion-specific analytics
- Personal dashboard
- Admin tooling

## Planned Features

Future improvements may include:
- Accumulator / parlay bets
- Additional prop markets
- Round betting
- Over/under round totals
- Improved event and fight research pages
- User-facing historical import
- CSV export
- Better charts and analytics
- More advanced dashboard filtering
- Search
- PostgreSQL
- Production deployment
- API support
- Improved mobile UI
- Audit logging and additional security hardening

## Why FightIQ?

FightIQ is intended to be more than a basic picks list.

The aim is to combine:
- MMA research
- Fight predictions
- Betting records
- Historical performance
- User-specific analytics

into one application.

It also serves as an ongoing software engineering project focused on Django development, data modelling, access control, automation, analytics, and secure multi-user application design.

---

Built as an ongoing MMA prediction and analytics project.
