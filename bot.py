from openai import AzureOpenAI
import os
import requests
import json

with open("keys/ticketmaster-keys.json", "r") as ticketmaster_files:
    tokens = json.load(ticketmaster_files)

client_key = tokens["client_key"]
client_secret = tokens["client_secret"]

#country_code = "UK"
search_size = 10

client = AzureOpenAI(
	api_key = os.getenv("AZURE_KEY"),
	api_version = "2023-10-01-preview",
	azure_endpoint = os.getenv("AZURE_ENDPOINT")
)

messages = [
    {"role": "system", "content":"Be really happy and make everything sound so much cooler"},
    {"role": "user", "content":"Find me a upcoming music shows in the UK"}
]

def find_events_by_country(country):
    url = f"https://app.ticketmaster.com/discovery/v2/events.json?countryCode={country}&{search_size}&apikey={client_key}"
    print(url)
    response = requests.get(url)
    data = response.json()
    #print(data)
    return f"Here are some shows in {country}"

functions = [
    {
        "type": "function",
        "function":{
            "name": "search_events",
            "description": "Finds upcoming music events in a specific country",
            "parameters": {
                "type": "object",
                "properties": {
                    "country":{
                        "type":"string",
                        "description":"The country I want to check"
                    }
                },
                "required": ["country"]
            }
        }
    }
]

response = client.chat.completions.create(
    model = "GPT-4",
    messages = messages,
    tools = functions,
    tool_choice = "auto"
)

response_message = response.choices[0].message
#print(response_message)

gpt_tools = response.choices[0].message.tool_calls

if gpt_tools:
    avaliable_functions={
        "search_events": find_events_by_country
    }
    messages.append(response_message)
    for gpt_tool in gpt_tools:
        function_name = gpt_tool.function.name
        function_to_call = avaliable_functions[function_name]
        function_parameters = json.loads(gpt_tool.function.arguments)
        function_response = function_to_call(function_parameters.get("country"))

        messages.append(
		    {
				"tool_call_id": gpt_tool.id,
				"role": "tool",
				"name": function_name,
				"content": function_response
			}
		)
        second_response = client.chat.completions.create(
			model = "GPT-4",
			messages=messages
		)
        print(second_response.choices[0].message.content)
else:
    print(response.choices[0].message.content)
    print("Defaulted")
