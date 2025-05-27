"""UI entrypoint."""

import json
from textwrap import dedent

import gradio as gr
import requests
from loguru import logger
from src.agent.custom_types import Message


def message(message: str, _history: list[list[str]], user_id: str) -> str:
    """Processes the user's message and returns a response."""
    formatted_msg = Message(
        body=message,
        user_id=user_id,
    )
    logger.info("Msg: {}", formatted_msg.model_dump_json(indent=2))
    response = requests.post(
        "http://127.0.0.1:8000/message",
        json=formatted_msg.model_dump(),
        headers={"Content-Type": "application/json"},
    )
    return json.loads(response.content)["answer"]


with gr.Blocks() as demo:
    gr.Markdown("# ACL test bot")  # Added a title for clarity
    gr.Markdown(
        dedent("""
            Check the data the bot server at
            [data/documents](https://github.com/msteiner-google/ofga-example/tree/main/data/documents)
            for the mock documents
            and [data/tabular_data](https://github.com/msteiner-google/ofga-example/tree/main/data/tabular_data)
            for the mock tabular data.
            """)
    )

    # 1. Add an input field for User ID
    user_id_input = gr.Textbox(
        label="User ID",
        placeholder="Enter your User ID here...",
        info="Specify your User ID to see how responses might change.",
    )

    chatbot = gr.Chatbot(
        label="Chat",
        placeholder="<strong>Your Personal Yes-Man</strong><br>Ask Me Anything",
    )

    # Assuming your ChatInterface can take a list of inputs for `fn`
    # If ChatInterface is `gradio.ChatInterface`, you'd pass user_id_input
    # in the `additional_inputs` argument.
    # For a custom ChatInterface, you'll need to ensure it's designed
    # to pass this additional input to the `fn`.

    # If you are using the standard `gradio.ChatInterface`:
    chat_interface = gr.ChatInterface(
        fn=message,
        chatbot=chatbot,
        additional_inputs=[user_id_input],  # Pass the textbox here
    )

    # If `ChatInterface` is your custom class as in the original code:
    # You'll need to modify your `ChatInterface` class to accept and pass
    # the `user_id_input` to the `message` function.
    # For now, let's assume you'll adapt it or use a more direct approach
    # if `ChatInterface` is just a conceptual wrapper in your example.

    # A more direct way if `ChatInterface` is just a placeholder for setup:
    # We need a way to trigger the 'message' function with all inputs.
    # Typically, a gr.Textbox for the message input and a gr.Button to submit.
    # The original code used a `ChatInterface` which simplifies this.
    # Let's adapt it to use `gr.ChatInterface` for a complete, working example.

    # Re-structuring to use gr.ChatInterface for clarity and functionality:
    # Remove the custom ChatInterface line for this example and use gr.ChatInterface
    # if that's the goal, or show how to pass it if it's truly custom.

    # Let's assume your `ChatInterface` from `src.ui.chat_interface`
    # is a standard `gradio.ChatInterface` or behaves like it regarding `additional_inputs`.
    # If it's a completely custom class, you'll need to modify its __init__ or call method
    # to accept and use `user_id_input`.

    # Option 1: Using gr.ChatInterface (recommended for standard Gradio apps)
    # chat_ui = gr.ChatInterface(
    #     fn=message,
    #     chatbot=chatbot,
    #     additional_inputs=[user_id_input]
    # )

    # Option 2: If your `ChatInterface` is custom and you want to keep its structure.
    # You need to ensure your `ChatInterface` class handles the `user_id_input`.
    # For example, it might internally use a button that, when clicked,
    # gathers values from the message input, history, *and* your new user_id_input.

    # Given the original code's structure:
    # `ChatInterface(fn=message, type="messages", chatbot=chatbot)`
    # This looks like it's setting up the chat functionality.
    # To add the user_id, you'd typically make it an input to the function `fn`.
    # Gradio's `ChatInterface` does this via `additional_inputs`.
    # If `src.ui.chat_interface.ChatInterface` is your own class, you need to modify it.

    # For a direct example of how to wire it up if `ChatInterface` is not `gr.ChatInterface`:
    # You would typically have a message input textbox and a submit button.

    # The `submit` action will call the `message` function
    # It needs the message text, the chat history, and the user_id
    # The `chatbot` component itself often manages history.
    # `gr.Chatbot` acts as an output and input (for history).


demo.launch()
