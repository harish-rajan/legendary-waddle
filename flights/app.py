from flask import Flask, render_template, request, redirect, url_for, flash
import pymysql.cursors
from flask import Flask, request, render_template, redirect
from pymysql import connect, MySQLError

# Connect to the database
connection = pymysql.connect(host='localhost',
                             user='root',
                             password='',
                             db='flight_tracking',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

app = Flask(__name__)



@app.route('/')
def home():
    return render_template("home.html")

@app.route('/airplanes')
def airplanes():
    try:
        with connection.cursor() as cursor:
            sql = "SELECT airlineid, tail_num, seat_capacity, speed, locationID, plane_type" \
                  ", skids, propellers, jet_engines FROM airplane"

            cols = ['airlineid', 'tail_num', 'seat_capacity', 'speed', 'locationID', 'plane_type', 'skids',
                    'propellers', 'jet_engines']
            cursor.execute(sql)
            items = cursor.fetchall()

            sql2 = "SELECT DISTINCT airlineID FROM airline"

            cursor.execute(sql2)
            airlines = cursor.fetchall()
            return render_template("airplanes.html", items=items, cols=cols, airlines=airlines, success='')
    except Exception as e:
        return render_template("airplanes.html", items=[], cols=[], success='Error: ' + str(e))

@app.route('/addairplaneReq', methods=['GET', 'POST'])
def add_airplane():
    airlineID = request.args.get('airlineID')
    tail_num = request.args.get('tail_num')
    seat_capacity = request.args.get('seat_capacity')
    speed = request.args.get('speed')
    locationID = request.args.get('locationID')
    plane_type = request.args.get('plane_type')
    skids = request.args.get('skids')
    try:
        if skids is not None:
            skids = 1
        propellers = request.args.get('propellers')
        if propellers is not None:
            propellers = int(propellers)
        jet_engines = request.args.get('jet_engines')
        if jet_engines is not None:
            jet_engines = int(jet_engines)
        if speed is not None:
            speed = int(speed)
        if seat_capacity is not None:
            seat_capacity = int(seat_capacity)
    except ValueError:
        return render_template("airplanes.html", success='Invalid input given.')

    try:

        cursor = connection.cursor()
        cursor.execute("SELECT * FROM airplane WHERE airlineID = %s and tail_num = %s", (airlineID, tail_num))
        if cursor.fetchone():
            return render_template("airplanes.html", success='Duplicate entry.')

        sql_proc = "call add_airplane(%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        args = [airlineID, tail_num, seat_capacity, speed, locationID, plane_type, skids, propellers, jet_engines]
        cursor.execute(sql_proc, args)
        connection.commit()
        cursor.close()
        return redirect("/airplanes")

    except MySQLError as e:
        return render_template("flights.html", success=f'Can\'t complete: {e}')
    except Exception as e:
        return render_template("flights.html", success=f'Error: {e}')
    
@app.route('/airports')
def airports():
    try:
        with connection.cursor() as cursor:
            sql = "SELECT airportID, airport_name, city, state, country, locationID FROM airport"

            cols = ['airportID', 'airport_name', 'city', 'state', 'country', 'locationID']
            cursor.execute(sql)
            items = cursor.fetchall()

            return render_template("airports.html", items=items, cols=cols, success='')
    except Exception as e:
        return render_template("airports.html", items=[], cols=[], success='Error: ' + str(e))



# Assuming 'connection' is your MySQL connection object
# app = Flask(__name__)  # This should already be defined in your app.py

@app.route('/addAirportReq', methods=['GET', 'POST'])
def add_airport():
    airportID = request.args.get('airportID', '').strip()
    airport_name = request.args.get('airport_name', '').strip()
    city = request.args.get('city', '').strip()
    state = request.args.get('state', '').strip()
    country = request.args.get('country', '').strip()
    locationID = request.args.get('locationID', '').strip()

    if not (airportID and airport_name and city and state and country):
        return render_template("airports.html", success='All fields are required.')

    try:
        with connection.cursor() as cursor:
            # Check if the airportID already exists
            cursor.execute("SELECT * FROM airport WHERE airportID = %s", (airportID,))
            if cursor.fetchone():
                return render_template("airports.html", success='Duplicate entry.')

            # Proceed with insertion if no duplicate found
            sql_proc = "call add_airport(%s, %s, %s, %s, %s, %s)"
            args = [airportID, airport_name, city, state, country, locationID]
            cursor.execute(sql_proc, args)
            connection.commit()
        return redirect("/airports")
    except MySQLError as e:
        return render_template("airports.html", success=f'Can\'t complete: {e}')
    except Exception as e:
        return render_template("airports.html", success=f'Error: {e}')

# app.run() # if this is the main module


@app.route('/people')
def people():
    try:
        with connection.cursor() as cursor:
            sql = "select t1.personID, t1.first_name, t1.last_name, case " \
                    "when t1.personID in (select personID from passenger) then 'passenger' " \
                    "when t1.personID in (select personID from pilot) then 'pilot' else null " \
                "end as role, t1.locationID, case " \
                    "when t2.airportID is not null then concat(t2.airport_name, ' (', t2.airportID, ')') " \
                    "when t3.tail_num is not null then concat(t3.airlineID, ' flight ', regexp_substr(t4.flightID,'[0-9]+')) " \
                    "else null end as location_name " \
            "from person t1 left join airport t2 on t1.locationID = t2.locationID " \
                "left join airplane t3 on t1.locationID = t3.locationID " \
                "left join flight t4 on t3.airlineID = t4.support_airline and t3.tail_num = t4.support_tail " \
            "order by convert(right(t1.personID, length(t1.personID) - 1), decimal)"

            cols = ['personID', 'first_name', 'last_name', 'role', 'locationID', 'location_name']
            cursor.execute(sql)
            items = cursor.fetchall()

            sql2 = "select locationID from location"
            cursor.execute(sql2)
            locations = cursor.fetchall()

            return render_template("people.html", items=items, cols=cols, locations=locations, success='')
    except Exception as e:
        return render_template("people.html", items=[], cols=[], success='Error: ' + str(e))
    
@app.route('/addPersonReq', methods=['GET'])
def add_persons():
    personID = request.args.get('personID')
    first_name = request.args.get('first_name')
    last_name = request.args.get('last_name')
    locationID = request.args.get('locationID')
    tax_ID = request.args.get('tax_ID')
    experience = request.args.get('experience')
    miles = request.args.get('miles')
    funds = request.args.get('funds')
    if not(personID and first_name and last_name and locationID):
        return render_template("people.html", success='All fields are required.')
    if request.args.get('passengerRole') == True:
        miles = int(miles)
        funds = int(funds)

    if request.args.get('pilotRole') == True:
        tax_ID = tax_ID.strip()
        experience = int(experience)
    

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM person WHERE personID = %s", (personID))
            if cursor.fetchone():
                return render_template("people.html", success='Duplicate entry.')
            args = (personID, first_name, last_name, locationID, tax_ID,
                    experience, miles, funds)
            cursor.callproc('add_person', args)
            connection.commit()
            return redirect("/people")

    except MySQLError as e:
        return render_template("people.html", success=f'Can\'t complete: {e}')
    except Exception as e:
        return render_template("people.html", success=f'Error: {e}')


@app.route('/pilots')
def pilots():
    try:
        with connection.cursor() as cursor:
            sql = "select t1.personID, t2.first_name, t2.last_name, t1.taxID, t1.experience, concat(t3.support_airline, ' flight ', regexp_substr(t1.commanding_flight,'[0-9]+')) as commanding_flight " \
                "from pilot t1 join person t2 on t1.personID = t2.personID " \
                "left join flight t3 on t1.commanding_flight = t3.flightID " \
                "order by convert(right(t1.personID, length(t1.personID) - 1), decimal)"

            cols = ['personID', 'first_name', 'last_name', 'taxID', 'experience', 'commanding_flight']
            cursor.execute(sql)
            items = cursor.fetchall()
            return render_template("pilots.html", items=items, cols=cols, success='')
    except Exception as e:
        return render_template("pilots.html", items=[], cols=[], success='Error: ' + str(e))
    
@app.route('/pilots/<personID>/licenses')
def lisences(personID):
    try:
        with connection.cursor() as cursor:
            sql = f"select license from pilot_licenses where personID = '{personID}'"

            cols = ['license']
            cursor.execute(sql)
            items = cursor.fetchall()

            sql2 = f"select concat(first_name, ' ', last_name) as name from person where personID = '{personID}'"
            cursor.execute(sql2)
            name = list(cursor.fetchone().values())[0]

            return render_template("licenses.html", items=items, cols=cols, name=name, personID=personID, success='')
    except Exception as e:
        return render_template("licenses.html", items=[], cols=[], name="", personID="", success='Error: ' + str(e))
    
@app.route('/licenseReq', methods=['GET'])
def license():
    personID = request.args.get('personID').strip()
    license = request.args.get('license').strip()

    try:
        with connection.cursor() as cursor:
            args = (personID, license)
            cursor.callproc('grant_or_revoke_pilot_license', args)
            connection.commit()
            return redirect(f"/pilots/{personID}/licenses")
    except Exception as e:
        return redirect(f"/pilots/{personID}/licenses")
    
@app.route('/flights')
def flights():
    try:
        with connection.cursor() as cursor:
            sql = "select t1.support_airline, t1.flightID, t1.support_tail, t1.airplane_status, t1.routeID, t1.progress, " \
                "t3.departure, t3.arrival, t1.next_time, t1.cost " \
                "from flight t1 left join route_path t2 on t1.routeID = t2.routeID and t1.progress = t2.sequence " \
                "left join leg t3 on t2.legID = t3.legID"

            cols = ['support_airline', 'flightID', 'support_tail', 'airplane_status', 'routeID', 'progress', 'departure', 'arrival', 'next_time', 'cost']
            cursor.execute(sql)
            items = cursor.fetchall()

            sql2 = "select routeID from route"
            cursor.execute(sql2)
            routes = cursor.fetchall()

            sql3 = "select airlineID from airline"
            cursor.execute(sql3)
            airlines = cursor.fetchall()

            sql4 = "select airlineID, tail_num from airplane"
            cursor.execute(sql4)
            airplanes = cursor.fetchall()

            sql5 = "select routeID, max(sequence) as sequence from route_path group by routeID"
            cursor.execute(sql5)
            max_progress = cursor.fetchall()

            return render_template("flights.html", items=items, cols=cols, routes=routes, airlines=airlines, airplanes=airplanes, max_progress=max_progress, success='')
    except Exception as e:
        return render_template("flights.html", items=[], cols=[], success='Error: ' + str(e))

@app.route('/addFlightReq', methods=['GET'])
def add_flights():
    flightID = request.args.get('flightID')
    routeID = request.args.get('routeID')
    support_airline = request.args.get('support_airline')
    support_tail = request.args.get('support_tail')
    progress = request.args.get('progress')
    next_time = request.args.get('next_time')
    cost = request.args.get('cost')
    try:
        if progress is not None:
            progress = int(progress.strip())
        if cost is not None:
            cost = int(cost.strip())
    except ValueError:
        return render_template("flights.html", success='Invalid input given.')

    if not(flightID and routeID and support_airline and support_tail and progress and next_time and cost):
        return render_template("flights.html", success='All fields are required.')

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM flight WHERE flightID = %s", (flightID))
            if cursor.fetchone():
                return render_template("flights.html", success='Duplicate entry.')

            args = (flightID, routeID, support_airline, support_tail, progress, next_time, cost)
            cursor.callproc('offer_flight', args)
            connection.commit()
            return redirect('/flights')

    except MySQLError as e:
        return render_template("flights.html", success=f'Can\'t complete: {e}')
    except Exception as e:
        return render_template("flights.html", success=f'Error: {e}')
@app.route('/flights/<flightID>')
def flight(flightID):
    try:
        with connection.cursor() as cursor:
            sql = "select t1.support_airline, t1.flightID, t1.support_tail, t1.airplane_status, t1.routeID, t1.progress, " \
                "t3.departure, t3.arrival, t1.next_time, t1.cost " \
                "from flight t1 left join route_path t2 on t1.routeID = t2.routeID and t1.progress = t2.sequence " \
                f"left join leg t3 on t2.legID = t3.legID where t1.flightID = '{flightID}'"

            cols = ['airlineid', 'tail_num', 'seat_capacity', 'speed', 'locationID', 'plane_type', 'skids',
                    'propellers', 'jet_engines']
            cursor.execute(sql)
            items = cursor.fetchall()

            sql2 = "select t1.personID, concat(t2.first_name, ' ', t2.last_name) as name from pilot t1 join person t2 " \
                "on t1.personID = t2.personID where t1.commanding_flight is null"
            
            cursor.execute(sql2)
            pilots = cursor.fetchall()

            return render_template("flight.html", items=items, cols=cols, pilots=pilots, flightID=flightID, success='')
    except Exception as e:
        return render_template("flight.html", items=[], cols=[], success='Error: ' + str(e))
    
@app.route('/flights/<flightID>/takeoff')
def takeoff(flightID):
    try:
        with connection.cursor() as cursor:
            args = (flightID,)
            cursor.callproc('flight_takeoff', args)
            connection.commit()
            return redirect(f'/flights/{flightID}')
    except Exception as e:
        return redirect(f'/flights/{flightID}')
    
@app.route('/flights/<flightID>/landing')
def landing(flightID):
    try:
        with connection.cursor() as cursor:
            args = (flightID,)
            cursor.callproc('flight_landing', args)
            connection.commit()
            return redirect(f'/flights/{flightID}')
    except Exception as e:
        return redirect(f'/flights/{flightID}')
    
@app.route('/flights/<flightID>/board')
def board(flightID):
    try:
        with connection.cursor() as cursor:
            args = (flightID,)
            cursor.callproc('passengers_board', args)
            connection.commit()
            return redirect(f'/flights/{flightID}')
    except Exception as e:
        return redirect(f'/flights/{flightID}')
    
@app.route('/flights/<flightID>/disembark')
def disembark(flightID):
    try:
        with connection.cursor() as cursor:
            args = (flightID,)
            cursor.callproc('passengers_disembark', args)
            connection.commit()
            return redirect(f'/flights/{flightID}')
    except Exception as e:
        return redirect(f'/flights/{flightID}')
    
@app.route('/flights/<flightID>/assignPilotReq')
def assign_pilot(flightID):
    try:
        with connection.cursor() as cursor:
            personID = request.args.get('personID').strip()
            args = (flightID, personID)
            cursor.callproc('assign_pilot', args)
            connection.commit()
            return redirect(f'/flights/{flightID}')
    except Exception as e:
        return redirect(f'/flights/{flightID}')
    
@app.route('/flights/<flightID>/recycleCrew')
def recycle_crew(flightID):
    try:
        with connection.cursor() as cursor:
            args = (flightID,)
            cursor.callproc('recycle_crew', args)
            connection.commit()
            return redirect(f'/flights/{flightID}')
    except Exception as e:
        return redirect(f'/flights/{flightID}')
    
@app.route('/flights/<flightID>/retireFlight')
def retire_flight(flightID):
    try:
        with connection.cursor() as cursor:
            args = (flightID,)
            cursor.callproc('retire_flight', args)
            connection.commit()
            return redirect(f'/flights')
    except Exception as e:
        return redirect(f'/flights/{flightID}')
    
@app.route('/views')
def views():
    try:
        with connection.cursor() as cursor:
            sql1 = "SELECT * FROM flights_in_the_air"
            flightsInAirCols = ['departing_from', 'arriving_at', 'num_flights', 'flight_list', 'earliest_arrival',
                    'latest_arrival', 'airplane_list']
            cursor.execute(sql1)
            flightsInAir = cursor.fetchall()

            sql2 = "SELECT * FROM flights_on_the_ground"
            flightsOnGroundCols = ['departing_from', 'num_flights', 'flight_list', 'earliest_arrival',
                    'latest_arrival', 'airplane_list']
            cursor.execute(sql2)
            flightsOnGround = cursor.fetchall()

            sql3 = "SELECT * FROM people_in_the_air"
            peopleInAirCols = ['departing_from', 'arriving_at', 'num_airplanes', 'airplane_list',
                    'flight_list', 'earliest_arrival', 'latest_arrival', 'num_pilots', 'num_passengers', 'joint_pilots_passengers', 'person_list']
            cursor.execute(sql3)
            peopleInAir = cursor.fetchall()

            sql4 = "SELECT * FROM people_on_the_ground"
            peopleOnGroundCols = ['departing_from', 'airport', 'airport_name', 'city',
                    'state', 'country', 'num_pilots', 'num_passengers', 'joint_pilots_passengers', 'person_list']
            cursor.execute(sql4)
            peopleOnGround = cursor.fetchall()

            sql5 = "SELECT * FROM route_summary"
            routeSummaryCols = ['route', 'num_legs', 'leg_sequence', 'route_length',
                    'num_flights', 'flight_list', 'airport_sequence']
            cursor.execute(sql5)
            routeSummary = cursor.fetchall()

            sql6 = "SELECT * FROM alternative_airports"
            alternativeAirportCols = ['city', 'state', 'country', 'num_airports',
                    'airport_code_list', 'airport_name_list']
            cursor.execute(sql6)
            alternativeAirport = cursor.fetchall()

            return render_template("views.html", flightsInAirCols=flightsInAirCols, flightsInAir=flightsInAir, 
                                   flightsOnGroundCols=flightsOnGroundCols, flightsOnGround=flightsOnGround,
                                   peopleInAirCols=peopleInAirCols, peopleInAir=peopleInAir,
                                   peopleOnGroundCols=peopleOnGroundCols, peopleOnGround=peopleOnGround,
                                   routeSummaryCols=routeSummaryCols, routeSummary=routeSummary,
                                   alternativeAirportCols=alternativeAirportCols, alternativeAirport=alternativeAirport,
                                   success='')
    except Exception as e:
        return render_template("views.html", flightsInAirCols=[], flightsInAir=[], flightsOnGroundCols=[], flightsOnGround=[],
                                   peopleInAirCols=[], peopleInAir=[], peopleOnGroundCols=[], peopleOnGround=[],
                                   routeSummaryCols=[], routeSummary=[], alternativeAirportCols=[], alternativeAirport=[],
                               success='Error: ' + str(e))
    
@app.route('/simulationCycle')
def simulation_cycle():
    try:
        with connection.cursor() as cursor:
            cursor.callproc('simulation_cycle', None)
            connection.commit()
            return redirect(f'/views')
    except Exception as e:
        return redirect(f'/views')