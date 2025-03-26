import requests
import time
from send_mail import send_mail
from groqmodel import groq_suum
from whatsapp import create_pdf, send_image
from groq_image import groq_image
from search_download import main
from groq_date import groq_date
from supabase_general import update_callback_time, update_summary

def groq_trans_querr(trans):
    groq_api = "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"
    
    from groq import Groq
    client = Groq(api_key=groq_api)

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "you are a helpful assistant."
            },
            {
                "role": "user",
                "content": f"you have this {trans}, analyze the transcript and just return the question or querry that user asked and my answer was that i'll send hium later on. If there is multiple queries then try to combine them in one querry and then return. You need to just return a question which user asked and required internet connection to answer just return them and if there is no actual querry then return none."
            }
        ],
        model="llama-3.3-70b-versatile",
        temperature=0.5,
        max_completion_tokens=1024,
        top_p=1,
        stop=None,
        stream=False,
    )

    # Print the completion returned by the LLM.
    print(chat_completion.choices[0].message.content)
    return chat_completion.choices[0].message.content

def crawl_web(querry):
    from firecrawl import FirecrawlApp
    from groq import Groq
    import tiktoken
    
    app = FirecrawlApp(api_key="fc-cffd0abdf63f46c0b029afd6d25c92bc")
    groq_api = "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"
    search_engine = "AIzaSyDMS2uBldD8l3xhT-B-5Etza0MLP26L3L0"
    engine_id = "a49a4c9e1acce490d"
    tokenizer = tiktoken.get_encoding("cl100k_base") 
    client = Groq(api_key=groq_api)

    def groq_summarize(data, querry):
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "you are a helpful assistant."
                },
                {
                    "role": "user",
                    "content": f"you have this {data}, summarize it according to user querry, {querry} and try to extract and return the valuable info"
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.5,
            max_completion_tokens=1024,
            top_p=1,
            stop=None,
            stream=False,
        )

        # Print the completion returned by the LLM.
        print(chat_completion.choices[0].message.content)
        return chat_completion.choices[0].message.content
        
    url = "https://www.googleapis.com/customsearch/v1"
    para = {
        'q': querry,
        'key': search_engine,
        'cx': engine_id,
    }
    response = requests.get(url, params=para)
    results = response.json()
    
    if 'items' in results:
        target_url = results['items'][0]['link']
        print(f"Found URL: {target_url}")
        scrape_result = app.scrape_url(target_url, params={'formats': ['markdown', 'html']})
        data = scrape_result['markdown']
        tokens = tokenizer.encode(data)

        # Keep only the first 5000 tokens
        trimmed_tokens = tokens[:5000]
        trimmed_text = tokenizer.decode(trimmed_tokens)

        print(f"Original tokens: {len(tokens)}, Trimmed tokens: {len(trimmed_tokens)}")
        data = groq_summarize(trimmed_text, querry)
        print(data)
        return data
    return "No relevant information found."

def to_check_querr(name, call_id, mail, number, contact_id):
    auth_token = '0f4fbb74-f6df-4b5f-83dc-6e7f380e6cf0'
    url = f"https://api.vapi.ai/call/{call_id}"
    headers = {
        'Authorization': f'Bearer {auth_token}',
        'Content-Type': 'application/json',
    }
    
    # Add timeout and max retries
    max_retries = 20  # Adjust as needed
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            response = requests.get(url, headers=headers)
            trans = response.json()
            
            if 'monitor' in trans and 'listenUrl' in trans['monitor']:
                print(f"Listen URL: {trans['monitor']['listenUrl']}")
            
            if 'transport' in trans:
                print(f"Transport: {trans['transport']}")
                
            print(f"Call status: {trans['status']}")
            
            if trans['status'] == 'ended':
                try:
                    transcript = trans['transcript']
                    print("Summarizing call...")
                    data = groq_suum(transcript)
                    
                    print("Checking for callback time...")
                    call_back = groq_date(transcript)
                    
                    if mail:
                        print("Sending email summary...")
                        send_mail(data, mail, "Summary")
                    
                    print("Updating summary in database...")
                    if contact_id:
                        update_summary(contact_id, data)
                    
                    if call_back and ("none" not in call_back.lower() and "None" not in call_back):
                        print(f"Found callback time: {call_back}")
                        update_callback_time(contact_id, call_back)
                    
                    print("Creating and sending PDF summary...")
                    create_pdf(number, data)
                    
                    print("Checking for queries...")
                    querry = groq_trans_querr(transcript)
                    
                    print("Checking for image requests...")
                    image_querry = groq_image(transcript)
                    
                    print(f"Query detected: {querry}")
                    
                    # Handle image query if exists
                    if image_querry != "None":
                        print(f"Processing image query: {image_querry}")
                        main(image_querry)
                        array = send_image(number)
                        if mail:
                            send_mail(data, mail, "Documents that you asked for", array)
                    
                    # Handle web query if exists
                    if querry != "None":
                        try:
                            print("Web scrapping for query...")
                            answer = crawl_web(querry)
                            print("Answer found")
                            querry_answer = "You asked me a question on call and I have found the answer for you. The answer is: " + answer
                            if mail:
                                send_mail(querry_answer, mail, "Query Answer")
                            create_pdf(number, querry_answer)
                            return answer
                        except Exception as e:
                            print(f"Error processing query: {e}")
                            return None
                    
                    return "Success"
                except Exception as e:
                    print(f"An error occurred: {e}")
                    return f"Error occurred: {str(e)}"
            
            # If call is still in progress, wait before checking again
            time.sleep(10)  # Wait 10 seconds before checking again
            retry_count += 1
            
        except Exception as e:
            print(f"Error checking call status: {e}")
            return f"Error checking call status: {str(e)}"
    
    return "Timeout: Call status check exceeded maximum retries"