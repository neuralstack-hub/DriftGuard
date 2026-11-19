# Beijing PM2.5 Dataset

## Source & Attribution
- **Dataset**: Beijing PM2.5 Data Set
- **Repository**: [UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/381/beijing+pm2+5+data)
- **DOI**: `10.24432/C5JS49`
- **Citation**: Chen, S. (2015). *Beijing PM2.5* [Dataset]. UCI Machine Learning Repository.
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Original File**: `PRSA_data_2010.1.1-2014.12.31.csv` (43,824 hourly observations from Jan 1, 2010 to Dec 31, 2014)

## How to Download
Run the provided download script from the project root:
```bash
python scripts/download_dataset.py
```
This downloads the official archive from UCI and extracts `PRSA_data_2010.1.1-2014.12.31.csv` into `data/raw/`.

## Schema & Features
| Column | Role | Type | Description |
| :--- | :--- | :--- | :--- |
| `No` | Row ID (dropped) | Integer | Sequential row number |
| `year` | Feature | Integer | Year of observation (2010–2014) |
| `month` | Feature | Integer | Month of year (1–12) |
| `day` | Feature | Integer | Day of month (1–31) |
| `hour` | Feature | Integer | Hour of day (0–23) |
| `pm2.5` | **Target** | Float/Int | PM2.5 concentration (ug/m³) from US Embassy in Beijing (`NA` for missing) |
| `DEWP` | Feature | Float/Int | Dew Point (°C) |
| `TEMP` | Feature | Float/Int | Temperature (°C) |
| `PRES` | Feature | Float/Int | Atmospheric Pressure (hPa) |
| `cbwd` | Feature | Categorical | Combined wind direction (`NE`, `NW`, `SE`, `cv`) |
| `Iws` | Feature | Float | Cumulated wind speed (m/s) |
| `Is` | Feature | Integer | Cumulated hours of snow |
| `Ir` | Feature | Integer | Cumulated hours of rain |
