class RuleBasedChatbot:
    def __init__(self):
        self.responses = {
            "hello": "Hi there! How can I help you today?",
            "bye": "Goodbye! Have a great day!",
            "how are you": "I'm just a computer program, but thanks for asking!",
            "what's your name": "I'm a simple rule-based chatbot. I don't have a name, but you can call me Chatbot!"
        }

    def get_response(self, user_input):
        return self.responses.get(user_input.lower(), "I'm sorry, I don't understand that.")

if __name__ == "__main__":
    bot = RuleBasedChatbot()
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("Chatbot: Goodbye!")
            break
        response = bot.get_response(user_input)
        print(f"Chatbot: {response}")
