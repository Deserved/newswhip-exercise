# Import all dependant libraries
import re
import datetime
import maxminddb
import operator
import requests
import sys

# Dictionary contains distinct countries from file as key and number of lines from file as value
countries_rank = {}
# Dictionary contains distinct countries from file as key and their location data retrieved from GeoLite2 database
countries_location = {}

# Parts of the pattern to build pattern for regular expression to parse log file
parts = [
    r'(?P<host>\S+)',                   # host %h
    r'\S+',                             # indent %l (unused)
    r'(?P<user>\S+)',                   # user %u
    r'\[(?P<time>.+)\]',                # time %t
    r'"(?P<request>.*)"',               # request "%r"
    r'(?P<status>[0-9]+)',              # status %>s
    r'(?P<size>\S+)'                    # size %b (careful, can be '-')
]

pattern = re.compile(r'\s+'.join(parts)+r'\s*\Z')

# Open log file and GoeLite 2 database
with open("sample.log") as log_file, maxminddb.open_database('GeoLite2-City.mmdb') as geolite_db:
    # Take every line in file
    for line in log_file:

        # Transform ever line in file to dictionary from now: log record
        log_record = re.match(pattern, line).groupdict()

        # Check if log record was on weekday
        is_weekday = (datetime.datetime.strptime(log_record["time"], '%d/%b/%Y:%H:%M:%S %z').weekday() < 5)
        # Check if log record got 5xx http status code
        http_status_5xx = (int(log_record["status"]) >= 500)

        # Only select lines that happened on weekday with http status code 5xx
        if http_status_5xx and is_weekday:

            # Get location of the IP Address
            ipv4_address = log_record["host"]
            location = geolite_db.get(ipv4_address)

            # Exclude locations that have no coordinates
            if location is not None and 'location' in location:

                # Some locations have country in 'registered_country' object some in 'country', get their ISO code
                if 'registered_country' in location:
                    country_iso_code = location['registered_country']['iso_code']
                else:
                    country_iso_code = location['country']['iso_code']

                # Populate dictionary with distinct countries codes and their location
                countries_location[country_iso_code] = location['location']

                # Count log records per country
                if country_iso_code in countries_rank:
                    countries_rank[country_iso_code] += 1
                else:
                    countries_rank[country_iso_code] = 1

# Order dictionary by country and descending number of log records, than select top 3
top_three = list(
    dict(
        sorted(
            countries_rank.items(),
            key=operator.itemgetter(1),
            reverse=True
        )
    ).items()
)[:3]

# For each country in top3, try to get Temperature using celsius units and print data
for index, country in enumerate(top_three):
    response = requests.get(
        url='https://api.openweathermap.org/data/2.5/weather',
        params=dict(
            lat=countries_location[country[0]]['latitude'],
            lon=countries_location[country[0]]['longitude'],
            units='metric',
            # P.S. Never ever do it this way in production :)
            appid='fe6f82b0341da7b464a08fdb4fba18f4'
        )
    )

    if response.status_code == 200:
        weather_data = response.json()

        if 'main' in weather_data:
            position = '#' + str((index + 1)) + ' ' + country[0] + ' ' + str(country[1]) + ' ' + str(weather_data['main']['temp']) + 'C'
        else:
            position = '#' + str((index + 1)) + ' ' + country[0] + ' ' + str(country[1]) + ' <Meteo data is unavailable>'

        print(position)
