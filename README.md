# UEX-Trader

UEX-Trader is a desktop application designed to facilitate trading within the UEXcorp space trading ecosystem. The application allows users to configure API keys, toggle between production and debug modes, and trade commodities by selecting systems, planets, and terminals. Additionally, users can switch between Light and Dark appearance modes for better user experience.

![UEX-Trader Icon](resources/UEXTrader_icon.png)

## Prerequisites

Before you begin, ensure you have met the following requirements:

- You have Python 3.11.10 or higher installed.
- You have `pip` (Python package installer) installed.
- You have access to the UEXcorp API.

## Installation

1. **Clone the repository:**

  ```sh
  git clone https://github.com/Hybris95/UEX-Trader.git
  cd UEX-Trader
  ```

2. **Create a virtual environment:**

  ```sh
  python -m venv .venv
  ```

3. **Activate the virtual environment:**

  - On Windows:

   ```sh
   .\.venv\Scripts\activate
   ```

  - On macOS/Linux:

   ```sh
   source .venv/bin/activate
   ```

4. **Install the required dependencies:**

  ```sh
  pip install -r requirements.txt
  ```

## Startup

1. **Run the application:**

  ```sh
  python main.py
  ```

2. **The application window should open, displaying the Configuration, Trade Commodity, Find Trade Route, and Best Trade Routes tabs.**

## Configuration

1. **Open the Configuration tab:**

  - **UEXcorp API Key:** Enter your UEXcorp App Access Token ( you first have to create an App on UEXCorp : https://uexcorp.space/api/apps ).
  - **UEXcorp Secret Key:** Enter your UEXcorp Secret key ( Account for UEXcorp required : https://uexcorp.space/account/home/tab/account_main/ )
  - **Is Production:** Toggle between `True` and `False` to switch between production and development environments.
  - **Debug Mode:** Toggle between `True` and `False` to enable or disable debug logging.
  - **Appearance Mode:** Select between `Light` and `Dark` modes for the application's appearance.

2. **Save Configuration:**

  - Click the "Save Configuration" button to save your settings. The application will apply the new appearance mode if it has changed.

## Use Cases

### Trading Commodities

1. **Select System:**

  - Choose a star system from the dropdown list.

2. **Select Planet:**

  - Choose a planet from the dropdown list.

3. **Select Terminal:**

  - Use the search input to filter and select a terminal. You can type part of the terminal's name to quickly find it.

4. **Select Commodity:**

  - Choose a commodity from the dropdown list.

5. **Enter Amount and Price:**

  - Enter the amount (in SCU) and price (in UEC/SCU) for the commodity.

6. **Execute Trade:**

  - Click "Buy Commodity" to buy or "Sell Commodity" to sell the selected commodity.

### Finding Trade Routes

1. **Select Departure System, Planet, and Terminal:**

  - Choose your desired departure location using the respective dropdown menus.

2. **(Optional) Set Restrictions:**

  - Check "Restrict to System" to limit trade routes within the selected departure system.
  - Check "Restrict to Planet" to limit trade routes within the selected departure planet.

3. **(Optional) Set Investment Limits:**

  - Enter a value in "Max Investment" to limit the maximum investment for each trade route.
  - Enter a value in "Max SCU" to limit the maximum SCU purchased for each trade route.
  - Enter a value in "Min SCU at Departure" to filter out routes with insufficient SCU available at the departure terminal.

4. **Initiate Search:**

  - The application will automatically search and display the top 10 most profitable trade routes based on your selected criteria.

### Best Trade Routes

1. **Select Departure System and Planet:**

  - Choose your desired departure system and planet using the respective dropdown menus. You can select "All Planets" to include all planets in the selected system.

2. **Select Destination System and Planet:**

  - Choose your desired destination system and planet using the respective dropdown menus. You can select "All Systems" to include all systems and "All Planets" to include all planets in the selected system.

3. **(Optional) Set Investment Limits:**

  - Enter a value in "Max Investment" to limit the maximum investment for each trade route.
  - Enter a value in "Max SCU" to limit the maximum SCU purchased for each trade route.

4. **(Optional) Set Filters:**

  - Check "Ignore Stocks" to ignore the available SCU at the departure terminal.
  - Check "Ignore Demand" to ignore the demand SCU at the arrival terminal.

5. **Initiate Search:**

  - Click "Find Best Trade Routes" to search for the best trade routes based on your selected criteria. The application will display the top 10 most profitable trade routes.

6. **Execute Trade:**

  - Click "Select to Buy" to buy the selected commodity or "Select to Sell" to sell the selected commodity.

### Appearance Mode

- **Light Mode:** Provides a standard light theme for the application.
- **Dark Mode:** Provides a dark theme for better visibility in low-light environments.

## Logging

- The application logs various actions and API responses to help with debugging and monitoring. Logs are displayed in the console where the application is run.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

If you have any questions or issues, please open an issue on the GitHub repository.
