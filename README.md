# HabitOS — Health Habit Adherence Analyzer

A full-stack behavioral analytics application that helps individuals and households track, measure, and improve daily health habits through data-driven insights and real-time dashboards.

---

## Live App
🔗 **https://habitos-3ztptyssxhde6xpfz4k9zq.streamlit.app/**

> Try it instantly — no sign up needed. Click **Household Demo** or **Individual Demo** on the login page to explore with real data.

---

## Problem

Most people start health routines — gym, water intake, sleep, vitamins — but struggle to stay consistent. The core challenges are:

- **No accountability** — habits are tracked mentally, not systematically
- **No visibility** — no way to see patterns, drop-offs, or progress over time
- **No social layer** — living with others but no shared tracking or friendly competition
- **Rigid tools** — existing apps lock you into predefined habits with no customization

In shared households specifically, there is no structured way to compare progress, motivate each other, or identify who needs support.

---

## Solution

HabitOS is a data-driven habit tracking and analytics system that combines individual accountability with household-level visibility.

It transforms raw daily logs into actionable behavioral insights — showing not just *what* you tracked, but *when* you dropped off, *which* habits you struggle with, and *how* you compare to your household.

This project bridges **behavioral data analysis**, **product thinking**, and **full-stack development**.

---

## Live Features

### 🔐 Authentication System
- Secure login and registration with hashed passwords
- Session management — stay logged in, sign out anytime
- New users get 4 default habits automatically on sign up

### 🧍 Individual Dashboard
- **Hero banner** with personal adherence stats
- **Habit radar chart** — adherence across all habits at a glance
- **Daily heatmap** — completion grid across the full tracking period
- **Per-habit gauges** — color-coded by performance threshold
- **Streak tracking** — current consecutive-day streaks per habit
- **Trend line** — daily adherence over time

### 🏠 Household Dashboard
- **Ranked leaderboard** — 🥇🥈🥉 with adherence bars and streak counts
- **Adherence gauges** — one per member, color coded
- **Habit Performance Matrix** — color-coded table across all members and habits
- **Daily trend lines** — multi-member adherence over time
- **Radar overlay** — all members on one chart for direct comparison
- **Individual heatmaps** — side-by-side for all members
- **Invite system** — unique 8-character code to add household members

### ✨ Custom Habits
- Add any habit with a custom name, icon, unit, and daily target
- Choose between binary (done/not done) or quantity tracking
- Delete habits you no longer need
- 16 icon options, 8 unit types

### 📝 Daily Logging
- Log any habit for any date
- Set completion status and actual value tracked
- Logs update in real time across all dashboards

### 📊 Analytics and Insights
- **Adherence rate** — percentage of completed habits over tracked period
- **Drop-off detector** — 3-day rolling average to spot consistency drops
- **Habit comparison** — which habits are easiest or hardest across the household
- **7-day quick stats** in sidebar — always visible

---

## Demo Data

The app ships with 3 weeks of real household data (April 2026) for **Ram**, **Mathi**, and **Guna** tracking gym, water, sleep, and vitamins daily.

| Member | Overall Adherence | Best Habit |
|--------|------------------|-----------|
| Ram    | 78.6%            | Gym       |
| Mathi  | 70.2%            | Sleep     |
| Guna   | 13.1%            | Vitamins  |

---

## Project Approach

### 1. Data Layer
- SQLite database with 5 normalized tables: users, households, household_members, habits, logs
- Upsert logic — re-logging the same date updates rather than duplicates
- Demo data seeds automatically on first launch from house_1.csv

### 2. Analytics Layer
- Adherence rate calculations per user, habit, and household
- Streak computation from ordered log history
- Rolling averages for trend smoothing
- Pivot tables for the performance matrix

### 3. Product Layer
- Multi-page Streamlit app with session-state routing
- Individual and household modes with fully separate dashboards
- Custom dark UI with CSS variables, Google Fonts, and Plotly dark theme

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit, custom CSS, Google Fonts (Syne + Space Mono) |
| Charts | Plotly — radar, heatmap, gauge, line, bar |
| Data processing | Pandas, NumPy |
| Database | SQLite |
| Auth | SHA-256 password hashing, session state |
| Language | Python 3.12 |
| Hosting | Streamlit Community Cloud |

---

## Key Insights from the Data

- **Guna shows classic drop-off behavior** — strong start, rapid decline after day 3, consistent low adherence at 13.1%
- **Ram maintains the highest consistency** — 78.6% overall, strongest in gym and water
- **Sleep is the hardest habit** across all members — lowest adherence relative to target
- **Vitamins have high variance** — some members perfect, others near zero
- **Household tracking creates accountability** — visible leaderboard motivates consistency

---

## File Structure

```
habitos/
├── app.py           # Main Streamlit app — routing, dashboards, charts
├── auth.py          # Login, register, onboarding, demo access pages
├── database.py      # SQLite backend — all DB operations and demo seed
├── requirements.txt # Python dependencies
└── house_1.csv      # Source data for demo household (Ram, Mathi, Guna)
```

---

## Outcome

Transformed a raw habit-tracking CSV into a fully deployed, multi-user analytics product that:

- Gives individuals **visibility** into their own behavioral patterns
- Creates **accountability** through household comparison and leaderboards
- Makes **drop-off analysis** actionable — not just what happened, but when and why
- Demonstrates an end-to-end **data → insight → product** workflow

---

## Future Enhancements

### 🔔 Smart Reminders
- Daily push notifications for incomplete habits
- Weekly summary email with adherence report

### 🎮 Gamification
- Points system and badges for streaks
- Household challenges — "Who can hit 90% this week?"

### 🔮 Predictive Analytics
- Identify users at risk of dropping off based on rolling trend
- Suggest optimal habit targets based on past performance

### ☁️ Cloud Database
- Migrate from SQLite to PostgreSQL via Supabase
- Persistent data across server restarts
- Support for larger households and longer history

### 📱 Mobile-Optimized UI
- Responsive layout for phone-first logging
- One-tap daily habit completion

### 🔗 Integrations
- Apple Health and Google Fit sync
- Notion or Google Sheets export
