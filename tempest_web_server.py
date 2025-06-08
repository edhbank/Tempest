import socket
import json
import threading
from datetime import datetime
from flask import Flask, jsonify, send_from_directory, render_template_string

app = Flask(__name__)
latest_data = {
    'obs_st': None,
    'rapid_wind': None,
    'evt_precip': None
}

UDP_PORT = 50222

def c_to_f(c): return (c * 9 / 5) + 32
def mps_to_mph(mps): return mps * 2.23694
def mm_to_inches(mm): return mm / 25.4
def mbar_to_inhg(mbar): return mbar * 0.02953

def listen_udp():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', UDP_PORT))
    print(f"?? Listening for Tempest UDP packets on port {UDP_PORT}...")

    while True:
        raw_data, addr = sock.recvfrom(4096)
        try:
            message = json.loads(raw_data.decode('utf-8'))
            msg_type = message.get('type')
            if msg_type in latest_data:
                latest_data[msg_type] = message
        except Exception as e:
            print("?? Error decoding UDP packet:", e)

@app.route('/')
def serve_ui():
   return send_from_directory('static', 'index.html')

@app.route('/data.json')
def serve_data():
    def safe(obs):
        if not obs:
            return None
        if obs.get('type') == 'obs_st':
            data = obs.get('obs', [[]])[0]
            return {
            	'time': datetime.utcfromtimestamp(data[0]).strftime('%Y-%m-%d %I:%M:%S %p'),
                'temperature': round(c_to_f(data[7]), 1),
                'humidity': data[8],
                'wind_avg': round(mps_to_mph(data[2]), 1),
                'wind_dir': (data[3]*100),
                'rain': round(mm_to_inches(data[12]), 2),
                'pressure': round(mbar_to_inhg(data[6]), 2)
            }
        elif obs.get('type') == 'rapid_wind':
            ob = obs.get('ob', [])
            return {
                'speed': round(mps_to_mph(ob[1]), 1),
                'direction': ob[2]
            }
        elif obs.get('type') == 'evt_precip':
            return {
                'time': datetime.utcfromtimestamp(obs['evt'][0]).strftime('%Y-%m-%d %I:%M:%S %p')
            }
        return None

    return jsonify({
        'obs_st': safe(latest_data['obs_st']),
        'rapid_wind': safe(latest_data['rapid_wind']),
        'evt_precip': safe(latest_data['evt_precip'])
    })
def index():
    obs_st = latest_data['obs_st']
    rapid_wind = latest_data['rapid_wind']
    evt_precip = latest_data['evt_precip']

    def format_obs(obs):
        if not obs: return "<p>No observation data yet.</p>"
        data = obs.get('obs', [[]])[0]
        ts = datetime.utcfromtimestamp(data[0]).strftime('%Y-%m-%d %I:%M:%S %p')
        return f"""
        <h2>?? Standard Observation</h2>
        <p><strong>Device:</strong> {obs['serial_number']}<br>
        <strong>Time:</strong> {ts}</p>
        <ul>
            <li>??? Time: {data[0]:.1f}</li>
            <li>??? Temperature: {c_to_f(data[7]):.1f} F</li>
            <li>?? Humidity: {data[8]:.0f} %</li>
            <li>??? Wind Avg: {mps_to_mph(data[2]):.1f} mph from {data[3]}</li>
            <li>?? Wind Gust: {mps_to_mph(data[4]):.1f} mph</li>
            <li>? Rain Today: {mm_to_inches(data[12]):.2f} in</li>
            <li>?? Pressure: {mbar_to_inhg(data[6]):.2f} inHg</li>
        </ul>
        """

    def format_rapid(obs):
        if not obs: return "<p>No rapid wind data yet.</p>"
        data = obs.get('ob', [])
        ts = datetime.utcfromtimestamp(data[0]).strftime('%Y-%m-%d %I:%M:%S %p')
        return f"""
        <h2>?? Rapid Wind</h2>
        <p><strong>Device:</strong> {obs['serial_number']}<br>
        <strong>Time:</strong> {ts}</p>
        <ul>
            <li>??? Speed: {mps_to_mph(data[1]):.1f} mph</li>
            <li>?? Direction: {data[2]} </li>
        </ul>
        """

    def format_precip(evt):
        if not evt: return "<p>No rain event yet.</p>"
        ts = datetime.utcfromtimestamp(evt['evt'][0]).strftime('%Y-%m-%d %I:%M:%S %p')
        return f"""
        <h2>? Rain Event</h2>
        <p><strong>Device:</strong> {evt['serial_number']}<br>
        <strong>Rain started at:</strong> {ts}</p>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Tempest Weather Station</title>
        <meta http-equiv="refresh" content="10">
        <style>
            body {{
                font-family: 'Segoe UI', sans-serif;
                background: #f0f4f8;
                color: #333;
                padding: 20px;
                max-width: 800px;
                margin: auto;
            }}
            h1 {{
                color: #0056b3;
            }}
            h2 {{
                color: #333;
                border-bottom: 1px solid #ccc;
                padding-bottom: 5px;
            }}
            ul {{
                list-style: none;
                padding-left: 0;
            }}
            li {{
                padding: 4px 0;
            }}
            .section {{
                background: white;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(0,0,0,0.05);
                padding: 15px 20px;
                margin-bottom: 20px;
            }}
        </style>
    </head>
    <body>
        <h1>??? Tempest Weather Dashboard</h1>
        <div class="section">{format_obs(obs_st)}</div>
        <div class="section">{format_rapid(rapid_wind)}</div>
        <div class="section">{format_precip(evt_precip)}</div>
        <p style="text-align:center; font-size: 0.9em; color: #888;">Auto-refreshes every 10 seconds</p>
    </body>
    </html>
    """
    return render_template_string(html)

def start_web_and_udp():
    udp_thread = threading.Thread(target=listen_udp, daemon=True)
    udp_thread.start()
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == '__main__':
    start_web_and_udp()