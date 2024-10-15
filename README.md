# UEXcorp Trader

## Purpose

This application is a simple trading tool for the UEXcorp API. It allows you to:

- Buy and sell commodities at different terminals in the Star Citizen universe.
- Select systems, planets, and terminals from dropdown lists for easy trading.
- View a log of API requests made by the application.
- Configure your UEXcorp API key.

## Prerequisites

- **Python 3.7 or higher:** You can download Python from [https://www.python.org/downloads/](https://www.python.org/downloads/).
- **PyQt5:** Install using pip: `pip install PyQt5`
- **aiohttp:** Install using pip: `pip install aiohttp`
- **configparser:** This module is usually included in the standard Python library.

## Installation and Startup

1. Clone the repository: 
   `git clone https://github.com/Hybris95/UEX-Trader.git`
   (Replace with your repository URL)

2. Navigate to the project directory: 
   `cd UEX-Trader`

3. Run the application: 
   `python main.py`

## Configuration

- On the first run, you'll need to enter your UEXcorp API key in the "Configuration" tab.
- Save the API key, and the application will load data from the UEXcorp API.

## Usage

- **Buy/Sell Tabs:** Select the desired system, planet, terminal, commodity, amount, and price. Then click the "Buy Commodity" or "Sell Commodity" button.
- **API Output:** The bottom section of the application displays a log of API requests, which can be useful for debugging. 

## Notes

- The application assumes you are not performing production operations.
- Ensure you have a valid UEXcorp API key for the trading functionality to work. 
