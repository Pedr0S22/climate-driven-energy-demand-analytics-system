import os
import logging
from dotenv import load_dotenv, find_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

load_dotenv(find_dotenv())

# Keep full access just to be safe
SCOPES = ["https://www.googleapis.com/auth/drive"]
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))


def authenticate_gdrive():
    creds = None
    token_path = os.path.join(SCRIPT_DIR, "token.json")
    creds_path = os.path.join(SCRIPT_DIR, "credentials.json")

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(creds_path):
                raise FileNotFoundError("Missing credentials.json!")
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as token:
            token.write(creds.to_json())

    return build("drive", "v3", credentials=creds)


def upload_file_to_drive(service, file_path, drive_folder_id):
    file_name = os.path.basename(file_path)

    # Check for duplicates in the specific folder
    query = f"name='{file_name}' and '{drive_folder_id}' in parents and trashed=false"
    results = (
        service.files()
        .list(q=query, spaces="drive", fields="files(id, name)", supportsAllDrives=True, includeItemsFromAllDrives=True)
        .execute()
    )

    if results.get("files", []):
        logging.info(f"Drive: {file_name} already exists. Skipping.")
        return

    file_metadata = {"name": file_name, "parents": [drive_folder_id]}

    # Set proper mime types
    if file_name.endswith(".csv"):
        mime_type = "text/csv"
    elif file_name.endswith(".zip"):
        mime_type = "application/zip"
    else:
        mime_type = "application/octet-stream"

    media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
    logging.info(f"Drive: Uploading {file_name}...")
    service.files().create(body=file_metadata, media_body=media, fields="id", supportsAllDrives=True).execute()


def backup_project_data():
    logging.info("--- Starting Google Drive Backup ---")
    service = authenticate_gdrive()
    # drive folder ids
    weather_drive_folder_id = os.getenv("WEATHER_DRIVE_FOLDER_ID")
    energy_drive_folder_id = os.getenv("ENERGY_DRIVE_FOLDER_ID")

    # Safety check: ensure the IDs were actually loaded
    if not weather_drive_folder_id or not energy_drive_folder_id:
        raise ValueError("Missing Drive Folder IDs! Check your .env file.")

    # 1. Backup Energy CSVs directly
    raw_energy_dir = os.path.join(PROJECT_ROOT, "data", "raw", "energy")
    if os.path.exists(raw_energy_dir):
        logging.info("Backing up Energy data...")
        for file in os.listdir(raw_energy_dir):
            if file.endswith(".csv"):
                file_path = os.path.join(raw_energy_dir, file)
                upload_file_to_drive(service, file_path, energy_drive_folder_id)

    # 2. Backup Weather CSVs
    raw_weather_dir = os.path.join(PROJECT_ROOT, "data", "raw", "weather")
    if os.path.exists(raw_weather_dir):
        logging.info("Backing up Weather data...")
        for file in os.listdir(raw_weather_dir):
            if file.endswith(".csv"):
                file_path = os.path.join(raw_weather_dir, file)
                upload_file_to_drive(service, file_path, weather_drive_folder_id)

    logging.info("--- Backup Complete ---")


# serves only for testing purposes
# if __name__ == '__main__':
# Run this directly to test the backup
# backup_project_data()
