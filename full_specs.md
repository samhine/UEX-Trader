Given the following specifications write me a main.py :
```
Give me a little example of an application written in Python, using PyQt for the interface, ConfigParser to store long-term variables and aiohttp for API interactions.

The application design is simple, and must contain a few tabs :
1st tab : Allow you to configure the API tokens for uexcorp.space (as documented on https://uexcorp.space/api/documentation/ )
2nd tab : Buy commodity ( list of commodities on https://uexcorp.space/api/2.0/commodities ) at a given terminal ( list of terminals on https://uexcorp.space/api/2.0/terminals , documentation on https://uexcorp.space/api/documentation/id/terminals/ )
3rd tab : Sell commodity (like buying)

Buying or selling commodity uses the given POST call :
https://uexcorp.space/api/2.0/user_trades_add/
Documentation at https://uexcorp.space/api/documentation/id/user_trades_add/
```
Version of Python to use is Python3.13
Also give me the requirements.txt file.

Below you will find documentations required for each API call :
```
 /commodities
Method GET
URL https://uexcorp.space/api/2.0/commodities
Authorization —
Cache TTL +1 hour

Input -
Output id int(11)
id_parent int(11)
name string(255)
code string(5) // UEX commodity code
slug string(255) // UEX URL slug
kind string(255)
price_buy float // average market price per SCU
price_sell float // average market price per SCU
is_available int(1) // available in-game
is_visible int(1) // visible on the website
is_raw int(1)
is_refined int(1)
is_mineral int(1)
is_harvestable int(1)
is_buyable int(1)
is_sellable int(1)
is_temporary int(1)
is_illegal int(1) // if the commodity is restricted in one or more jurisdictions
is_fuel int(1)
wiki string(255)
date_added int(11) // timestamp
date_modified int(11) // timestamp

Response 
status • ok

Update date Patch cycle (usually)
Documentation update: 5 days ago
```

```
 /planets
Methods GET
URL https://uexcorp.space/api/2.0/planets?id_star_system={int}	
Authorization —
Cache TTL +1 day
Input id_star_system int(11) // optional
is_lagrange int(11) // optional

Output 
id int(11)
id_star_system int(11)
id_faction int(11)
name string(255)
name_origin string(255) // discovery name
code string(255) // our code
is_available int(1)
is_visible int(1)
is_default int(1)
is_lagrange int(1)
date_added int(11) // timestamp
date_modified int(11) // timestamp
star_system_name string(255)

Response 
status • ok

Update rate Patch cycle (usually)
Documentation update: 4 months ago
```

```
 /star_systems
Methods GET
URL https://uexcorp.space/api/2.0/star_systems
Authorization —
Cache TTL +1 day

Input -
Output id int(11)
name string(255)
code string(2) // our code
is_available int(1)
is_visible int(1)
is_default int(1)
wiki string(255) // Wiki URL
date_added int(11) // timestamp
date_modified int(11) // timestamp

Response 
status • ok

Update rate Patch cycle (usually)
Documentation update: 4 months ago
```

```
 /terminals
Methods GET

URL 
https://uexcorp.space/api/2.0/terminals?id_star_system={int}
https://uexcorp.space/api/2.0/terminals?id_planet={int}
https://uexcorp.space/api/2.0/terminals?name={string}
https://uexcorp.space/api/2.0/terminals?code={string}

Authorization —
Cache TTL +12 hours

Input 
id_star_system int(11)
id_planet int(11)
id_orbit int(11)
id_moon int(11)
id_space_station int(11)
id_city int(11)
id_outpost int(11)
id_poi int(11)
type string(255)
name string(255)
code string(255)
Output id int(11)
id_star_system int(11)
id_planet int(11)
id_orbit int(11)
id_moon int(11)
id_space_station int(11)
id_outpost int(11)
id_poi int(11)
id_city int(11)
id_faction int(11)
name string(255)
nickname string(255)
code string(6) // our code
type string(20) // our type
screenshot string(255)
screenshot_thumbnail string(255) // please choose thumbnails whenever possible
screenshot_author string(255) // screenshot author
mcs int(11) // maximum container size operated by freight elevator (in SCU)
is_available string(255) // is available in-game
is_visible int(1) // is visible in the UEX website
is_default_system int(1) // is the default terminal in a star system
is_affinity_influenceable int(1) // if terminal data is faction affinity influenced
is_habitation int(1)
is_refinery int(1)
is_cargo_center int(1)
is_medical int(1)
is_food int(1)
is_shop_fps int(1) // shop trading FPS items
is_shop_vehicle int(1) // shop trading vehicle components
is_refuel int(1)
is_repair int(1)
is_nqa int(1) // no questions asked terminal
has_loading_dock int(1)
has_docking_port int(1)
has_freight_elevator int(1)
date_added int(11) // timestamp
date_modified int(11) // timestamp
star_system_name string(255)
planet_name string(255)
orbit_name string(255)
moon_name string(255)
space_station_name string(255)
outpost_name string(255)
city_name string(255)
Types reference commodity
item
commodity_raw
vehicle_buy
vehicle_rent
vehicle_pledge
fuel
refinery_audit
workaround

Response 
status • invalid_type
• ok
Update rate Patch cycle (usually)
Documentation update: 2 months ago
```

```
 /user_trades_add
Method POST
URL https://uexcorp.space/api/2.0/user_trades_add/
Authorization Bearer Token	
Cache TTL —

Input (Header) 
secret_key string(40) // required user secret key, should be passed via header, obtained in user profile
Input (POST) id_terminal int(11) // required
id_commodity int(11) // required
id_user_fleet int(11) // optional, user fleet vehicle ID
operation string(4) // transaction type, required, should be 'buy' or 'sell'
scu int(11) // required, amount purchased/sold in SCU
price float // required, values in UEC per SCU
is_production int(1) // required for production

JSON input example
	{
 "is_production": 0,
 "id_terminal": 29,
 "id_commodity": 18,
 "operation": "buy",
 "scu": 110,
 "price": 2441
}

Output 
id_user_trade int(11) // user trade unique ID

Responses 

// user secret key not provided
missing_secret_key

// user not found with provided secret key
user_not_found

// user banned or disabled by administrator
user_not_allowed

// user account not verified on RSI website
user_not_verified

// user secret key length should be exactly 40 characters
invalid_secret_key

// transaction type not provided
missing_operation

// invalid transaction type - should be buy or sell
invalid_operation

// terminal ID not provided
missing_id_terminal

// terminal ID not found
terminal_not_found

// commodity ID not provided
missing_id_commodity

// commodity ID not found
commodity_not_found

// SCU not provided
missing_scu

// commodity price per SCU not provided
missing_price

// vehicle ID not found
vehicle_not_found

// all good!
ok

Last update: 4 months ago
```
