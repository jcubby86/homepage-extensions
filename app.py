from flask import Flask, jsonify
from flask_caching import Cache
import requests
import xmltodict
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
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
def get_bandwidth():
    racknerd_base_url = os.getenv("RACKNERD_BASE_URL")
    racknerd_key = os.getenv("RACKNERD_KEY")
    racknerd_hash = os.getenv("RACKNERD_HASH")

    if not racknerd_base_url or not racknerd_key or not racknerd_hash:
        logger.error("Missing required environment variables: RACKNERD_BASE_URL, RACKNERD_KEY, or RACKNERD_HASH")
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
                    "bandwidth": parse_racknerd_data(json_data["bw"]),
                    "memory": parse_racknerd_data(json_data["mem"]),
                    "disk": parse_racknerd_data(json_data["hdd"]),
                    "ip_address": json_data["ipaddress"],
                    "status": json_data["status"],
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


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    logger.info("Starting RackNerd Homepage API server on port 5000")
    app.run(host="0.0.0.0", port=5000)
