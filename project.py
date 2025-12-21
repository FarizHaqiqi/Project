import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Eco-Cost Analyzer", 
    page_icon="☀️",
    layout="wide"
)

# --- 2. CUSTOM CSS (Untuk Tampilan Lebih Cantik) ---
st.markdown("""
<style>
    /* Mengubah background aplikasi */
    .stApp {
        background: linear-gradient(to bottom right, #f8f9fa, #e9ecef);
    }
    
    /* Style untuk Banner */
    .hero-banner {
        background-image: linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.6)), url('https://images.unsplash.com/photo-1509391366360-2e959784a276?q=80&w=2072');
        background-size: cover;
        background-position: center;
        padding: 50px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 20px;
        color: white;
    }
    
    /* Info Box Style */
    .info-box {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #2ecc71;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# --- 3. KONSTANTA PROYEK ---
TARIF_PLN = 1400 
FILE_DATA = 'produksi_emisi_provinsi.csv' 
# REQUEST: Batasi Wp sampai 550
WP_CHOICES = [300, 350, 400, 450, 500, 550] 
MIN_PV_MODULES = 1 
# REQUEST: Batasi modul sampai 50
MAX_PV_MODULES = 50 
TAHUN_ANALISIS = 15 
ASUMSI_INFLASI_LISTRIK = 0.05 
BIAYA_AWAL_PV_PER_Wp = 15000 

# --- 4. FUNGSI UTILITY ---
def format_rupiah(x):
    if x >= 1e9: return f"Rp {x/1e9:,.2f} M"
    if x >= 1e6: return f"Rp {x/1e6:,.1f} Jt"
    return f"Rp {x:,.0f}"

@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_csv(file_path, delimiter=',')
        if len(df.columns) <= 2:
            df = pd.read_csv(file_path, delimiter=';')
        
        if df.columns[0].lower() in ['no', 'no.']:
            df = df.iloc[:, 1:].copy() 
            
        df.columns = ['Provinsi', 'Produksi_Harian_kWh', 'Faktor_Emisi_kg_per_kWh']
        
        for col in ['Produksi_Harian_kWh', 'Faktor_Emisi_kg_per_kWh']:
            if df[col].dtype == object: 
                df[col] = df[col].astype(str).str.replace(',', '.', regex=True)
                df[col] = df[col].astype(str).str.replace(' kWh/kWp', '', regex=False) 
            df[col] = pd.to_numeric(df[col], errors='coerce') 

        df.dropna(inplace=True) 
        return df
    except Exception as e:
        st.error(f"Error fatal: {e}")
        return pd.DataFrame()

data_solar = load_data(FILE_DATA)
if data_solar.empty: st.stop()

# --- 5. HEADER & BANNER ---
st.markdown("""
    <div class="hero-banner">
        <h1 style='color: white;'>☀️ Solar Eco-Cost Analyzer</h1>
        <p>Hitung Potensi Hemat Biaya & Jejak Karbon Anda Sekarang</p>
    </div>
""", unsafe_allow_html=True)

# --- 6. INPUT USER & INFO WILAYAH ---
st.subheader("⚙️ Parameter Instalasi")
col_input, col_info = st.columns([2, 1])

with col_input:
    c1, c2 = st.columns(2)
    with c1:
        provinsi_pilihan = st.selectbox("📍 Pilih Lokasi:", data_solar['Provinsi'].tolist())
        tagihan_input = st.number_input("💸 Tagihan Listrik (Rp/Bulan):", min_value=10000, value=500000, step=50000)
    
    with c2:
        wp_pilihan = st.selectbox("⚡ Kapasitas Panel (Wp):", WP_CHOICES, index=len(WP_CHOICES)-1)
        # REQUEST: Max value 50
        jumlah_modul = st.number_input("📦 Jumlah Modul (Max 50):", min_value=1, max_value=MAX_PV_MODULES, value=4)

# LOOKUP DATA
data_lokasi = data_solar[data_solar['Provinsi'] == provinsi_pilihan].iloc[0]
radiasi_harian = data_lokasi['Produksi_Harian_kWh']
faktor_emisi_lokal = data_lokasi['Faktor_Emisi_kg_per_kWh']

# REQUEST: Tampilkan PV Out dan Faktor Emisi
with col_info:
    st.markdown(f"""
    <div class="info-box">
        <h4 style="margin-top:0;">📊 Data Wilayah: {provinsi_pilihan}</h4>
        <p><b>☀️ Potensi Surya (PV Out):</b><br>{radiasi_harian} kWh/kWp/hari</p>
        <p><b>🏭 Faktor Emisi Grid:</b><br>{faktor_emisi_lokal} kg CO₂/kWh</p>
    </div>
    """, unsafe_allow_html=True)

# --- 7. PROSES ALGORITMA (LOGIKA ASLI DIPERTAHANKAN) ---
kapasitas_pv_wp = wp_pilihan * jumlah_modul
kapasitas_pv_kwp = kapasitas_pv_wp / 1000.0
tagihan_bulanan = tagihan_input

konsumsi_kwh = tagihan_bulanan / TARIF_PLN
produksi_pv_harian = radiasi_harian * kapasitas_pv_kwp 
produksi_pv_bulanan = produksi_pv_harian * 30

penghematan_rp = produksi_pv_bulanan * TARIF_PLN
emisi_dicegah_total = produksi_pv_bulanan * faktor_emisi_lokal 
skor_kemandirian = min((produksi_pv_bulanan / konsumsi_kwh) * 100, 100) 
tagihan_baru = max(tagihan_bulanan - penghematan_rp, 0)

# Payback Calculation
biaya_instalasi_pv = kapasitas_pv_wp * BIAYA_AWAL_PV_PER_Wp
biaya_kumulatif_tanpa_pv = []
biaya_kumulatif_dengan_pv = []
total_biaya_tanpa_pv = 0
total_biaya_dengan_pv = biaya_instalasi_pv 
payback_tahun = TAHUN_ANALISIS + 1 

tagihan_curr = tagihan_bulanan
tagihan_baru_curr = tagihan_baru

for tahun in range(1, TAHUN_ANALISIS + 1):
    tagihan_curr *= (1 + ASUMSI_INFLASI_LISTRIK)
    tagihan_baru_curr *= (1 + ASUMSI_INFLASI_LISTRIK)
    
    total_biaya_tanpa_pv += tagihan_curr * 12
    total_biaya_dengan_pv += tagihan_baru_curr * 12

    biaya_kumulatif_tanpa_pv.append(total_biaya_tanpa_pv)
    biaya_kumulatif_dengan_pv.append(total_biaya_dengan_pv)

    if total_biaya_dengan_pv <= total_biaya_tanpa_pv and payback_tahun > TAHUN_ANALISIS:
        payback_tahun = tahun
    
emisi_total_ton = emisi_dicegah_total * 12 * TAHUN_ANALISIS / 1000 
df_proyeksi = pd.DataFrame({'Tahun': range(1, TAHUN_ANALISIS + 1),'Tanpa PV': biaya_kumulatif_tanpa_pv,'Dengan PV': biaya_kumulatif_dengan_pv})

# Data Donut
emisi_awal_total = konsumsi_kwh * faktor_emisi_lokal 
emisi_dicegah_grafik = min(emisi_dicegah_total, emisi_awal_total) 
emisi_tersisa_pln = emisi_awal_total - emisi_dicegah_grafik

# --- 8. DASHBOARD METRIC ---
st.write("---")
m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("💰 Hemat Biaya/Bulan", format_rupiah(penghematan_rp), delta=f"Tagihan Baru: {format_rupiah(tagihan_baru)}")
with m2: st.metric("⏳ Balik Modal", f"{payback_tahun} Tahun" if payback_tahun <= TAHUN_ANALISIS else "> 15 Tahun")
with m3: st.metric("🌱 Reduksi CO₂/Bulan", f"{emisi_dicegah_total:.1f} kg")
with m4: st.metric("⚡ Kemandirian Energi", f"{skor_kemandirian:.1f}%")

# --- 9. VISUALISASI ---
st.write("")
tab1, tab2, tab3, tab4 = st.tabs(["📉 Grafik Biaya", "📈 Proyeksi ROI", "🌍 Analisis Emisi", "ℹ️ Detail Teknis"])

with tab1:
    st.subheader("Perbandingan Tagihan Listrik")
    fig_bar = px.bar(
        x=['Sebelum PV', 'Sesudah PV'], 
        y=[tagihan_bulanan, tagihan_baru],
        text=[format_rupiah(tagihan_bulanan), format_rupiah(tagihan_baru)],
        color=['Sebelum PV', 'Sesudah PV'],
        color_discrete_map={'Sebelum PV': '#34495e', 'Sesudah PV': '#2ecc71'}
    )
    fig_bar.update_layout(showlegend=False, xaxis_title="", yaxis_title="Rupiah")
    st.plotly_chart(fig_bar, use_container_width=True)

with tab2:
    st.subheader("Kapan Modal Anda Kembali?")
    df_melt = df_proyeksi.melt('Tahun', var_name='Skenario', value_name='Total Biaya')
    fig_line = px.line(df_melt, x='Tahun', y='Total Biaya', color='Skenario', markers=True,
                       color_discrete_map={'Tanpa PV': '#e74c3c', 'Dengan PV': '#2ecc71'})
    if payback_tahun <= TAHUN_ANALISIS:
        val_pb = df_proyeksi.loc[df_proyeksi['Tahun'] == payback_tahun, 'Dengan PV'].values[0]
        fig_line.add_scatter(x=[payback_tahun], y=[val_pb], mode='markers', marker=dict(size=12, color='blue'), name='Titik Balik Modal')
    fig_line.update_layout(yaxis_tickformat=",.0f")
    st.plotly_chart(fig_line, use_container_width=True)

with tab3:
    col_pie, col_desc = st.columns([1.5, 1])
    with col_pie:
        # REQUEST: Donut Chart yang lebih bagus (Pakai Plotly, bukan Matplotlib)
        labels = ['Dicegah (PV)', 'Sisa (PLN)']
        values = [emisi_dicegah_grafik, emisi_tersisa_pln]
        
        fig_donut = go.Figure(data=[go.Pie(
            labels=labels, values=values, hole=.6, 
            marker_colors=['#2ecc71', '#bdc3c7'],
            textinfo='percent', hoverinfo="label+value+percent"
        )])
        fig_donut.update_layout(title_text="Proporsi Pengurangan Emisi", margin=dict(t=30, b=0, l=0, r=0))
        # Text di tengah donut
        fig_donut.add_annotation(text=f"{skor_kemandirian:.0f}%", x=0.5, y=0.5, font_size=24, showarrow=False, font_color="#27ae60")
        st.plotly_chart(fig_donut, use_container_width=True)
        
    with col_desc:
        st.info(f"Sistem Anda mencegah **{emisi_dicegah_total:.1f} kg CO₂** per bulan.")
        st.write("Ini setara dengan:")
        st.write(f"🌳 Menanam **{int(emisi_dicegah_total/20)} pohon**")
        st.write(f"🚗 Menghindari perjalanan mobil sejauh **{int(emisi_dicegah_total*5)} km**")

with tab4:
    # REQUEST: Detail teknis jangan hilang
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### ⚙️ Spesifikasi Sistem")
        st.table(pd.DataFrame({
            "Parameter": ["Kapasitas Total", "Jumlah Modul", "Jenis Panel", "Produksi Energi"],
            "Nilai": [f"{kapasitas_pv_kwp:.2f} kWp", f"{jumlah_modul} Unit", f"{wp_pilihan} Wp", f"{produksi_pv_bulanan:.2f} kWh/bln"]
        }).set_index('Parameter'))
    with c2:
        st.markdown("### 💸 Analisis Finansial")
        st.table(pd.DataFrame({
            "Parameter": ["Investasi Awal", "Penghematan/Bulan", "Total Hemat (15 Thn)", "ROI"],
            "Nilai": [format_rupiah(biaya_instalasi_pv), format_rupiah(penghematan_rp), format_rupiah(total_biaya_tanpa_pv - total_biaya_dengan_pv), f"{payback_tahun} Tahun"]
        }).set_index('Parameter'))