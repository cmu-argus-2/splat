# SPLAT Protocol Web Interface (Flask)

A Flask-based web application for unpacking and packing SPLAT (Struct Packed Lightweight Argus Telemetry) protocol messages.

## Project Structure

```
splat_web/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── static/                # Static files
│   ├── css/
│   │   └── style.css     # Stylesheet
│   └── js/
│       └── main.js       # JavaScript functionality
└── templates/             # HTML templates
    └── index.html        # Main page template
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure the `splat` package is available in your Python path.

## Running the Application

### Development Mode

```bash
python app.py
```

The server will start at `http://localhost:5000`

### Production Mode

For production, use a WSGI server like Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

Or with uWSGI:

```bash
pip install uwsgi
uwsgi --http 0.0.0.0:5000 --wsgi-file app.py --callable app --processes 4 --threads 2
```

## Features

- **Unpack Binary Data**: Decode hex-encoded SPLAT protocol messages
- **Pack Data to Binary**: Create binary messages from report/command data
- **Search & Filter**: Search through variables and arguments
- **Real-time Validation**: Instant feedback on packing/unpacking operations
- **Responsive Design**: Works on desktop and mobile devices

## API Endpoints

- `GET /` - Main web interface
- `GET /api/reports` - List all available reports
- `GET /api/commands` - List all available commands
- `POST /api/unpack` - Unpack hex data
- `POST /api/pack` - Pack data to binary

## Configuration

The Flask app can be configured through environment variables:

- `FLASK_ENV`: Set to `development` or `production`
- `FLASK_DEBUG`: Set to `1` for debug mode (auto-reload on changes)

Example:
```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
python app.py
```

## Development

### File Organization

- **app.py**: Contains all Flask routes and business logic
- **templates/index.html**: HTML structure using Jinja2 templating
- **static/css/style.css**: All styling and responsive design
- **static/js/main.js**: Client-side JavaScript for API calls and UI updates

### Adding New Features

1. Add backend logic to `app.py`
2. Update frontend in `templates/index.html`
3. Add styling to `static/css/style.css`
4. Implement client-side logic in `static/js/main.js`

## Browser Compatibility

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)
