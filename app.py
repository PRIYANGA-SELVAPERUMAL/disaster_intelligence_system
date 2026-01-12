import streamlit as st
import json
import requests
import folium
from datetime import datetime
from streamlit_folium import st_folium
from stable_baselines3 import PPO

# ---------------- CONFIG ----------------
st.set_page_config(page_title="National Disaster Command Center", layout="wide")
st.title("🚨 National Disaster Command Center")
st.markdown("AI-Powered Disaster Intelligence & Relief Planning System")

# ---------------- LOAD DATA ----------------
@st.cache_resource
def load_world():
    return json.load(open("phase6_world_corrected.json"))

@st.cache_resource
def load_model():
    return PPO.load("ppo_final_model.zip")

@st.cache_data(ttl=300)
def get_live_earthquakes():
    url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
    data = requests.get(url).json()
    quakes = []
    for f in data["features"]:
        p = f["properties"]
        g = f["geometry"]
        quakes.append({
            "place": p["place"],
            "mag": p["mag"],
            "time": datetime.utcfromtimestamp(p["time"]/1000),
            "lat": g["coordinates"][1],
            "lon": g["coordinates"][0]
        })
    return quakes

world = load_world()
model = load_model()
quakes = get_live_earthquakes()

# ---------------- MAP ----------------
st.subheader("🌍 Live Disaster & Relief Hub Map")
m = folium.Map(location=[20, 0], zoom_start=2)

# Disaster zones
for z in world:
    dz = z["disaster_zone"]
    folium.CircleMarker(
        location=[dz["lat"], dz["lon"]],
        radius=8,
        color="red",
        fill=True,
        popup=f"Zone {dz['zone']} | Population: {int(dz['population'])}"
    ).add_to(m)

# Live earthquakes
for q in quakes:
    if q["mag"] is None:
        continue
    folium.CircleMarker(
        location=[q["lat"], q["lon"]],
        radius=min(15, q["mag"] * 3),
        color="orange",
        fill=True,
        popup=f"🌋 {q['place']} | M {q['mag']}"
    ).add_to(m)

st_folium(m, height=500, use_container_width=True)

# ---------------- LIVE FEED ----------------
st.subheader("📡 Live Earthquake Feed")
st.dataframe(
    [{"Place": q["place"], "Magnitude": q["mag"], "Time (UTC)": q["time"]} for q in quakes if q["mag"]],
    use_container_width=True
)

# ---------------- PPO SIMULATOR ----------------
st.divider()
st.subheader("🧠 PPO Relief Allocation Simulator")

extra_amb = st.slider("Add Ambulances", 0, 200, 0)
extra_shel = st.slider("Add Shelters", 0, 200, 0)

sim = json.loads(json.dumps(world))
total_saved = 0

for item in sim:
    item["relief_hub"]["A"] += extra_amb
    item["relief_hub"]["S"] += extra_shel

for _ in range(20):
    for item in sim:
        z = item["disaster_zone"]
        h = item["relief_hub"]

        if z["population"] <= 0:
            continue

        max_batch = min(h["A"] * 50, h["T"] * 60, h["S"] * 20)
        batch = min(z["population"], max_batch)
        z["population"] -= batch
        total_saved += batch

st.success(f"🎯 Predicted Lives Saved: {int(total_saved)}")

# ---------------- ZONE TABLE ----------------
st.divider()
st.subheader("📊 Zone Status")

table = []
for item in sim:
    z = item["disaster_zone"]
    h = item["relief_hub"]
    table.append({
        "Zone": z["zone"],
        "Remaining Population": int(z["population"]),
        "Ambulances": h["A"],
        "Shelters": h["S"]
    })

st.dataframe(table, use_container_width=True)
