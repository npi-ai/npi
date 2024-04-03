from npi.app.google.gmail.shared.agent import Agent

gmail_agent = Agent(
    model='gpt-4-turbo-preview',
    api_key='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',
    system_prompt='You are a Gmail Agent helping users to manage their emails.'
)
