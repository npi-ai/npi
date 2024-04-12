from npi.browser_app.general_browser_agent import GeneralBrowserAgent

if __name__ == '__main__':
    agent = GeneralBrowserAgent(headless=False)
    response = agent.chat(
        'Book a one-way flight from ATL to LAX on 4/20 using Google Flights. Delta Airline is preferred'
    )
    print(response)
