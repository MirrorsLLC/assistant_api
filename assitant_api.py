
from openai import OpenAI
import time
from dotenv import load_dotenv
import os
import json

load_dotenv()



def send_email_to_real_agent():
    return "thank you on behalf of our agency"


class AssistantManager:
    def __init__(self, api_key, model="gpt-4-1106-preview"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.assistant = None
        self.thread = None
        self.run = None

    def create_assistant(self, name, instructions, tools, file):
        file = self.upload_files(file)
        self.assistant = self.client.beta.assistants.create(
            name=name,
            instructions=instructions,
            tools=tools,
            model=self.model,
            file_ids=[file.id]
        )

    def retrieve_assistant(self, assistant_id):
        try:
            self.assistant = self.client.beta.assistants.retrieve(assistant_id)
        except Exception as e:
            print(f"Error retrieving assistant: {e}")
            self.assistant = None

    def upload_files(self, file_path):
        api_key = os.getenv("OPENAI_API_KEY")
        client = OpenAI(api_key=api_key)
        # Upload a file with an "assistants" purpose
        file = client.files.create(
        file=open(file_path, "rb"),
        purpose='assistants')
    
        return file

    def create_thread(self):
        self.thread = self.client.beta.threads.create()

    def add_message_to_thread(self, role, content):
        self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role=role,
            content=content
        )

    def run_assistant(self, instructions):
        self.run = self.client.beta.threads.runs.create(
            thread_id=self.thread.id,
            assistant_id=self.assistant.id,
            instructions=instructions
        )

    def wait_for_completion(self):
        while True:
            time.sleep(5)
            run_status = self.client.beta.threads.runs.retrieve(
                thread_id=self.thread.id,
                run_id=self.run.id
            )
            print(run_status.model_dump_json(indent=4))

            if run_status.status == 'completed':
                self.process_messages()
                break
            elif run_status.status == 'requires_action':
                print("Function Calling ...")
                self.call_required_functions(run_status.required_action.submit_tool_outputs.model_dump())
            else:
                print("Waiting for the Assistant to process...")

    def process_messages(self):
        messages = self.client.beta.threads.messages.list(thread_id=self.thread.id)

        for msg in messages.data:
            role = msg.role
            content = msg.content[0].text.value
            print(f"{role.capitalize()}: {content}")

    def call_required_functions(self, required_actions):
        tool_outputs = []

        for action in required_actions["tool_calls"]:
            func_name = action['function']['name']
            arguments = json.loads(action['function']['arguments'])

            if func_name == "send_email_to_real_agent":
                output = send_email_to_real_agent()
                tool_outputs.append({
                    "tool_call_id": action['id'],
                    "output": output
                })
            else:
                raise ValueError(f"Unknown function: {func_name}")

        print("Submitting outputs back to the Assistant...")
        self.client.beta.threads.runs.submit_tool_outputs(
            thread_id=self.thread.id,
            run_id=self.run.id,
            tool_outputs=tool_outputs
        )



def main():
    api_key = os.getenv("OPENAI_API_KEY")
    assistant_id = "asst_YlvNgooU8NdVhIWqG9XeiuU6"  

    manager = AssistantManager(api_key)
    manager.retrieve_assistant(assistant_id)
    if not manager.assistant:
        manager.create_assistant(
            name="Real Estate Assistant",
            instructions="You are a real estate assistant, helping clients find their ideal homes and suggesting housing options.",
            file="listing_sample_cities_100.json",
            tools=[{
                "type": "retrieval",
                "function": {
                    "name": "send_email_to_real_agent",
                    "description": "Send an email to a real estate agent to express a client's interest in booking a house.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "send_email_to_real_agent": {
                                "type": "string",
                                "description": "operation to the end point"
                            }
                        },
                        "required": ["description"]
                    }
                }
            }]
        )
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("Goodbye!")
            break

        manager.create_thread()
        manager.add_message_to_thread(role="user", content=user_input)
        manager.run_assistant(instructions="")
        manager.wait_for_completion()

if __name__ == '__main__':
    main()