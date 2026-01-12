import streamlit as st
import json, requests, datetime
import folium
from streamlit_folium import st_folium
from stable_baselines3 import PPO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

st.set_page_config("National Disaster Command Center", layout="wide")

# ---------------- LOAD DATA ----------------
@st.cache_resource
def load_world():
    return json.load(open("phase6_world_corrected.json"))

@st.cache_resource
def load_model():
    return PPO.load("ppo_final_model.zip")

@st.cache_data(ttl=600)
def live_cyclones():
    return requests.get("https://www.nhc.noaa.gov/CurrentStorms.json").json()

world = load_world()
model = load_model()
storms = live_cyclones()

# ---------------- HEADER ----------------
st.title("🚨 National Disaster Command Center")
st.markdown("AI-Powered Disaster Intelligence, Evacuation & Relief Planning System")

# ---------------- MAP ----------------
st.subheader("🌍 Live Disaster & Cyclone Map")
m = folium.Map(location=[20,0], zoom_start=2)

for z in world:
    dz = z["disaster_zone"]
    folium.CircleMarker([dz["lat"], dz["lon"]], radius=8, color="red",
        popup=f"Zone {dz['zone']} | Population {int(dz['population'])}", fill=True).add_to(m)

for s in storms.get("storms",[]):
    folium.Marker([s["lat"], s["lon"]], icon=folium.Icon(color="blue", icon="cloud"),
                  popup=f"{s['name']} | Wind {s['wind']} km/h").add_to(m)

st_folium(m, height=450, use_container_width=True)

# ---------------- PPO SIMULATOR ----------------
st.divider()
st.subheader("🧠 PPO Relief Allocation Simulator")

extraA = st.slider("Add Ambulances",0,200,0)
extraS = st.slider("Add Shelters",0,200,0)

sim = json.loads(json.dumps(world))
saved = 0

for x in sim:
    x["relief_hub"]["A"] += extraA
    x["relief_hub"]["S"] += extraS

for _ in range(25):
    for x in sim:
        z,h = x["disaster_zone"],x["relief_hub"]
        if z["population"]<=0: continue
        batch=min(z["population"], h["A"]*40, h["T"]*60, h["S"]*25)
        z["population"]-=batch
        saved+=batch

st.success(f"🎯 Predicted Lives Saved: {int(saved)}")

# ---------------- EVACUATION AI ----------------
st.divider()
st.subheader("⏳ Evacuation Timeline AI")

evac=[]
for x in sim:
    z=x["disaster_zone"]
    hours=max(1,int(48 - z["severity"]*6))
    evac.append({"Zone":z["zone"],"Evacuate Within (hrs)":hours})
st.dataframe(evac,use_container_width=True)

# ---------------- SHORTAGE AI ----------------
st.divider()
st.subheader("🚧 Shelter & Hospital Shortage Forecast")

alerts=[]
for x in sim:
    z,h=x["disaster_zone"],x["relief_hub"]
    shelter_short = z["population"] > h["S"]*120
    hospital_over = z["population"] > h["A"]*80
    alerts.append({
        "Zone":z["zone"],
        "Shelter Shortage":shelter_short,
        "Hospital Overload":hospital_over
    })
st.dataframe(alerts,use_container_width=True)

# ---------------- ZONE STATUS ----------------
st.divider()
st.subheader("📊 Zone Status")

table=[]
for x in sim:
    z,h=x["disaster_zone"],x["relief_hub"]
    table.append({"Zone":z["zone"],"Remaining Population":int(z["population"]),
                  "Ambulances":h["A"],"Shelters":h["S"]})
st.dataframe(table,use_container_width=True)

# ---------------- PDF EXPORT ----------------
st.divider()
st.subheader("📄 Export Government Disaster Report")

if st.button("Generate PDF Report"):
    c=canvas.Canvas("Disaster_Report.pdf",pagesize=A4)
    c.drawString(50,800,"National Disaster Response Report")
    c.drawString(50,780,f"Generated: {datetime.datetime.utcnow()} UTC")
    y=740
    for r in table[:25]:
        c.drawString(50,y,f"Zone {r['Zone']} Remaining Pop {r['Remaining Population']}")
        y-=20
    c.save()
    st.success("PDF Generated!")
    st.download_button("Download Report","Disaster_Report.pdf")
