import streamlit as st
import json, zipfile, os
import folium
from streamlit_folium import st_folium
from stable_baselines3 import PPO
import numpy as np

# ----------------- Load PPO Brain -----------------

if not os.path.exists("ppo_brain"):
    with zipfile.ZipFile("ppo_streamlit_ready.zip", "r") as z:
        z.extractall("ppo_brain")

model = PPO.load("ppo_brain")

# ----------------- Load World -----------------

world = json.load(open("phase6_world_corrected.json"))

# ----------------- Streamlit Config -----------------

st.set_page_config(page_title="National Disaster Command Center", layout="wide")
st.title("🚨 National Disaster Command Center")
st.markdown("AI Powered Disaster Intelligence & Relief Planning System")

# ----------------- MAP -----------------

st.subheader("🌍 Live Disaster & Relief Hub Map")
m = folium.Map(location=[20,0], zoom_start=2)

for item in world:
    z = item["disaster_zone"]
    h = item["relief_hub"]
    folium.CircleMarker(
        location=[z["lat"], z["lon"]],
        radius=8,
        popup=f"Zone {z['zone']} | Pop {int(z['population'])} | A:{h['A']} T:{h['T']} S:{h['S']}",
        color="red", fill=True
    ).add_to(m)

st_folium(m, width=1200, height=500)

# ----------------- PPO Decision -----------------

def ppo_decide(z, h):
    obs = np.array([
        z["risk"], z["urgency"], z["population"],
        h["A"], h["T"], h["S"]
    ]).reshape(1, -1)
    action, _ = model.predict(obs, deterministic=True)
    return int(action)

# ----------------- Simulator -----------------

st.subheader("🧠 PPO Relief Allocation Simulator")

extraA = st.slider("Add Ambulances", 0, 200, 0)
extraS = st.slider("Add Shelters", 0, 200, 0)

sim = json.loads(json.dumps(world))
total_saved = 0

for item in sim:
    item["relief_hub"]["A"] += extraA
    item["relief_hub"]["S"] += extraS

for _ in range(30):
    for item in sim:
        z = item["disaster_zone"]
        h = item["relief_hub"]

        if z["population"] <= 0:
            continue

        action = ppo_decide(z, h)

        if action == 0:
            continue
        elif action == 1:
            factor = 0.3
        elif action == 2:
            factor = 0.6
        else:
            factor = 1.0

        capacity = min(h["A"]*50, h["T"]*60, h["S"]*20)
        batch = int(min(z["population"], capacity * factor))

        z["population"] -= batch
        total_saved += batch

# ----------------- Output -----------------

st.success(f"🛟 Predicted Lives Saved: {int(total_saved)}")

# ----------------- Zone Table -----------------

st.subheader("📊 Zone Status")

rows = []
for item in sim:
    z = item["disaster_zone"]
    h = item["relief_hub"]
    rows.append([z["zone"], int(z["population"]), h["A"], h["S"]])

st.dataframe(rows, use_container_width=True)
