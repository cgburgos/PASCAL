import gradio as gr
import openai
import requests
import csv
import os
import json
from dotenv import load_dotenv

load_dotenv()


with open("modules/api/ChatGPTtemplates.json", "r") as jsonFile:
    ChatGPTtemplates = json.load(jsonFile)

prompt_templates = {"UNS Assistant": ChatGPTtemplates["UNS Assistant"]}

def get_openaikey():
    return os.getenv("chatgpt_openai_key")

def get_empty_state():
    return {"total_tokens": 0, "messages": []}


def on_token_change(user_token):
    openai.api_key = get_openaikey()

def on_prompt_template_change(prompt_template):
    return ChatGPTtemplates[prompt_template]

def submit_message(prompt, prompt_template, temperature, max_tokens, context_length, state):
    openai.api_key = get_openaikey()
    history = state['messages']

    if not prompt:
        return gr.update(value=''), [(history[i]['content'], history[i+1]['content']) for i in range(0, len(history)-1, 2)], f"Total tokens used: {state['total_tokens']}", state
    
    prompt_template = ChatGPTtemplates[prompt_template]

    system_prompt = []
    if prompt_template:
        system_prompt = [{ "role": "system", "content": prompt_template }]
    prompt_msg = { "role": "user", "content": prompt }
    """
    if not user_token:
        history.append(prompt_msg)
        history.append({
            "role": "system",
            "content": "Error: OpenAI API Key is not set."
        })
        return '', [(history[i]['content'], history[i+1]['content']) for i in range(0, len(history)-1, 2)], f"Total tokens used: 0", state
    """
    
    try:
        completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=system_prompt + history[-context_length*2:] + [prompt_msg], temperature=temperature, max_tokens=max_tokens)

        history.append(prompt_msg)
        history.append(completion.choices[0].message.to_dict())

        state['total_tokens'] += completion['usage']['total_tokens']
    
    except Exception as e:
        history.append(prompt_msg)
        history.append({
            "role": "system",
            "content": f"Error: {e}"
        })

    total_tokens_used_msg = f"Total tokens used: {state['total_tokens']}"
    chat_messages = [(history[i]['content'], history[i+1]['content']) for i in range(0, len(history)-1, 2)]

    return '', chat_messages, total_tokens_used_msg, state

def clear_conversation():
    return gr.update(value=None, visible=True), None, "", get_empty_state()


css = """
      #col-container {max-width: 80%; margin-left: auto; margin-right: auto;}
      #chatbox {min-height: 400px;}
      #header {text-align: center;}
      #prompt_template_preview {padding: 1em; border-width: 1px; border-style: solid; border-color: #e0e0e0; border-radius: 4px;}
      #total_tokens_str {text-align: right; font-size: 0.8em; color: #666;}
      #label {font-size: 0.8em; padding: 0.5em; margin: 0;}
      .message { font-size: 1.2em; }
      """

with gr.Blocks(css=css) as demo:
    
    state = gr.State(get_empty_state())


    with gr.Column(elem_id="col-container"):
        with gr.Row():
            with gr.Column():
                chatbot = gr.Chatbot(elem_id="chatbox")
                input_message = gr.Textbox(show_label=False, placeholder="Enter text and press enter", visible=True).style(container=False)
                btn_submit = gr.Button("Submit")
                total_tokens_str = gr.Markdown(elem_id="total_tokens_str")
                btn_clear_conversation = gr.Button("Start New Conversation")

                with gr.Accordion("Advanced parameters", open=False):
                    prompt_template = gr.Dropdown(label="Set a custom insruction for the chatbot:", value="UNS Assistant", choices=list(ChatGPTtemplates.keys()))
                    prompt_template_preview = gr.Markdown(elem_id="prompt_template_preview")
                    temperature = gr.Slider(minimum=0, maximum=2.0, value=0.7, step=0.1, label="Temperature", info="Higher = more creative/chaotic")
                    max_tokens = gr.Slider(minimum=100, maximum=500, value=300, step=1, label="Max tokens per response")
                    context_length = gr.Slider(minimum=1, maximum=10, value=2, step=1, label="Context length", info="Number of previous messages to send to the chatbot. Be careful with high values, it can blow up the token budget quickly.")
                

    btn_submit.click(submit_message, [input_message, prompt_template, temperature, max_tokens, context_length, state], [input_message, chatbot, total_tokens_str, state])
    input_message.submit(submit_message, [prompt_template, temperature, max_tokens, context_length, state], [input_message, chatbot, total_tokens_str, state])
    btn_clear_conversation.click(clear_conversation, [], [input_message, chatbot, total_tokens_str, state])
    prompt_template.change(on_prompt_template_change, inputs=[prompt_template], outputs=[prompt_template_preview])

    
    demo.load(inputs=None, outputs=[prompt_template], queur=False)


demo.queue(concurrency_count=10)
demo.launch(height='800px', debug=True)