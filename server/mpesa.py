import requests
import base64
import datetime
import os
import json

MPESA_AUTH_URL = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
MPESA_STK_PUSH_URL = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

def get_access_token():
    consumer_key = os.getenv("MPESA_CONSUMER_KEY", "").strip()
    consumer_secret = os.getenv("MPESA_CONSUMER_SECRET", "").strip()

    print(f"DEBUG: Loaded MPESA_CONSUMER_KEY: {'*' * (len(consumer_key) - 5) + consumer_key[-5:] if consumer_key else 'NOT SET'}")
    print(f"DEBUG: Loaded MPESA_CONSUMER_SECRET: {'*' * (len(consumer_secret) - 5) + consumer_secret[-5:] if consumer_secret else 'NOT SET'}")

    if not consumer_key or not consumer_secret:
        print("ERROR: Missing MPESA credentials in environment.")
        return None

    try:
        response = requests.get(MPESA_AUTH_URL, auth=(consumer_key, consumer_secret))
        print(f"M-Pesa Access Token API Status Code: {response.status_code}")
        print(f"M-Pesa Access Token API Raw Response Text: {response.text}")
        response.raise_for_status()
        return response.json().get("access_token")
    except requests.exceptions.RequestException as e:
        print(f"Access Token Request Error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Access Token JSON Decode Error: {e}")
        return None

def lipa_na_mpesa_online(phone_number, amount):
    access_token = get_access_token()
    if not access_token:
        print("Failed to get access token. Aborting STK Push.")
        return {"error": "Failed to get access token"}

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    business_short_code = os.getenv("MPESA_BUSINESS_SHORT_CODE")
    passkey = os.getenv("MPESA_PASS_KEY")
    callback_url = os.getenv("BASE_CALLBACK_URL") + "/api/mpesa/callback"

    if not business_short_code or not passkey or not callback_url:
        return {"error": "Missing MPESA configuration in .env"}

    try:
        business_short_code = int(business_short_code)
        amount = int(amount)
    except ValueError:
        return {"error": "Invalid shortcode or amount"}

    phone = str(phone_number)
    if phone.startswith("07") or phone.startswith("01"):
        phone = "254" + phone[1:]
    elif phone.startswith("+254"):
        phone = phone[1:]

    password = base64.b64encode(
        f"{business_short_code}{passkey}{timestamp}".encode()
    ).decode()

    payload = {
        "BusinessShortCode": business_short_code,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": business_short_code,
        "PhoneNumber": phone,
        "CallBackURL": callback_url,
        "AccountReference": "CompanyXLTD",
        "TransactionDesc": "Payment of X",
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(MPESA_STK_PUSH_URL, json=payload, headers=headers)
        print("STK Push API Status Code:", response.status_code)
        print("STK Push API Raw Response Text:", response.text)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"STK Push Request Error: {e}")
        return {"error": str(e)}
