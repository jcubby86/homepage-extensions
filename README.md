# Homepage Extensions

A Flask API server that provides custom service integrations for [Homepage](https://gethomepage.dev/), aggregating statistics from multiple services including RackNerd VPS, Manyfold, BookStack, and LLDAP.

## Configuration

Set the following environment variables based on which services you want to use:

### RackNerd
- `RACKNERD_BASE_URL` - RackNerd API base URL
- `RACKNERD_KEY` - RackNerd API key
- `RACKNERD_HASH` - RackNerd API hash

### Manyfold
- `MANYFOLD_BASE_URL` - Manyfold instance URL
- `MANYFOLD_CLIENT_ID` - OAuth application client ID
- `MANYFOLD_CLIENT_SECRET` - OAuth application client secret
- `MANYFOLD_SCOPES` - OAuth scopes (defaults to "read")

### BookStack
- `BOOKSTACK_BASE_URL` - BookStack instance URL
- `BOOKSTACK_API_TOKEN` - BookStack API token

### LLDAP
- `LDAP_SERVER_URL` - LLDAP server hostname/IP
- `LDAP_PORT` - LLDAP port (defaults to 3890)
- `LDAP_QUERY_BIND` - Bind DN (e.g., `uid=admin,ou=people,dc=example,dc=com`)
- `LDAP_QUERY_PASSWORD` - Bind password
- `LDAP_BASE_DN` - Base DN for searches (e.g., `dc=example,dc=com`)

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export RACKNERD_BASE_URL=https://your-racknerd-server.com
export RACKNERD_KEY=your_key
export RACKNERD_HASH=your_hash
# ... set other variables as needed
```

3. Run the server:
```bash
python app.py
```

The server will run on `http://localhost:5000`

## Docker

### Build the Docker image:
```bash
docker build -t homepage-extensions .
```

### Run the container:
```bash
docker run -p 5000:5000 \
  -e RACKNERD_BASE_URL=https://your-server.com \
  -e RACKNERD_KEY=your_key \
  -e RACKNERD_HASH=your_hash \
  homepage-extensions
```

### Or use Docker Compose:

Edit [docker-compose.yml](docker-compose.yml) and set your environment variables, then:

```bash
docker-compose up
```

To run in detached mode:
```bash
docker-compose up -d
```

## API Endpoints

### GET /racknerd
Get VPS statistics from RackNerd including bandwidth, memory, and disk usage.

**Example Response:**
```json
{
  "bandwidth": {
    "used": "3.35 GB",
    "total": "2.93 TB",
    "free": "2.93 TB",
    "used_bytes": 3599023114,
    "total_bytes": 3221225472000,
    "free_bytes": 3217626448886,
    "usage_percent": 0.11
  },
  "memory": {
    "used": "512.00 MB",
    "total": "2.00 GB",
    "free": "1.50 GB",
    "used_bytes": 536870912,
    "total_bytes": 2147483648,
    "free_bytes": 1610612736,
    "usage_percent": 25.0
  },
  "disk": {
    "used": "10.50 GB",
    "total": "50.00 GB",
    "free": "39.50 GB",
    "used_bytes": 11274289152,
    "total_bytes": 53687091200,
    "free_bytes": 42412802048,
    "usage_percent": 21.0
  },
  "ip_address": "192.168.1.100",
  "status": "online"
}
```

### GET /manyfold
Get statistics from Manyfold including models, creators, and collections counts.

**Example Response:**
```json
{
  "models": 150,
  "creators": 45,
  "collections": 12
}
```

### GET /bookstack
Get statistics from BookStack including books and pages counts.

**Example Response:**
```json
{
  "total_books": 25,
  "total_pages": 320
}
```

### GET /ldap
Get user and group counts from LLDAP.

**Example Response:**
```json
{
  "users": 7,
  "groups": 6
}
```

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

## Caching

All endpoints (except `/health`) use a 1-hour cache to reduce load on upstream services.
