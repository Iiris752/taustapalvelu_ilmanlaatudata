from flask import Flask, request, jsonify
import psycopg2
import os
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

load_dotenv()

app = Flask(__name__)

#tietokantayhteyst
def _get_conn():
    return psycopg2.connect(
        dbname=os.getenv("DB"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )

#päivän mittaustulokset:
#testaus selaimessa esim.: http://127.0.0.1:5000/measurements/day?location_id=2975&date=2026-01-15
@app.get("/measurements/day")
def get_day_measurements():
    location_id = request.args.get("location_id")
    date = request.args.get("date")

    #otetaan measurement taulu ja liitetään sensor tauluun
    #haetaan vain sille location id:lle kuuluvat rivit
    #haetaan vain siltä päivältä ja muunnetaan aikaleima pelkäksi päiväksi
    #sortataan aikajärjestykseen
    query = """
        SELECT m.measurement_id, m.sensor_id, s.parameter,
               m.value, m."datetimeUtc"
        FROM measurement m
        JOIN sensor s ON s.sensor_id = m.sensor_id
        WHERE m.location_id = %s
          AND m."datetimeUtc"::date = %s
        ORDER BY m."datetimeUtc"
    """

    #avataan yhteys tietokantaan ja luodaan kursori ja palautetaan avain-arvo sanakirja muodossa
    conn = _get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    #suoritetaan SQL kysely parametrisoituna location id ja date
    #SQL injectionista huolehdittu aiemmin
    cur.execute(query, (location_id, date))
    #haetaan SQL rivit
    rows = cur.fetchall()
    conn.close()

    #flask muuttaa listan jsoniksi
    return jsonify(rows)

#mittausten lukumäärä
#Testaus selaimeen: http://127.0.0.1:5000/measurements/count?location_id=2975
@app.get("/measurements/count")
def get_count_measurements():
    location_id = request.args.get("location_id")
    query = "SELECT COUNT(*) AS count FROM measurement WHERE location_id = %s"
    conn = _get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(query, (location_id,))
    row = cur.fetchone()
    conn.close()
    count = row["count"]

    return jsonify({"location_id": location_id, "count": count})


# sensorin päivittäinen keskiarvo
# esim. http://127.0.0.1:5000/measurements/avg?location_id=2975&sensor_id=2002989&date=2026-01-15
@app.get("/measurements/avg")
def get_sensor_avg():
    location_id = request.args.get("location_id")
    sensor_id = request.args.get("sensor_id")
    date = request.args.get("date")

    query = """
        SELECT AVG(value)
        FROM measurement
        WHERE location_id = %s
          AND sensor_id = %s
          AND "datetimeUtc"::date = %s
    """

    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(query, (location_id, sensor_id, date))
    avg_val = cur.fetchone()[0]
    conn.close()

    return jsonify({
        "location_id": location_id,
        "sensor_id": sensor_id,
        "date": date,
        "average": avg_val
    })


#ajetaan:
if __name__ == "__main__":
    app.run(debug=True)