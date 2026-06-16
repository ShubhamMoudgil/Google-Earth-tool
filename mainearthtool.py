"""
Coord to KML - Streamlit Web App
Author: SMML
"""

import streamlit as st
import pandas as pd
import pyproj
import simplekml
import warnings
import io
import os

warnings.filterwarnings("ignore")

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Coordinates to Google Earth",
    page_icon="🌍",
    layout="centered",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #f0f4f8; }

    /* Title block */
    .title-block {
        background: linear-gradient(135deg, #1a73e8 0%, #0d47a1 100%);
        border-radius: 12px;
        padding: 28px 32px 20px 32px;
        margin-bottom: 28px;
        color: white;
    }
    .title-block h1 { color: white; margin: 0; font-size: 2rem; letter-spacing: -0.5px; }
    .title-block p  { color: #c8d8f5; margin: 6px 0 0 0; font-size: 0.95rem; }

    /* Card container */
    .card {
        background: white;
        border-radius: 10px;
        padding: 24px 28px;
        margin-bottom: 20px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }
    .card-title {
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #1a73e8;
        margin-bottom: 14px;
    }

    /* Step badges */
    .step-badge {
        display: inline-block;
        background: #e8f0fe;
        color: #1a73e8;
        border-radius: 50%;
        width: 26px; height: 26px;
        text-align: center;
        line-height: 26px;
        font-weight: 700;
        font-size: 0.85rem;
        margin-right: 8px;
    }

    /* Success / error banners */
    .success-box {
        background: #e6f4ea;
        border-left: 4px solid #34a853;
        border-radius: 6px;
        padding: 14px 18px;
        margin-top: 18px;
    }
    .error-box {
        background: #fce8e6;
        border-left: 4px solid #ea4335;
        border-radius: 6px;
        padding: 14px 18px;
        margin-top: 18px;
    }

    /* Download button */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #1a73e8, #0d47a1);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 28px;
        font-size: 1rem;
        font-weight: 600;
        width: 100%;
        margin-top: 8px;
        cursor: pointer;
        transition: opacity 0.2s;
    }
    .stDownloadButton > button:hover { opacity: 0.88; }

    /* Divider */
    hr { border: none; border-top: 1px solid #e0e0e0; margin: 20px 0; }

    /* Hide Streamlit branding */
    #MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="title-block">
    <h1>🌍 Coordinates to Google Earth</h1>
    <p>Convert UTM coordinates from an Excel file into a KML file ready for Google Earth.</p>
</div>
""", unsafe_allow_html=True)


# ── Core conversion function ───────────────────────────────────────────────────
def utm_to_latlon(df, zone_number, hemisphere_type):
    south = (hemisphere_type.lower() == "south")
    utm = pyproj.Proj(proj="utm", zone=zone_number, ellps="WGS84", south=south)
    wgs84 = pyproj.Proj(proj="latlong", datum="WGS84")
    transformer = pyproj.Transformer.from_proj(utm, wgs84)
    df[["Longitude", "Latitude"]] = df.apply(
        lambda row: transformer.transform(row["Easting"], row["Northing"]),
        axis=1,
        result_type="expand",
    )
    return df


def build_kml(df):
    kml = simplekml.Kml()
    for _, row in df.iterrows():
        northing  = float(row["Northing"])
        easting   = float(row["Easting"])
        longitude = float(row["Longitude"])
        latitude  = float(row["Latitude"])

        table_html = """
        <style>
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid black; padding: 8px; text-align: left; }}
        th {{ background-color: #e3f2fd; }}
        tr:nth-child(even) td {{ background-color: #ffffff; }}
        tr:nth-child(odd)  td {{ background-color: #e3f2fd; }}
        </style>
        <table>
            <tr><th>Point ID</th>  <td>{}</td></tr>
            <tr><th>Northing</th>  <td>{}</td></tr>
            <tr><th>Easting</th>   <td>{}</td></tr>
            <tr><th>Latitude</th>  <td>{:.6f}</td></tr>
            <tr><th>Longitude</th> <td>{:.6f}</td></tr>
        </table>
        """.format(row["BH_ID"], northing, easting, latitude, longitude)

        pnt = kml.newpoint()
        pnt.name        = str(row["BH_ID"])
        pnt.description = table_html
        pnt.coords      = [(longitude, latitude)]

    return kml


# ── Step 1 · Upload Excel ──────────────────────────────────────────────────────
st.markdown("""
<div class="card">
    <div class="card-title"><span class="step-badge">1</span> Upload Excel File</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Excel file must contain columns: **BH_ID**, **Northing**, **Easting**",
    type=["xlsx"],
    label_visibility="visible",
)

if uploaded_file:
    try:
        df_raw = pd.read_excel(uploaded_file)
        required_cols = {"BH_ID", "Northing", "Easting"}
        missing = required_cols - set(df_raw.columns)
        if missing:
            st.markdown(f'<div class="error-box">❌ Missing columns: <b>{", ".join(missing)}</b>. Please check your file.</div>', unsafe_allow_html=True)
            df_raw = None
        else:
            st.success(f"✅ {len(df_raw)} rows loaded successfully.")
            st.dataframe(df_raw.head(5), use_container_width=True)
    except Exception as e:
        st.markdown(f'<div class="error-box">❌ Could not read file: {e}</div>', unsafe_allow_html=True)
        df_raw = None
else:
    df_raw = None

st.markdown("</div>", unsafe_allow_html=True)


# ── Step 2 · UTM Settings ──────────────────────────────────────────────────────
st.markdown("""
<div class="card">
    <div class="card-title"><span class="step-badge">2</span> UTM Settings</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    zone_number = st.number_input(
        "Zone Number (1 – 60)",
        min_value=1, max_value=60, value=40, step=1,
    )
with col2:
    hemisphere_type = st.radio(
        "Hemisphere",
        options=["North", "South"],
        horizontal=True,
    )

st.markdown("</div>", unsafe_allow_html=True)


# ── Step 3 · KML File Name ─────────────────────────────────────────────────────
st.markdown("""
<div class="card">
    <div class="card-title"><span class="step-badge">3</span> Output File Name</div>
""", unsafe_allow_html=True)

kml_file_name = st.text_input(
    "KML file name (without extension)",
    value="output",
    placeholder="e.g. site_boreholes",
)

st.markdown("</div>", unsafe_allow_html=True)


# ── Step 4 · Convert & Download ────────────────────────────────────────────────
st.markdown("""
<div class="card">
    <div class="card-title"><span class="step-badge">4</span> Convert & Download</div>
""", unsafe_allow_html=True)

if st.button("🔄 Convert to KML", use_container_width=True):
    if df_raw is None:
        st.warning("⚠️ Please upload a valid Excel file first.")
    elif not kml_file_name.strip():
        st.warning("⚠️ Please enter a file name.")
    else:
        try:
            with st.spinner("Converting coordinates…"):
                df_converted = utm_to_latlon(df_raw.copy(), int(zone_number), hemisphere_type)
                kml_obj      = build_kml(df_converted)

                # Save KML to an in-memory buffer
                kml_buffer = io.BytesIO()
                kml_string = kml_obj.kml()
                kml_buffer.write(kml_string.encode("utf-8"))
                kml_buffer.seek(0)

            st.markdown('<div class="success-box">✅ Conversion complete! Click below to download your KML file.</div>', unsafe_allow_html=True)

            # Preview converted data
            st.subheader("Converted Coordinates Preview")
            st.dataframe(
                df_converted[["BH_ID", "Northing", "Easting", "Latitude", "Longitude"]].head(10),
                use_container_width=True,
            )

            # Metrics
            m1, m2, m3 = st.columns(3)
            m1.metric("Points converted", len(df_converted))
            m2.metric("UTM Zone", f"{int(zone_number)} {hemisphere_type[0]}")
            m3.metric("Output file", f"{kml_file_name.strip()}.kml")

            # Download button
            st.download_button(
                label="⬇️ Download KML File",
                data=kml_buffer,
                file_name=f"{kml_file_name.strip()}.kml",
                mime="application/vnd.google-earth.kml+xml",
                use_container_width=True,
            )

        except KeyError as e:
            st.markdown(f'<div class="error-box">❌ Column not found: {e}. Check your Excel headers.</div>', unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f'<div class="error-box">❌ Conversion failed: {e}</div>', unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("""
<hr>
<p style="text-align:center; color:#9e9e9e; font-size:0.8rem;">
    Coordinates to Google Earth · Built with Streamlit · SMML
</p>
""", unsafe_allow_html=True)