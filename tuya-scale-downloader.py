import logging
import json
from datetime import datetime, timedelta
import pytz
import os

from dotenv import load_dotenv

# NB Custom tuya_connector module required for correct behaviour on POST requests with parameters
# https://github.com/jsinkers/tuya-connector-python
from tuya_connector import TuyaOpenAPI, TUYA_LOGGER

load_dotenv()

# Read environment variables
API_ENDPOINT = os.environ.get('API_ENDPOINT')
ACCESS_ID = os.environ.get('ACCESS_ID')
ACCESS_KEY = os.environ.get('ACCESS_KEY')
DEVICE_ID = os.environ.get('DEVICE_ID')
BIRTHDATE = os.environ.get('BIRTHDATE')
DATA_FILE = os.environ.get('DATA_FILE')
DEBUG_LOGS = os.environ.get('DEBUG_LOGS', False)

# Initialize Tuya API connection
openapi = TuyaOpenAPI(API_ENDPOINT, ACCESS_ID, ACCESS_KEY)
openapi.connect()

# Enable debug log
if DEBUG_LOGS:
    TUYA_LOGGER.setLevel(logging.DEBUG)


# get a single page of scale history data
def get_scale_data_history(device_id, page_no=1, page_size=10, start_time=None):
    print(f"Retrieving page {page_no} of scale data history")
    params = {
        "page_no": page_no,
        "page_size": page_size
    }
    
    if start_time:
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time).replace(tzinfo=pytz.UTC)
        elif isinstance(start_time, datetime):
            start_time = start_time.replace(tzinfo=pytz.UTC)
        start_time_ms = int(start_time.timestamp() * 1000)
        params["start_time"] = start_time_ms

    response = openapi.get(f"/v1.0/scales/{device_id}/datas/history", params=params)
    if response.get('success'):
        return response['result']
    else:
        logging.error(f"Failed to get scale data history: {response}")
        return None

# retrieve all scale history data
def get_all_scale_data_history(device_id, page_size=10, start_time=None):
    """ 
    @param device_id: The device ID
    @param page_size: The number of records to retrieve per page
    @param start_time: The start time of the records to retrieve, as a string in ISO 8601 format
    """
    all_data = []
    page_no = 1
    total_pages = 1  # Initialize to ensure the loop runs at least once

    while page_no <= total_pages:
        result = get_scale_data_history(device_id, page_no, page_size, start_time)
        if result:
            print(f"Retrieved {len(result['records'])} records from page {page_no} of {total_pages}")
            all_data.extend(result['records'])  # Assuming 'data' contains the list of records
            total_pages = result.get('total', 1)  # Get total number of pages from the response
            page_no += 1
        else:
            break

    return all_data

# https://support.tuya.com/en/help/_detail/K9g77yt8rx4ii
# retrieve a scale analysis report
def get_analysis_report(device_id, data):
    # todo: if no resistance, then don't get report? 
    #data = convert_scale_record(data)
    #response = openapi._TuyaOpenAPI__request(path=f"/v1.0/scales/{device_id}/analysis-reports", method='PUT', params=data)
    response = openapi.post(path=f"/v1.0/scales/{device_id}/analysis-reports/", body=data, params=data)#, body=None)
    if response.get('success'):
        return response['result']
    else:
        logging.error(f"Failed to get analysis report for data ID {data}: {response}")
        return None

# helper to determine age at a given time (in ms since Unix epoch) based on birthd date
def age_at_time(time, birth_date):
    # parse birth date 
    birth_date = datetime.strptime(birth_date, "%Y-%m-%d")
    record_date = datetime.fromtimestamp(time / 1000)
    # Calculate the difference in years
    age = record_date.year - birth_date.year - ((record_date.month, record_date.day) < (birth_date.month, birth_date.day))
    return age

# helper to convert scale history record data into format for scale analysis report
def convert_scale_record(data):
    #data= { "height":178, "weight":78.3, "resistance":718, "age":26, "sex":1 }
    new_data = {
        "height": data["height"],
        "weight": data["wegith"],
        "resistance": data["body_r"],
        "age": age_at_time(data["create_time"], BIRTHDATE),
        "sex": 1 
    }
    print(new_data)
    return new_data

def load_existing_data(file_path):
    if os.path.exists(file_path):
        print(f"Loading existing data from {file_path}")
        with open(file_path, 'r') as file:
            return json.load(file)
    else:
        print(f"No existing data found at {file_path}")
    return []

def save_data(file_path, data):
    print(f"Saving data to {file_path}")
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def get_last_record_time(data):
    if data:
        last_record = max(data, key=lambda x: x['create_time'])   
        return datetime.fromtimestamp(last_record['create_time'] / 1000, tz=pytz.UTC)
    return None

def update_data():
    existing_data = load_existing_data(DATA_FILE)
    last_record_time = get_last_record_time(existing_data)
    # add 1 ms to last record time to avoid retrieving the same records
    if last_record_time:
        last_record_time += timedelta(milliseconds=1)
    
    new_data = get_all_scale_data_history(DEVICE_ID, start_time=last_record_time)
    
    if new_data:
        all_data = existing_data + new_data
        all_data = sorted(all_data, key=lambda x: x['create_time'])  # Ensure data is sorted by timestamp
        save_data(DATA_FILE, all_data)
        print(f"New records retrieved: {len(new_data)}")
    else:
        print("No new records retrieved.")

if __name__ == '__main__':
    update_data()
