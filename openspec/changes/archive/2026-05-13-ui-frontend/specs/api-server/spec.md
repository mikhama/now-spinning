## MODIFIED Requirements

### Requirement: Flask API server entry point
The system SHALL provide a Flask API server in `api/main.py` that can be run with `python -m api.main`. The Flask app SHALL serve the `ui/` directory as static files at the root URL path, making `index.html`, `style.css`, `app.js`, and `images/` accessible to the browser.

#### Scenario: Start the API server
- **WHEN** the user runs `python -m api.main`
- **THEN** the Flask server SHALL start and listen for HTTP and WebSocket connections

#### Scenario: Serve the frontend HTML page
- **WHEN** a GET request is made to `/`
- **THEN** the server SHALL respond with the contents of `ui/index.html`

#### Scenario: Serve static CSS file
- **WHEN** a GET request is made to `/style.css`
- **THEN** the server SHALL respond with the contents of `ui/style.css`

#### Scenario: Serve static JS file
- **WHEN** a GET request is made to `/app.js`
- **THEN** the server SHALL respond with the contents of `ui/app.js`

#### Scenario: Serve cover image assets
- **WHEN** a GET request is made to `/images/30348842.jpeg`
- **THEN** the server SHALL respond with the image file from `ui/images/`
