from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

@app.route('/', methods=['POST'])
def receive_alert():
    data = request.get_json(silent=True) or {}

    nginx_alert = any(
        alert.get('status') == 'firing'
        and alert.get('labels', {}).get('alertname') == 'NginxDown'
        for alert in data.get('alerts', [])
    )

    if not nginx_alert:
        return jsonify({"status": "ignored"}), 200

    result = subprocess.run(
        [
            "ansible-playbook",
            "-i", "/opt/self-healing/ansible/hosts",
            "/opt/self-healing/ansible/restart_nginx.yml"
        ],
        capture_output=True,
        text=True
    )

    return jsonify({
        "status": "success" if result.returncode == 0 else "failed",
        "output": result.stdout,
        "error": result.stderr
    }), 200 if result.returncode == 0 else 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001)
