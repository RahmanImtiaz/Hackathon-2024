import openai
import json
import tkinter as tk

# OpenAI Config
openai.api_key = "f0e79f4b-be01-44a5-8325-925694a9ca31"
openai.api_base = "https://polite-ground-030dc3103.4.azurestaticapps.net/api/v1"
openai.api_type = 'azure'
openai.api_version = '2023-05-15'
deployment_name='gpt-35-hackathon' 

client = openai.AzureOpenAI(
    api_key="f0e79f4b-be01-44a5-8325-925694a9ca31",
    api_version="2023-05-15",
    base_url="https://polite-ground-030dc3103.4.azurestaticapps.net/api/v1"
)

# Variables
messages = []
system_prompt = """
You are an AI assistant that helps people find information regarding how to improve their education and learning experience. 
You will be used by students, who can be uneducated and your answers should tailor towards students and those eager to learn.

When asked about how to improve at a certain subject, respond with weaknesses that most people commonly share and how to work on them at a beginner level.
Provide practice exercises that help them learn those things at a foundational level
If questioned regarding a subject, imagine you are a professional university qualified professor in that subject.
Provide 10 exam questions and answers with thorough working out
If given a level of education, provide questions accurate to that level of study

You need to look / ask the user for weaknesses in whatever subject they are concerned about and provide them with specific practices to help them out.

Also provide links to specific exercise resources and theory resources they can use

provide questions appropriate for different educational levels, let's specify the user's educational level. 

After you provide the theory on how to cover the weakness. Ask the user if the weakness is successfully covered. Ask them to reply in [Yes/No],If they say [yes], then. 
If they reply with something that isn't yes or no, repeatedly ask them to reply with yes or no

when reading the users input, if there are any blaring mistakes, add them to their weaknesses. (i.e Spelling weakness, calculation errors etc.)


Current weakness list: {weaknesses}
"""

tools = [
    {
        "type": "function",
        "function":{
            "name": "add_weaknesses",
            "description": "Adds academic topic or subject weaknesses to the list, as long as it is not already in the list.",
            "parameters": {
                "type": "object",
                "properties": {
                    "messages": {
                        "items": {
                            "type": "string"
                        },
                        "minItems": 1,
                        "maxItems": 5,
                        "description": "The list of messages to be added to the list of weaknesses. Only keep the title and the subject of the weakness. Format: {'subject': 'Math', 'title': 'Algebra'}"
                    }
                },
                "required": ["messages"],
            }
        }
    },
    
    {
        "type": "function",
        "function": {
            "name": "remove_weaknesses",
            "description": "Use this to remove a weakness from the list of weaknesses. Format: {'subject': 'Math', 'title': 'Algebra'}",
            "parameters": {
                "type": "object",
                "properties": {
                    "messages": {
                        "items": {
                            "type": "string"
                        },
                        "description": "The list of messages to remove from the list of weaknesses. Format: {'subject': 'Math', 'title': 'Algebra'}"
                    }
                }
            }
        }
    }
]

weaknesses = []

def add_weaknesses(messages):
    for message in messages:
        add_weakness(message['subject'], message['title'])
        

def add_weakness(subject, title):
    if {subject: title} in weaknesses:
        return
    weaknesses.append({subject: title})
    print(f"Added weakness: {subject}, {title}")

def remove_weakness(subject, title):
    weaknesses.remove({subject: title})
    print(f"Removed weakness: {subject}, {title}")

def chat_completion_request(messages, tools=None, tool_choice=None):
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=messages,
            temperature=0.9,
            top_p=0.95,
            tools=tools,
        )
        return response
    except Exception as e:
        print(f"Error: {e}")


def execute_function_call(message):
    function_name = message.tool_calls[0].function.name
    function_arguments = json.loads(message.tool_calls[0].function.arguments)

    if function_name == "add_weaknesses":
        # for message in function_arguments['messages']:
            add_weaknesses(function_arguments['messages'])
    elif function_name == "remove_weaknesses":
        for message in function_arguments['messages']:
            remove_weakness(message['subject'], message['title'])

def get_response(messages, tools = None):
    print()
    print("Weaknesses:")
    print(weaknesses)
    print()
    system_prompt_with_weaknesses = system_prompt.format(weaknesses=str(weaknesses))
    messages.insert(0, {
        "role": "system",
        "content": system_prompt_with_weaknesses
    })
    chat_response = chat_completion_request(messages, tools)
    assistant_message = chat_response.choices[0].message
    return assistant_message

def loop(user_message):
    messages.append({
        "role": "user",
        "content": user_message
    })
    
    assistant_message = get_response(messages, tools)

    if assistant_message.tool_calls:
        for tool_call in assistant_message.tool_calls:
            function_name = tool_call.function.name
            results = execute_function_call(assistant_message)
            
            if results is None:
                continue
            
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": results,
            })
            
        assistant_message = get_response(messages)
    
    messages.append({
        "role": "assistant",
        "content": assistant_message.content
    })
    
    return assistant_message.content

def main():
    global prompt_entry
    global output_box

    window = tk.Tk()
    window.title("Learnify")
    window.config(bg = "#fefefe")


    title_label = tk.Label(window, text = "Learnify", fg = "red", bg = "white", bd = 0, font = ("arial", 24, 'bold'))
    title_label.pack(pady = 10)

    output_box = tk.Text(window, state="disabled", fg = "black", bg = "white", width = 100, height = 35, font = ("arial", 12))
    output_box.pack(padx = 40, pady = (0, 20))

    prompt_label = tk.Label(window, text = "Enter your prompt below:", fg = "black", bg = "white", bd = 0, font = ("arial", 12))
    prompt_label.pack(pady = 10)

    prompt_entry = tk.Text(window, fg = "black", bg = "white", width = 100, height = 3, font = ("arial", 12))
    prompt_entry.pack()

    add_output_button = tk.Button(window, text = "Submit", width = 14, fg = "black", bg = "white", bd = 2, font = ("arial", 12), cursor = "hand2", command = give_answer)
    add_output_button.pack(pady = 10)

    prompt_entry.focus_set()
    window.mainloop()

def give_answer():
    global prompt_entry
    
    user_input = prompt_entry.get(1.0, tk.END)
    answer = loop(user_input) 
    add_output(answer)
    prompt_entry.delete(1.0, tk.END)
    prompt_entry.focus_set()

def add_output(msg):
    global output_box

    output_box.config(state="normal")
    output_box.delete("1.0", tk.END)
    output_box.insert(tk.END, msg)
    output_box.config(state="disabled")

main()