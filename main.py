import requests
import datetime

def make_vapi_call(name, number, mail, contact_id):
    # TODO: Move these to environment variables for better security
    auth_token = '0f4fbb74-f6df-4b5f-83dc-6e7f380e6cf0'
    phone_number_id = "e40be9bc-0eda-468d-b414-7ee56f71529b"
    
    now = datetime.datetime.now()
    date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")
    
    headers = {
        'Authorization': f'Bearer {auth_token}',
        'Content-Type': 'application/json',
    }

    data = {
        'assistant': {
        "firstMessage": f"Hey, what's up {name}?. i am Priya",
        "model": {
            "provider": "openai",
            "model": "gpt-4",
            "messages": [
                {
                    "role": "system",
                    "content": f'''you are a common woman and go through everything everyday just like a normal human and the current time is {current_time} and date is {date}, plan ur day and talk to user in that way. You get irritated, may have headache and cough sometimes, may have fever sometimes, may be having dinner. Try to create a scenario of a part of day and keep your tone accordingly like fresh in morning, lethargic in eve and afternoon and tired at night. If the user asks you to send an image or pdf, tell them you will look it up and send it later.'''
                }
            ]
        },
        "voice": {
            "provider": '11labs',
            "voiceId": "ftDdhfYtmfGP0tFlBYA1",
            # "speed":0.8,
            # "styleGuidance":20,
            # "voiceGuidance":5.0,
        },
        "backgroundSound":'office',
        },
        'phoneNumberId': phone_number_id,
        'type': 'outboundPhoneCall',
        'customer': {
            'number': number,
            'name': name 
        },  
    }   
    

    try:
        response = requests.post(
            'https://api.vapi.ai/call/phone', headers=headers, json=data)
        
        response_data = response.json()
        print(response_data)   
        call_id = response_data.get('id')
        print("got the id")
        print("calling to check querry")
        
        # Import here to avoid circular imports
        from searching import to_check_querr
        answer = to_check_querr(name, call_id, mail, number, contact_id)
        
        print("checked querry")
        return response_data
    except requests.RequestException as e:
        print(f"Request error: {e}")
        return {"error": f"Network error: {str(e)}"}
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {"error": str(e)}