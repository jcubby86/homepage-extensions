# Bandwidth Monitor API

A minimal Python web server that fetches bandwidth statistics from an upstream XML source and returns formatted usage data.

## Configuration

Set the `BANDWIDTH_URL` environment variable to your bandwidth XML endpoint.

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set the bandwidth URL:
```bash
export BANDWIDTH_URL=https://your-server.com/xml/status
```

3. Run the server:
```bash
python app.py
```

The server will run on `http://localhost:5000`

## Docker

### Build the Docker image:
```bash
docker build -t jcubby86/xml-to-json .
```

### Run the container:
```bash
docker run -p 5000:5000 -e BANDWIDTH_URL=https://your-server.com/xml/status jcubby86/xml-to-json
```

### Or use Docker Compose:

Edit [docker-compose.yml](docker-compose.yml) and set your `BANDWIDTH_URL`, then:

```bash
docker-compose up
```

To run in detached mode:
```bash
docker-compose up -d
```

## Usage

### Get Bandwidth Statistics

```bash
curl http://localhost:5000/bandwidth
```

**Example Response:**
```json
{
  "used": "3.35 GB",
  "total": "2.93 TB",
  "free": "2.93 TB",
  "used_bytes": 3599023114,
  "total_bytes": 3221225472000,
  "free_bytes": 3217626448886,
  "usage_percent": 0.11
}
```

## API Endpoints

- **GET /bandwidth** - Get bandwidth usage statistics
  - Fetches data from `BANDWIDTH_URL` environment variable
  - Returns formatted bandwidth information with used/total/free in human-readable format
  - Also includes raw byte values and usage percentage

- **GET /health** - Health check endpoint
  - Returns: `{"status": "healthy"}`
