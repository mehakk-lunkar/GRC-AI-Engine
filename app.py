from flask import Flask, render_template, request, redirect, url_for, flash
import requests

app = Flask(__name__)
app.secret_key = 'a8f9d7e6c3b2a1d0f4e5g6h7j8k9l0m1'

API_URL = "http://localhost:8000/api/ai-engine/v1/lookup"

@app.route("/", methods=["GET", "POST"])
def index():
    tools = []
    if request.method == "POST":
        task = request.form.get("task")
        compliance = request.form.get("compliance")
        jwt_token = request.form.get("jwt_token")

        if not task or not compliance or not jwt_token:
            flash("Please fill in all fields including JWT token.", "error")
            return redirect(url_for("index"))

        headers = {"Authorization": f"Bearer {jwt_token}"}
        payload = {"task": task, "compliance": compliance}

        try:
            response = requests.post(API_URL, json=payload, headers=headers)
            if response.status_code == 200:
                tools = response.json()
            else:
                try:
                    error_response = response.json()

                    if isinstance(error_response, dict) and isinstance(error_response.get("detail"), list):
                        for err in error_response["detail"]:
                            if "msg" in err:
                                msg = err["msg"].replace("Value error, ", "")
                                flash(msg, "error")

                    elif isinstance(error_response, list) and all("msg" in item for item in error_response):
                        for error_item in error_response:
                            msg = error_item["msg"].replace("Value error, ", "")
                            flash(msg, "error")
                    elif isinstance(error_response, dict) and "detail" in error_response:
                        flash(error_response["detail"], "error")
                    else:
                        flash("An unknown error occurred.", "error")
                except ValueError:
                    flash("An error occurred and the response could not be parsed.", "error")

        except Exception as e:
            flash(f"Request failed: {str(e)}", "error")

    return render_template("index.html", tools=tools)

if __name__ == "__main__":
    app.run(debug=True)
