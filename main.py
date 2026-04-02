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

#ajetaan:
if __name__ == "__main__":
    app.run(debug=True)