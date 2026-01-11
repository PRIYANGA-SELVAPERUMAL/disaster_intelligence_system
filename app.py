import streamlit as st
import json, os
import folium
from streamlit_folium import st_folium
from stable_baselines3 import PPO

# ---------------- CONFIG ----------------
st.set_page_config(page_title="National Disaster Command Center", layout="wide")

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_world():
    return json.load(open("phase6_world_corrected.json"))

world = load_world()

# ---------------- LOAD PPO MODEL ----------------
@st.cache_resource
def load_model():
    return PPO.load("ppo_streamlit_ready.zip")

model = load_model()

# ---------------- UI ----------------
st.title("🚨 National Disaster Command Center")
st.markdown("### AI-Powered Disaster Intelligence & Relief Planning System")

# ---------------- MAP ----------------
st.subheader("🌍 Live Disaster & Relief Hub Map")
m = folium.Map(location=[20, 0], zoom_start=2)

for z in world:
    dz = z["disaster_zone"]
    folium.CircleMarker(
        location=[dz["lat"], dz["lon"]],
        radius=8,
        popup=f"Zone {dz['zone']} | Population: {int(dz['population'])}",
        color="red",
        fill=True,
    ).add_to(m)

st_folium(m, width=1100, height=500)

# ---------------- SIMULATOR ----------------
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
st.subheader("📊 Zone Status")

rows = []
for item in sim:
    z = item["disaster_zone"]
    h = item["relief_hub"]
    rows.append({
        "Zone": z["zone"],
        "Remaining Population": int(z["population"]),
        "Ambulances": h["A"],
        "Shelters": h["S"]
    })

st.dataframe(rows, use_container_width=True)
