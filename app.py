from flask import Flask, request, jsonify
import pandas as pd
import requests

app = Flask(__name__)

# -------------------------
# LOAD YOUR DATASET
# -------------------------
# Make sure crop_data.csv exists in the same folder
df = pd.read_csv("Crops_data.csv")

# -------------------------
# API KEY (CHANGE THIS)
# -------------------------
WEATHER_KEY = "6a64717361a76c8882ab659c34e88c82"

# -------------------------
# MAIN WEBHOOK
# -------------------------
@app.post("/webhook")
def webhook():
    req = request.get_json()
    intent = req["queryResult"]["intent"]["displayName"]
    params = req["queryResult"]["parameters"]

    crop = params.get("crop")
    state = params.get("state")
    year = params.get("year")
    parameter = params.get("parameter")
    
    # -----------------------------
    # 1. REAL-TIME WEATHER INTENT
    # -----------------------------
    if intent == "weather.intent":
        city = params.get("geo-city")

        if not city:
            return jsonify({"fulfillmentText": "Please specify a city."})

        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_KEY}&units=metric"
        data = requests.get(url).json()

        # Handle city not found
        if data.get("cod") != 200:
            return jsonify({"fulfillmentText": "City not found. Try again."})

        temp = data["main"]["temp"]
        hum = data["main"]["humidity"]
        desc = data["weather"][0]["description"]

        return jsonify({
            "fulfillmentText":
                f"Weather Report for {city}:\n"
                f"🌡 Temperature: {temp}°C\n"
                f"💧 Humidity: {hum}%\n"
                f"☁ Condition: {desc.capitalize()}"
        })

    # -----------------------------
    # 2. CROP DATA QUERY (Yield/Area/Production)
    # -----------------------------
    if intent == "crop.yield.intent":
        try:
            filtered = df[
                (df["Crop"].str.lower() == crop.lower()) &
                (df["State"].str.lower() == state.lower()) &
                (df["Year"] == int(year))
            ]
        except:
            return jsonify({"fulfillmentText": "Invalid query parameters."})

        if filtered.empty:
            return jsonify({"fulfillmentText": "No matching data found in dataset."})

        # Capitalize parameter for column name
        col = parameter.capitalize()

        if col not in filtered.columns:
            return jsonify({"fulfillmentText": "Invalid parameter type."})

        value = filtered.iloc[0][col]

        return jsonify({
            "fulfillmentText":
                f"{parameter.capitalize()} of {crop} in {state} ({year}) is **{value}**."
        })

    # -----------------------------
    # 3. CROP COMPARISON
    # -----------------------------
    if intent == "compare.crops.intent":
        crop1 = params.get("crop")
        crop2 = params.get("crop2")

        # Filter dataset
        d1 = df[
            (df["Crop"].str.lower() == crop1.lower()) &
            (df["State"].str.lower() == state.lower()) &
            (df["Year"] == int(year))
        ]

        d2 = df[
            (df["Crop"].str.lower() == crop2.lower()) &
            (df["State"].str.lower() == state.lower()) &
            (df["Year"] == int(year))
        ]

        if d1.empty or d2.empty:
            return jsonify({"fulfillmentText": "Comparison data not found."})

        val1 = d1.iloc[0]["Yield"]
        val2 = d2.iloc[0]["Yield"]

        return jsonify({
            "fulfillmentText":
                f"Crop Comparison in {state} ({year}):\n"
                f"🌾 {crop1}: {val1} Yield\n"
                f"🌽 {crop2}: {val2} Yield"
        })

    # -----------------------------
    # Default fallback
    # -----------------------------
    return jsonify({"fulfillmentText": "Your query is being processed..."})

# Run locally
if __name__ == "__main__":
    app.run(port=3000, debug=True)