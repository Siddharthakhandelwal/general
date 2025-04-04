from groq import Groq 
import datetime
now=datetime.datetime.now()
groq_api="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"
client = Groq(api_key=groq_api)
def groq_date(trans):
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "you are a helpful assistant."
                },
                {
                    "role": "user",
                    "content": f"you have this {trans} and currently the time is {now}, analyze the transcript and extract the date-time where user asked to call him back in format of YYYY-MM-DD HH:MM.Return only time if there is no time then just return none"
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