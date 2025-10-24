# VocabVista - Word Frequency Visualizer

A web application that visualizes word frequency in text with color-coded insights. Rare words appear in red, and common words appear in green.

## Features

- Real-time text analysis
- Color-coded word frequency visualization
- Interactive heatmap display
- Word rarity classification (Very Rare, Rare, Uncommon, Common, Very Common)

## Tech Stack

- Backend: Flask (Python)
- Frontend: HTML, CSS, JavaScript
- API: Datamuse API for word frequency data
- Deployment: Render

## How It Works

1. User inputs text in the text area
2. Application sends text to backend API
3. Backend queries Datamuse API for word frequency data
4. Frequencies are mapped to colors (red = rare, green = common)
5. Frontend displays text with color-coded words based on frequency

## Deployment

This application is configured for deployment on Render using:

- Procfile for gunicorn configuration
- requirements.txt for Python dependencies
- Environment variable PORT for server port

## Local Development

```bash
pip install -r requirements.txt
flask run
```

Or with gunicorn:
```bash
gunicorn app:app
```