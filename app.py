from flask import Flask, jsonify
from flask_caching import Cache
import requests
import xmltodict
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configure cache - simple in-memory cache with 1 hour timeout
app.config["CACHE_TYPE"] = "SimpleCache"
app.config["CACHE_DEFAULT_TIMEOUT"] = 3600  # 1 hour in seconds

cache = Cache(app)


def parse_racknerd_data(bw_string):
    values = [int(x) for x in bw_string.split(",")]
    total_bytes, used_bytes, free_bytes, percent = values

    def bytes_to_human(bytes_val):
        """Convert bytes to human readable format"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_val < 1024.0:
                return f"{bytes_val:.2f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.2f} PB"

    return {
        "used": bytes_to_human(used_bytes),
        "total": bytes_to_human(total_bytes),
        "free": bytes_to_human(free_bytes),
        "used_bytes": used_bytes,
        "total_bytes": total_bytes,
        "free_bytes": free_bytes,
        "usage_percent": percent,
    }


@app.route("/racknerd", methods=["GET"])
@cache.cached(timeout=3600)
def racknerd():
    racknerd_base_url = os.getenv("RACKNERD_BASE_URL")
    racknerd_key = os.getenv("RACKNERD_KEY")
    racknerd_hash = os.getenv("RACKNERD_HASH")

    if not racknerd_base_url or not racknerd_key or not racknerd_hash:
        logger.error(
            "Missing required environment variables: RACKNERD_BASE_URL, RACKNERD_KEY, or RACKNERD_HASH"
        )
        return (
            jsonify(
                {
                    "error": "RACKNERD_BASE_URL, RACKNERD_KEY, or RACKNERD_HASH environment variable not set"
                }
            ),
            500,
        )

    try:
        logger.info("Fetching RackNerd data")
        url = f"{racknerd_base_url}/api/client/command.php?key={racknerd_key}&hash={racknerd_hash}&action=info&bw=true&mem=true&hdd=true"
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        wrapped_xml = f"<root>{response.text.strip()}</root>"
        json_data = xmltodict.parse(wrapped_xml)["root"]

        logger.info("Successfully fetched and parsed RackNerd data")
        return (
            jsonify(
                {
                    "bandwidth": parse_racknerd_data(json_data.get("bw", "0,0,0,0")),
                    "memory": parse_racknerd_data(json_data.get("mem", "0,0,0,0")),
                    "disk": parse_racknerd_data(json_data.get("hdd", "0,0,0,0")),
                    "ip_address": json_data.get("ipaddress", None),
                    "status": json_data.get("status", None),
                }
            ),
            200,
        )

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch RackNerd data: {str(e)}")
        return jsonify({"error": f"Failed to fetch URL: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Failed to parse RackNerd data: {str(e)}")
        return jsonify({"error": f"Failed to parse data: {str(e)}"}), 500


@app.route("/manyfold", methods=["GET"])
@cache.cached(timeout=3600)
def manyfold():
    manyfold_base_url = os.getenv("MANYFOLD_BASE_URL")
    manyfold_client_id = os.getenv("MANYFOLD_CLIENT_ID")
    manyfold_client_secret = os.getenv("MANYFOLD_CLIENT_SECRET")
    manyfold_scopes = os.getenv("MANYFOLD_SCOPES", "read")

    if not manyfold_base_url or not manyfold_client_id or not manyfold_client_secret:
        logger.error(
            "Missing required environment variables: MANYFOLD_BASE_URL, MANYFOLD_CLIENT_ID, or MANYFOLD_CLIENT_SECRET"
        )
        return (
            jsonify(
                {
                    "error": "MANYFOLD_BASE_URL, MANYFOLD_CLIENT_ID, or MANYFOLD_CLIENT_SECRET environment variable not set"
                }
            ),
            500,
        )

    try:
        logger.info("Fetching Manyfold OAuth token")

        # Get OAuth token
        token_url = f"{manyfold_base_url}/oauth/token"
        token_data = {
            "grant_type": "client_credentials",
            "client_id": manyfold_client_id,
            "client_secret": manyfold_client_secret,
            "scope": manyfold_scopes,
        }

        token_response = requests.post(token_url, data=token_data, timeout=10)
        token_response.raise_for_status()
        token_json = token_response.json()
        access_token = token_json.get("access_token")

        if not access_token:
            logger.error("Failed to obtain access token from Manyfold")
            return jsonify({"error": "Failed to obtain access token"}), 500

        logger.info("Successfully obtained Manyfold OAuth token")

        headers = {
            "Authorization": f"Bearer {access_token}",
            "accept": "application/vnd.manyfold.v0+json",
        }

        models_url = f"{manyfold_base_url}/models"
        models_response = requests.get(models_url, headers=headers, timeout=10)
        models_response.raise_for_status()
        logger.info("Successfully fetched Manyfold models")

        creators_url = f"{manyfold_base_url}/creators"
        creators_response = requests.get(creators_url, headers=headers, timeout=10)
        creators_response.raise_for_status()
        logger.info("Successfully fetched Manyfold creators")

        collections_url = f"{manyfold_base_url}/collections"
        collections_response = requests.get(
            collections_url, headers=headers, timeout=10
        )
        collections_response.raise_for_status()
        logger.info("Successfully fetched Manyfold collections")

        return (
            jsonify(
                {
                    "models": models_response.json().get("totalItems", 0),
                    "creators": creators_response.json().get("totalItems", 0),
                    "collections": collections_response.json().get("totalItems", 0),
                }
            ),
            200,
        )

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch Manyfold data: {str(e)}")
        return jsonify({"error": f"Failed to fetch data: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Failed to process Manyfold data: {str(e)}")
        return jsonify({"error": f"Failed to process data: {str(e)}"}), 500


@app.route("/bookstack", methods=["GET"])
@cache.cached(timeout=3600)
def bookstack():
    bookstack_base_url = os.getenv("BOOKSTACK_BASE_URL")
    bookstack_api_token = os.getenv("BOOKSTACK_API_TOKEN")

    if not bookstack_base_url or not bookstack_api_token:
        logger.error(
            "Missing required environment variables: BOOKSTACK_BASE_URL or BOOKSTACK_API_TOKEN"
        )
        return (
            jsonify(
                {
                    "error": "BOOKSTACK_BASE_URL or BOOKSTACK_API_TOKEN environment variable not set"
                }
            ),
            500,
        )

    try:
        logger.info("Fetching BookStack data")
        headers = {"Authorization": f"Token {bookstack_api_token}"}

        books_url = f"{bookstack_base_url}/api/books"
        books_response = requests.get(books_url, headers=headers, timeout=10)
        books_response.raise_for_status()

        pages_url = f"{bookstack_base_url}/api/pages"
        pages_response = requests.get(pages_url, headers=headers, timeout=10)
        pages_response.raise_for_status()

        logger.info("Successfully fetched BookStack data")
        return (
            jsonify(
                {
                    "total_books": books_response.json().get("total", 0),
                    "total_pages": pages_response.json().get("total", 0),
                }
            ),
            200,
        )

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch BookStack data: {str(e)}")
        return jsonify({"error": f"Failed to fetch data: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Failed to process BookStack data: {str(e)}")
        return jsonify({"error": f"Failed to process data: {str(e)}"}), 500


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    logger.info("Starting RackNerd Homepage API server on port 5000")
    app.run(host="0.0.0.0", port=5000)
