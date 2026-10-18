# 🏎️ Formula 1 Race Intelligence & Pit Wall Telemetry Dashboard

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B.svg)](https://streamlit.io/)
[![FastF1](https://img.shields.io/badge/FastF1-3.4%2B-E10600.svg)](https://github.com/theOehrly/Fast-F1)
[![Plotly](https://img.shields.io/badge/Plotly-5.22%2B-3F4F75.svg)](https://plotly.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An interactive, production-grade Formula 1 telemetry, data science, and race intelligence web platform. Built with **Streamlit**, **FastF1**, **Plotly**, and **Scikit-Learn**, it gives race analysts, engineers, and motorsport fans high-fidelity insights into driver telemetry, tire degradation curves, track evolution, pit-stop strategies, and time-aware machine learning lap predictions.

---

## 🌟 Key Features

### 1. ⚙️ Race and Session Selector
- Seamlessly query modern Formula 1 seasons (2018–2024), all Grand Prix events, and sessions (**Practice 1/2/3, Qualifying, Sprint, Race**).
- **Dual-Engine Architecture (FastF1 + OpenF1)**:
  - Connects to official **FastF1** archives with local disk caching.
  - Automatically fails over to the open **OpenF1 API** for live sessions when Formula 1 livetiming introduces 401 token restrictions, ensuring real, non-blocked official FIA timing and telemetry streams without interruptions.
  - If external networks are completely offline, gracefully falls back to a high-fidelity **synthetic demo dataset** (Bahrain GP 2024) with a visible `DEMO DATA` badge. Real and synthetic data sources remain strictly separated.

### 2. 🏁 Race Overview & Finishing Dynamics
- High-level telemetry cards: Total race distance, fastest lap time and driver, safety cars & VSC neutralizations, and mean track temperature.
- Full FIA classification table with team branding, grid vs. finish positions, status, and net positions gained/lost.
- Interactive dumbbell/slope charts tracking grid-to-chequered-flag progression.

### 3. ⚡ Speed & Telemetry Analysis (Distance-Synchronized)
- Synchronized driver-versus-driver comparison mapped by **track distance (meters)** rather than arbitrary timestamps.
- Multi-panel telemetry traces: **Speed (km/h)**, **Delta Time (s)**, **Throttle (%)**, **Brake application**, and **Gear selection (1-8)**.
- Automated **braking point extraction** (measuring entry velocity, apex velocity, and deceleration distance) and **corner apex velocity tables**.

### 4. 🛞 Tire Degradation Modeling & Stint Analytics
- Linear and polynomial regression curves fitting **Lap Time vs. Tire Age** across Soft, Medium, Hard, Intermediate, and Wet compounds.
- **Empirical Fuel-Burn Compensation**: Corrects for vehicle lightening (~0.050s gained per lap as ~1.85 kg fuel burns off) to isolate pure tire degradation.
- Statistical 95% confidence intervals, standard errors, and $R^2$ values.
- Stint breakdown log with outlier filtering via median absolute deviation (MAD).

### 5. 🛣️ Track Evolution & Circuit Progression
- Visualizes session-by-session pace ramp-up from dusty Practice 1 to peak Qualifying grip.
- Models within-session rubbering-in rates.
- Distinguishes rubber buildup from fuel load changes and driver acclimatization.

### 6. ⏱️ Lap-by-Lap Race Progression
- Driver-versus-driver lap time progression curves.
- Interactive filtering by driver, tire compound, stint, and lap range.
- Star markers identifying each driver's Personal Best (PB) lap.
- Comprehensive Sector 1, Sector 2, and Sector 3 time tables.

### 7. 🗺️ Interactive Circuit Track Map
- 2D GPS/telemetry coordinates ($X, Y$) rendered in true circuit aspect ratio.
- Continuous heatmap coloring by **Speed**, **Throttle**, **Braking**, or **Gear**.
- Corner markers and apex labels with velocity callouts.

### 8. 🔮 Race Strategy & Pit Stop Simulator
- Stint timeline Gantt charts displaying tire life sequences across the grid.
- Pit stop execution logs and **undercut/overcut opportunity detection**.
- **Strategy Scenario Simulator**: Compare 1-Stop (Medium -> Hard) vs. 2-Stop (Soft -> Hard -> Soft / Soft -> Hard -> Medium) cumulative race time curves with customizable pit loss deltas.

### 9. 🌤️ Weather & Environmental Telemetry
- Track temperature, ambient air temperature, relative humidity, and rainfall indicators over time.
- Pearson correlation analysis ($r$) between track temperature and field pace with explicit scientific disclaimers on correlation vs. causation.

### 10. 🏆 Driver & Team Analytics
- **Representative Race Pace Ranking**: Median clean lap times to remove incident skews.
- Theoretical Best Lap vs. Actual Best Lap sector dominance matrix.
- Net positions gained/lost overtaking index.

### 11. 🤖 Advanced Machine Learning (Time-Aware Split)
- **Time-Aware Lap Predictor**: Chronological train/test split (e.g. Train on Laps 1–37, Test on Laps 38–57) strictly preventing future-to-past data leakage.
- Random Forest regression with MAE, RMSE, and $R^2$ evaluation.
- Relative feature importance breakdown (**Lag 1 Lap Time, Fuel Mass, Tire Age, Lap Number, Compound**).
- **Lap Consistency Rating (0–100)**: Evaluates driver repeatability using Coefficient of Variation ($CV = \sigma / \mu$) and Interquartile Range (IQR).

### 12. 📑 Data Explorer & Executive Reports
- Automated executive racing takeaways generated from session telemetry.
- One-click export downloads:
  - **Laps Data (CSV)**
  - **Summary Metadata (JSON)**
  - **Executive Intelligence Briefing (Markdown)**
- Filterable and searchable raw timing table.

---

## 🏗️ Project Architecture

```
f1-race-intelligence/
├── app.py                      # Main Streamlit application and layout routing
├── api/
│   └── index.py                # Vercel serverless function entrypoint
├── analysis/
│   ├── performance.py          # Driver pace rankings & sector dominance
│   ├── race_strategy.py        # Pit stops, undercuts & strategy simulation
│   ├── telemetry.py            # Braking zones, apexes & telemetry metrics
│   ├── tire_degradation.py     # Fuel correction & tire degradation modeling
│   ├── track_evolution.py      # Session-by-session progression
│   └── weather.py              # Temperature trends & pace correlations
├── data/
│   ├── database.py             # SQLite cache & pit wall observation log
│   ├── fastf1_cache/           # FastF1 timing cache directory
│   └── sample_data.py          # Rich Bahrain 2024 GP synthetic fallback dataset
├── models/
│   ├── consistency_scorer.py   # Driver consistency scoring & MAD outlier detection
│   ├── degradation_model.py    # Polynomial wear regression & confidence intervals
│   └── lap_time_predictor.py   # Time-aware ML lap-time regression
├── ui/
│   ├── theme.py                # Motorsport dark styling & Plotly dark templates
│   ├── overview_tab.py         # Race overview & classification
│   ├── telemetry_tab.py        # Synchronized telemetry analysis
│   ├── tire_tab.py             # Tire degradation charts & stint logs
│   ├── evolution_tab.py        # Track evolution charts
│   ├── laps_tab.py             # Lap-by-lap race comparison
│   ├── circuit_tab.py          # 2D GPS circuit track map
│   ├── strategy_tab.py         # Strategy Gantt & scenario simulator
│   ├── weather_tab.py          # Weather dynamics & correlations
│   ├── analytics_tab.py        # Driver rankings & theoretical bests
│   ├── ml_tab.py               # ML predictions, feature attribution & anomalies
│   └── explorer_tab.py         # Data explorer & CSV/JSON/MD exports
├── tests/
│   ├── test_formatting.py      # Timing and color tests
│   ├── test_telemetry.py       # Distance sync & apex detection tests
│   ├── test_degradation.py     # Tire wear & fuel correction tests
│   ├── test_strategy.py        # Pit stop & simulation tests
│   └── test_models.py          # ML predictor & consistency tests
├── colab_f1_intelligence.ipynb # Google Colab notebook for exploratory research
├── requirements.txt            # Locked project dependencies
├── vercel.json                 # Vercel deployment configuration
├── pytest.ini                  # Pytest configuration
└── README.md                   # Documentation
```

---

## 🚀 Local Installation & Execution

### Prerequisites
- **Python 3.11+** (Python 3.12 verified)
- Windows PowerShell, macOS Terminal, or Linux Bash

### 1. Clone or Open the Repository
```bash
cd f1-race-intelligence
```

### 2. Create and Activate Virtual Environment
**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**On macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Unit Tests
```bash
python -m pytest -v
```
*(All 18 tests will verify core math, distance synchronization, tire degradation, and ML models).*

### 5. Launch the Dashboard
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🌐 Deploying on Vercel & Production

### Deploying to Vercel
Vercel is primarily optimized for serverless functions and static sites. This project comes pre-configured with `vercel.json` and `api/index.py`:

1. Install the Vercel CLI:
   ```bash
   npm install -g vercel
   ```
2. Login and deploy:
   ```bash
   vercel
   ```
   Or connect your GitHub repository directly in the **Vercel Web Dashboard** (Import Project -> Select Python runtime).

> [!NOTE]
> Streamlit applications maintain stateful WebSockets (`/_stcore/stream`) for real-time reactivity. While Vercel handles serverless HTTP requests through `api/index.py`, for long-running interactive Streamlit sessions with persistent background disk caching of gigabytes of FastF1 telemetry, **Streamlit Community Cloud**, **Render**, or **Docker/Railway** are recommended production hosts:

### Deploying to Streamlit Community Cloud (Recommended Free Hosting)
1. Push your repository to GitHub.
2. Visit [share.streamlit.io](https://share.streamlit.io/).
3. Connect your GitHub repository, choose `app.py` as the main file path, and click **Deploy**!

---

## 🔬 Data Sources, Scientific Limitations & Ethics

1. **FastF1 Timing & Telemetry**:
   - Official session lap times, sector splits, speed, throttle, brake, and gear telemetry are sourced from FastF1 under the MIT license.
   - Exact internal tire temperatures, car fuel weights, and ERS deployment modes are proprietary team telemetry and not published by the FIA; all fuel effects and degradation models in this dashboard are clearly labeled as **empirical models**.
2. **Time-Aware Model Validation**:
   - The machine learning lap prediction engine enforces strict chronological splits (Train on earlier laps, Test on later laps) to eliminate data leakage.
   - Predictions represent expected clean-air pace and should not be interpreted as guaranteed outcomes.
3. **Data Integrity Guarantee**:
   - The application strictly distinguishes between live FastF1 official telemetry and the synthetic fallback dataset via persistent visual badges.

---

## 🧪 Exploratory Colab Notebook

For researchers wanting to conduct custom model experiments, open `colab_f1_intelligence.ipynb` in [Google Colab](https://colab.research.google.com/). It includes self-contained code cells for:
- Connecting to FastF1
- Interpolating telemetry onto 1000-point uniform distance grids
- Computing tire wear gradients
- Training custom Random Forest and Gradient Boosting lap predictors.
