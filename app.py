import streamlit as st
import json, zipfile, os
import folium
from streamlit_folium import st_folium
import numpy as np
from stable_baselines3 import PPO

# ---------------- Load Files ----------------
if not os.path.exists("ppo_brain"):
    with zipfile.ZipFile("ppo_streamlit_ready.zip", "r") as z:
        z.extractall("ppo_brain")

model = PPO.load("ppo_brain")

world = json.load(open("phase6_world_corrected.json"))

# ---------------- UI ----------------
st.set_page_config(page_title="National Disaster Command Center", layout="wide")
st.title("🚨 National Disaster Command Center")
st.markdown("AI Powered Disaster Intelligence & Relief Planning System")

# ---------------- MAP ----------------
m = folium.Map(location=[20,0], zoom_start=2)
for z in world:
    dz = z["disaster_zone"]
    folium.CircleMarker(
        location=[dz["lat"], dz["lon"]],
        radius=8,
        popup=f"Zone {dz['zone']} | Population: {int(dz['population'])}",
        color="red",
        fill=True,
    ).add_to(m)

st.subheader("🌍 Live Disaster Risk Map")
st_folium(m, width=1100, height=500)

# ---------------- PPO SIM ----------------
st.subheader("🧠 PPO Relief Allocation Simulator")

extra_amb = st.slider("Add Ambulances", 0, 200, 0)
extra_shel = st.slider("Add Shelters", 0, 200, 0)

sim = json.loads(json.dumps(world))
total_saved = 0

for item in sim:
    item["relief_hub"]["A"] += extra_amb
    item["relief_hub"]["S"] += extra_shel

for _ in range(15):
    for item in sim:
        z = item["disaster_zone"]
        h = item["relief_hub"]

        if z["population"] <= 0:
            continue

        state = np.array([
            z["severity"],
            z["urgency"],
            z["population"]/1000,
            h["A"]/100,
            h["T"]/100,
            h["S"]/100,
            z["distance"]/100,
            z["accessibility"]
        ], dtype=np.float32)

        action, _ = model.predict(state)
        save_ratio = float(action[0])  # 0–1

        capacity = min(h["A"]*50, h["T"]*60, h["S"]*20)
        batch = int(min(z["population"], capacity * save_ratio))

        z["population"] -= batch
        total_saved += batch

st.success(f"🎯 PPO Predicted Lives Saved: {int(total_saved)}")

# ---------------- TABLE ----------------
import pandas as pd
rows = []
for item in sim:
    dz = item["disaster_zone"]
    h = item["relief_hub"]
    rows.append([dz["zone"], int(dz["population"]), h["A"], h["S"]])

df = pd.DataFrame(rows, columns=["Zone","Remaining Population","Ambulances","Shelters"])
st.subheader("📊 Zone Status")
st.dataframe(df, use_container_width=True)
