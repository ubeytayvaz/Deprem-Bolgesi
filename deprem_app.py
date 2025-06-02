import streamlit as st
import pandas as pd
import requests
from fpdf import FPDF
import tempfile
import os

# Veriyi oku
df = pd.read_excel("Deprem Bölgesi Bulma-Tariffeq.xlsx", sheet_name="Veri")
df = df[["ILADI", "ILCEADI", "KOYADI", "MAHADI", "Yeni Sınıf"]].dropna()

st.title("Deprem Bölgesi Sorgulama")

st.subheader("1. Adres Bilgisiyle Sorgulama")

# 1. İl Seçimi
selected_il = st.selectbox("İl Seçin", sorted(df["ILADI"].unique()))

# 2. İlçe Seçimi
ilce_options = df[df["ILADI"] == selected_il]["ILCEADI"].unique()
selected_ilce = st.selectbox("İlçe Seçin", sorted(ilce_options))

# 3. Köy/Bucak Seçimi
koy_options = df[(df["ILADI"] == selected_il) & (df["ILCEADI"] == selected_ilce)]["KOYADI"].unique()
selected_koy = st.selectbox("Köy/Bucak Seçin", sorted(koy_options))

# 4. Mahalle Seçimi
mah_options = df[
    (df["ILADI"] == selected_il) &
    (df["ILCEADI"] == selected_ilce) &
    (df["KOYADI"] == selected_koy)
]["MAHADI"].unique()
selected_mah = st.selectbox("Mahalle Seçin", sorted(mah_options))

# 5. Deprem Bölgesi (Yeni Sınıf)
result = df[
    (df["ILADI"] == selected_il) &
    (df["ILCEADI"] == selected_ilce) &
    (df["KOYADI"] == selected_koy) &
    (df["MAHADI"] == selected_mah)
]["Yeni Sınıf"].values

if len(result) > 0:
    st.success(f"Bu yerleşime ait Deprem Bölgesi Sınıfı: {result[0]}")

    if st.button("PDF Olarak İndir"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Deprem Bölgesi Sorgu Sonucu", ln=True, align="C")
        pdf.ln(10)
        pdf.cell(200, 10, txt=f"İl: {selected_il}", ln=True)
        pdf.cell(200, 10, txt=f"İlçe: {selected_ilce}", ln=True)
        pdf.cell(200, 10, txt=f"Köy/Bucak: {selected_koy}", ln=True)
        pdf.cell(200, 10, txt=f"Mahalle: {selected_mah}", ln=True)
        pdf.cell(200, 10, txt=f"Deprem Bölgesi Sınıfı: {result[0]}", ln=True)

        temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf.output(temp_pdf.name)
        st.download_button(label="PDF'i İndir", data=open(temp_pdf.name, "rb"), file_name="deprem_bolgesi.pdf")
        temp_pdf.close()
else:
    st.warning("Seçilen bilgilerle eşleşen veri bulunamadı.")

st.markdown("---")

st.subheader("2. Koordinat ile Sorgulama")
lat = st.text_input("Enlem (Latitude)", "")
lon = st.text_input("Boylam (Longitude)", "")

def reverse_geocode_osm(lat, lon):
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&addressdetails=1"
    headers = {"User-Agent": "DepremTariffeqApp"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json().get("address", {})
        return {
            "il": data.get("state", "").upper(),
            "ilce": data.get("county", "").upper(),
            "koy": data.get("village", "").upper(),
            "mahalle": data.get("neighbourhood", "") or data.get("suburb", "") or data.get("quarter", "")
        }
    return {}

if lat and lon:
    try:
        location = reverse_geocode_osm(lat, lon)
        il = location.get("il", "")
        ilce = location.get("ilce", "")
        koy = location.get("koy", "")
        mahalle = location.get("mahalle", "").upper()

        st.write(f"📍 Bulunan Yer: {mahalle.title()}, {koy.title()}, {ilce.title()}, {il.title()}")

        result_koord = df[
            (df["ILADI"] == il) &
            (df["ILCEADI"] == ilce) &
            (df["KOYADI"].str.upper().str.contains(koy)) &
            (df["MAHADI"].str.upper().str.contains(mahalle))
        ]

        if not result_koord.empty:
            st.success(f"Bu koordinata ait Deprem Bölgesi Sınıfı: {result_koord['Yeni Sınıf'].iloc[0]}")
        else:
            st.warning("\u26a0\ufe0f Bu koordinata ait mahalle veri kümesinde yok. Lütfen adres bilgisiyle sorgulayın.")
    except Exception as e:
        st.error(f"Hata oluştu: {e}")
