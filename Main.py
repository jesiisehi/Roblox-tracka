import requests
import time
from datetime import datetime

UIDS = ["2832056884", "3122609531", "1857023086", "21349438", "76333407",
        "3743862184", "96181741", "3954635046", "7179384789", "2801969876",
        "155361651", "140258990", "272629211", "2695915017", "19044882",
        "2590193767", "121823922", "197807548", "192649900", "15891007",
        "52392831","4198602015"]  # Add your user IDs here

PING_ROLE_ID = "@here"  # Replace with the actual role ID for pinging
ONLINE_WEBHOOK_URL = "https://discord.com/api/webhooks/1325325038190333962/--HuPRa4w4qPXKkiDONmNUed9odGtrys3Df5kV9xH1sOdtuWTdWKDcSJtWSQMMaPsYb1"
OFFLINE_WEBHOOK_URL = "https://discord.com/api/webhooks/1325325292180475917/VRBLZ40cz3leP-FfoIeBfPFVhY78kBu4H16nJbIFyDr16faKM_kVreT-LuSYlT95mQhH"
CHECK_INTERVAL = 90  # Time interval (in seconds) between checks
RATE_LIMIT_SLEEP = 30
ERROR_SLEEP = 10

URLS = {
    "checkPresence": "https://presence.roblox.com/v1/presence/users",
    "getUserInfo": "https://users.roblox.com/v1/users/{uid}"
}

previous_status = {uid: None for uid in UIDS}


def send_webhook(url, payload):
    """Send a webhook to the specified URL with the given payload."""
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 204:
            print(f"Webhook sent successfully at {datetime.now()}.")
        else:
            print(f"Failed to send webhook: {response.status_code} - {response.text}")
    except requests.RequestException as e:
        print(f"Error sending webhook: {e}")


def get_display_name(uid):
    """Get the display name of a user by UID."""
    url = URLS["getUserInfo"].format(uid=uid)
    try:
        response = requests.get(url)
        response.raise_for_status()
        user_data = response.json()
        return user_data.get("displayName", "Unknown User")
    except requests.RequestException as e:
        print(f"Error fetching user info for UID {uid}: {e}")
        return "Unknown User"


def check_user_presence():
    """Check the presence of all users."""
    payload = {"userIds": UIDS}
    try:
        response = requests.post(URLS["checkPresence"], json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            print(f"Rate limit reached. Waiting {RATE_LIMIT_SLEEP} seconds...")
            time.sleep(RATE_LIMIT_SLEEP)
        else:
            print(f"HTTP Error: {e}")
    except requests.RequestException as e:
        print(f"Error checking presence: {e}")
    time.sleep(ERROR_SLEEP)
    return None


def create_status_embed(display_name, uid, is_online, game_name=None, game_link=None):
    """Create a Discord embed for user status."""
    status = "🟢 Online" if is_online else "🔴 Offline"
    color = 0x008000 if is_online else 0xFF0000
    profile_link = f"https://www.roblox.com/users/{uid}/profile"

    fields = [
        {"name": "🆔User ID", "value": str(uid), "inline": True},
        {"name": "📊Status", "value": status, "inline": True},
        {"name": "📆Checked At", "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "inline": True},
        {"name": "🎮Currently Playing", "value": f"[{game_name}]({game_link})", "inline": False} if is_online and game_name and game_link else None,
        {"name": "🔗Profile Link", "value": f"[Click Here]({profile_link})", "inline": True} if is_online else None
    ]

    # Remove any None entries in the fields
    fields = [field for field in fields if field]

    return {
        "title": f"🎉Check User: {display_name}",
        "color": color,
        "fields": fields
    }


def process_user_presence(presence_info):
    """Process the presence information of a single user."""
    print(f"Debug: presence_info for user {presence_info['userId']}: {presence_info}")  # Debugging step

    uid = presence_info["userId"]
    is_online = presence_info['userPresenceType'] != 0
    display_name = get_display_name(uid)
    game_name = presence_info.get("lastLocation", None)
    game_link = f"https://www.roblox.com/games/{presence_info['placeId']}" if presence_info.get("placeId") else None

    if previous_status.get(uid) != is_online:  # Only send updates if the status has changed
        embed = create_status_embed(display_name, uid, is_online, game_name, game_link)
        webhook_url = ONLINE_WEBHOOK_URL if is_online else OFFLINE_WEBHOOK_URL
        send_webhook(webhook_url, {"embeds": [embed], "content": f"@here" if is_online else ""})
        previous_status[uid] = is_online


def main():
    """Main function to continuously check user presence."""
    print("Script started. Monitoring user statuses...")
    while True:
        presence_data = check_user_presence()
        if presence_data and "userPresences" in presence_data:
            for presence_info in presence_data["userPresences"]:
                process_user_presence(presence_info)
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()