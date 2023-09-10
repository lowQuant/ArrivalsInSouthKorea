from FlightRadar24 import FlightRadar24API
import datetime, time, sqlite3, datetime, os
import matplotlib.pyplot as plt

# import schedule

# GLOBALS
AIRPORTS = ["ICN", "GMP", "CJU", "CJJ","KUV","KWJ","MWX","RSU","HIN","PUS","USN","KPO"]
fr_api = FlightRadar24API()
today = datetime.date.today().isoformat()

# FUNCTIONS
def check_and_setup_db():
    """Check if the database exists, if not, execute create_db.py."""
    if not os.path.exists('flights.db'):
        conn = sqlite3.connect('flights.db')
        cursor = conn.cursor()
    
        # Create table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS flights (
            date TEXT,
            id TEXT PRIMARY KEY,
            callsign TEXT,
            airport TEXT,
            airline TEXT,
            aircraft TEXT,
            origin TEXT,
            ETA TEXT
        )
        ''')
        conn.commit()
        conn.close()

def fetch_flight_counts():
    conn = sqlite3.connect('flights.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT date, COUNT(*) as count 
    FROM flights 
    GROUP BY date 
    ORDER BY date
    ''')
    
    data = cursor.fetchall()
    conn.close()
    
    # Splitting the data into dates and counts
    dates = [entry[0] for entry in data]
    counts = [entry[1] for entry in data]
    
    return dates, counts

def plot_and_save_chart(dates, counts):
    plt.xkcd()  # Apply comic-style to the plot
    plt.figure(figsize=(10, 6))
    
    if len(dates) > 10:
        # Use a line chart if more than 10 dates
        plt.plot(dates[1:], counts[1:], marker='o', color='skyblue', linestyle='-')
    else:
        # Use a bar chart otherwise
        plt.bar(dates, counts, color='skyblue')
        
    plt.xlabel('Date')
    plt.ylabel('Number of Flights')
    plt.title('Number of Flights Per Day')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('flights_per_day.png')

def is_today_in_db():
    """Check if there are entries with today's date in the database."""
    conn = sqlite3.connect('flights.db')
    cursor = conn.cursor()
    today = datetime.date.today().isoformat()
    cursor.execute('SELECT COUNT(*) FROM flights WHERE date=?', (today,))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

def generate_chart_if_needed():
    # if not os.path.exists('flights_per_day.png') or is_today_in_db()==0:
    dates, counts = fetch_flight_counts()
    plot_and_save_chart(dates, counts)

def id_in_db(id):
    conn = sqlite3.connect('flights.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM flights WHERE id=?', (id,))
    data = cursor.fetchone()
    conn.close()
    return data is not None

def store_flight_details(flight_details):
    conn = sqlite3.connect('flights.db')
    cursor = conn.cursor()
    try:
        try:
            date = datetime.datetime.utcfromtimestamp(flight_details['status']['generic']['eventTime']['utc']).strftime('%Y-%m-%d')
        except KeyError:
            date = datetime.datetime.utcfromtimestamp(flight_details['firstTimestamp']).strftime('%Y-%m-%d')
    except:
        print("Date/Timestamp information missing. Filling with todays date.")
        date = datetime.date.today().isoformat()

    id = flight_details['identification']['id']
    callsign = flight_details['identification']['callsign']
    airport = flight_details['airport']['destination']['code']['iata']
    airline = flight_details['identification']['number']['default']
    aircraft = flight_details['aircraft']['model']['text']
    origin = flight_details['airport']['origin']['code']['iata']
    eta = flight_details['status']['text']
    
    cursor.execute('''
    INSERT INTO flights (date, id, callsign, airport, airline, aircraft, origin, ETA)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (date, id, callsign, airport, airline, aircraft, origin, eta))
    
    conn.commit()
    conn.close()

def main(fr_api,AIRPORTS):
    for airport in AIRPORTS:
            airport_details = fr_api.get_airport_details(airport, flight_limit=100)
            print(f"Checking flights for {airport_details['airport']['pluginData']['details']['name']}")
            arriving_flights = airport_details['airport']['pluginData']['schedule']['arrivals']['data']

            flights_from_china = [flight for flight in arriving_flights if flight['flight']['airport']['origin']['position']['country']['name'] == 'China']
            print(f"Seeing: \n {[flight['flight']['identification']['callsign'] for flight in arriving_flights if flight['flight']['airport']['origin']['position']['country']['name'] == 'China']}")
            
            for flight in flights_from_china:
                id = flight['flight']['identification']['id']
                callsign = flight['flight']['identification']['callsign']

                if not id_in_db(id) and id is not None:
                    flight_details = fr_api.get_flight_details(flight['flight']['identification']['id'])
                    store_flight_details(flight_details)
                elif callsign is not None:
                    print(f"{callsign} already in db for {today}")
                            
            time.sleep(2)

if __name__ == '__main__':
    check_and_setup_db()  # Check and set up the database first
    generate_chart_if_needed()
    main(fr_api, AIRPORTS)

    # schedule.every().hour.do(main, fr_api, AIRPORTS)
    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)
