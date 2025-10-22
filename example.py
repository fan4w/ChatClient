from ChatClient import ChatClient

if __name__ == "__main__":
    print("Initializing ChatClient with config.json")
    client = ChatClient(config_path="config.json")
    
    models = client.get_available_models()
    print("Available models:")
    for model in models:
        print(f"- {model['name']} (ID: {model['id']}, server by: {model['server']})")
    
    print("\nSetting model to ID 1")
    client.set_model_by_id(1)
    selected_model = client.get_selected_model()
    if selected_model:
        print(
            f"Selected model: {selected_model.name} (ID: {selected_model.id}, server by: {selected_model.server})"
        )

    print("\nStarting chat session...")
    user_input = "Hello, how are you?"
    print(f"\nUser: {user_input}")
    response = client.chat(user_input)
    print(f"Assistant: {response}")

    # system prompt and stream response example
    print("\nSetting system prompt to simulate a cat persona, and streaming response.")
    client.chat_cleanup()
    client.set_system_prompt(
        "You are a cat, so whatever I say, respond like a cat would."
    )
    stream_response = client.stream_chat(user_input)
    print("\nStreaming response:")
    for chunk in stream_response:
        if chunk:
            print(chunk, end="", flush=True)

    # json chat example and init from env
    print("\n\nRe-initializing ChatClient from environment variables.")
    client = ChatClient()
    
    print("\n\nSetting system prompt for JSON output.")
    json_system_prompt = """
        The user will provide some exam text. Please parse the "question" and "answer" and output them in JSON format.

        EXAMPLE INPUT:
        Which is the highest mountain in the world? Mount Everest.

        EXAMPLE JSON OUTPUT:
        {
            "question": "Which is the highest mountain in the world?",
            "answer": "Mount Everest"
        }
    """
    client.chat_cleanup()
    client.set_system_prompt(json_system_prompt)
    user_input = "Which is the longest river in the world? The Nile River."

    json_response = client.json_chat(user_input)
    print("\nJSON response:")
    print(json_response)

    print()
