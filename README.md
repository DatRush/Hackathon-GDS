## Project Name
CityPass bot

## Description
This project is the result of a 27-hour hackathon hosted by Crocos and AITU. It includes two main components: a parsing bot and a Telegram bot. The parsing bot operates in the background, continuously analyzing data from the organizer's website and automatically updating the information in the Telegram bot when new data appears, thereby eliminating the need for admin intervention. The Telegram bot provides users with information about popular attractions and constructs routes to them based on the user's geolocation.

## Technology Stack
The following technologies, libraries, and tools were used in the project:

* Python 3.8
* Chrome WebDriver
* PostgreSQL
* BeautifulSoup
* Requests
* Logging
* Telegram Bot API
* Google Maps API
* Installation

## Step-by-step instructions for setting up the project:

1. Clone the repository:
`git clone https://github.com/DatRush/Hackathon-GDS.git`

2. Install the required libraries:
`pip install -r requirements.txt`

3. Configure environment variables or API keys as per your requirements.

## Launch
1. To run the parsing bot:
`python3 parsing_citypass.py`

2. To run the Telegram bot:
`python3 telegram_bot.py`

## Configuration
Database Settings: Specify your PostgreSQL database connection parameters.
API Keys: Specify your Telegram Bot API and Google Maps API keys in environment variables for the bots to function correctly.

## Contributing
Contributions to the project are welcome, I am open to pull requests. 