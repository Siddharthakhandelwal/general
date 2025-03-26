import os
from supabase import create_client, Client
import datetime
import pytz  # For handling time zones
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("scheduler.log"),
                        logging.StreamHandler()
                    ])

# Supabase credentials
SUPABASE_URL = "https://mwytkzzzvtdwsscmxqgo.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im13eXRrenp6dnRkd3NzY214cWdvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MjU5NjQ2NiwiZXhwIjoyMDU4MTcyNDY2fQ.pM8de7Nyu71si4M9PLoKsbTGJxW_4ilZcNXBmkfndCQ"

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Function to update only the summary
def update_summary(contact_id, summary):
    """
    Updates only the summary for a given contact ID.
    
    :param contact_id: ID of the contact to update
    :param summary: Summary of the call
    """
    if not contact_id:
        logging.warning("No contact_id provided, cannot update summary")
        return
        
    response = (
        supabase.table("general_contacts")
        .update({"summary": summary, "called": True})  # Also mark as called
        .eq("id", contact_id)
        .execute()
    )

    if response.data:
        logging.info(f"Summary updated successfully for Contact ID: {contact_id}")
    else:
        logging.warning(f"Failed to update summary. Response: {response}")

# Function to update only the callback time
def update_callback_time(contact_id, callback_time):
    """
    Updates only the callback time for a given contact ID.
    
    :param contact_id: ID of the contact to update
    :param callback_time: Exact callback time in 'YYYY-MM-DD HH:MM' format (UTC)
    """
    if not contact_id:
        logging.warning("No contact_id provided, cannot update callback time")
        return
        
    try:
        # Convert string input to datetime object and format it correctly
        callback_time_obj = datetime.datetime.strptime(callback_time, "%Y-%m-%d %H:%M")
        callback_time_iso = callback_time_obj.isoformat()

        response = (
            supabase.table("general_contacts")
            .update({"callback_time": callback_time_iso})
            .eq("id", contact_id)
            .execute()
        )

        if response.data:
            logging.info(f"Callback time updated successfully for Contact ID: {contact_id}")
        else:
            logging.warning(f"Failed to update callback time. Response: {response}")

    except ValueError:
        logging.error("Invalid date format. Please enter time in 'YYYY-MM-DD HH:MM' format.")

# Function to get timezone from country code
def get_timezone(country_code):
    country_timezones = {
        "US": "America/New_York",  # Example: US → New York timezone
        "IN": "Asia/Kolkata",      # Example: India → Kolkata timezone
        "UK": "Europe/London",     # Example: UK → London timezone
    }
    return country_timezones.get(country_code, "UTC")  # Default to UTC if unknown

# Function to check if the current time is daytime (8 AM to 6 PM)
def is_daytime(country_code):
    timezone = pytz.timezone(get_timezone(country_code))
    now = datetime.datetime.now(timezone).time()
    return datetime.time(8, 0) <= now <= datetime.time(18, 0)

# Function to fetch latest data from Supabase
def fetch_data(table_name):
    try:
        # Including 'called' column to filter out already called contacts
        response = supabase.table(table_name).select(
            "id, name, country_code, phone, email, date_time, called"
        ).is_('called', None).execute()
        return response.data if response.data else []
    except Exception as e:
        logging.error(f"Error fetching data: {e}")
        return []

# Custom sorting function
def sort_and_interleave(entries):
    with_datetime = [entry for entry in entries if entry.get('date_time')]
    without_datetime = [entry for entry in entries if not entry.get('date_time')]

    # Convert date_time strings to datetime objects
    for entry in with_datetime:
        if isinstance(entry['date_time'], str):
            entry['date_time'] = datetime.datetime.fromisoformat(entry['date_time'])

    with_datetime.sort(key=lambda x: x['date_time'])

    result = []
    index_without = 0

    for entry in with_datetime:
        result.append(entry)
        if index_without < len(without_datetime):
            result.append(without_datetime[index_without])
            index_without += 1

    result.extend(without_datetime[index_without:])
    return result

# Main scheduler function
def schedule():
    # Import make_vapi_call here to avoid circular import
    from main import make_vapi_call
    
    table_name = "general_contacts"
    
    # Add a flag to control the loop
    running = True
    
    while running:
        try:
            # Fetch only uncalled contacts
            data = fetch_data(table_name)
            
            if not data:
                logging.info("No uncalled contacts found. Waiting before next check...")
                time.sleep(60)
                continue

            sorted_data = sort_and_interleave(data)
            current_utc_time = datetime.datetime.utcnow().replace(second=0, microsecond=0)

            for row in sorted_data:
                # Verify the contact is still uncalled (in case of race conditions)
                if row.get('called'):
                    continue

                name = row.get("name")
                number = f"{row.get('country_code', '')}{row.get('phone', '')}"
                mail = row.get("email")
                contact_id = row.get("id")
                country_code = row.get("country_code")
                contact_time = row.get("date_time")
                
                # Decision logic for calling
                should_call = False

                # If contact has a specific time
                if contact_time:
                    if isinstance(contact_time, str):
                        contact_time = datetime.datetime.fromisoformat(contact_time)
                    contact_time = contact_time.replace(second=0, microsecond=0)
                    should_call = contact_time == current_utc_time
                
                # If no specific time, check if it's daytime in contact's country
                elif is_daytime(country_code):
                    should_call = True

                # Make the call if conditions are met
                if should_call:
                    try:
                        # Attempt to make the call
                        logging.info(f"Initiating call to {name} ({number})")
                        call_result = make_vapi_call(name, number, mail, contact_id)
                        
                        # Mark as called if call is successful
                        if call_result and 'id' in call_result:
                            # Update happens in to_check_querr via make_vapi_call
                            logging.info(f"Call initiated successfully for {name}")
                        else:
                            logging.warning(f"Call failed for contact {contact_id}")
                    except Exception as e:
                        logging.error(f"Error calling {name}: {e}")

            logging.info("Waiting for next check...")
            time.sleep(60)  # Wait for 60 seconds before checking again

        except Exception as e:
            logging.error(f"An error occurred in scheduler: {e}")
            time.sleep(60)  # Wait before retrying in case of persistent error

    logging.info("Scheduler stopped.")