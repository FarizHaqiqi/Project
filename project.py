import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --- 1. KONFIGURASI HALAMAN (WAJIB DI PALING ATAS) ---
st.set_page_config(
    page_title="Eco-Cost Analyzer", 
    layout="wide",
    page_icon="☀️",
    initial_sidebar_state="collapsed"
)

# --- 2. CUSTOM CSS: UI MODERN, ELEGAN, & ANTI-EROR DARK MODE ---
st.markdown("""
<style>
    /* Import Font Premium: Plus Jakarta Sans */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    /* Terapkan Font ke seluruh aplikasi */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Background Utama: Gradasi Halus & Bersih */
    .stApp {
        background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
    }

    /* --- HERO BANNER (Judul Mengambang) --- */
    .hero-container {
        position: relative;
        background-image: linear-gradient(rgba(15, 23, 42, 0.6), rgba(15, 23, 42, 0.5)), url('https://images.unsplash.com/photo-1592833159057-65a284572477?q=80&w=2070');
        background-size: cover;
        background-position: center;
        border-radius: 24px;
        padding: 60px 20px;
        text-align: center;
        margin-bottom: 40px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .hero-title {
        color: #ffffff !important;
        font-size: 3.5rem;
        font-weight: 800;
        margin-bottom: 12px;
        letter-spacing: -0.025em;
        text-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }

    .hero-subtitle {
        color: #e2e8f0 !important;
        font-size: 1.25rem;
        font-weight: 500;
        max-width: 800px;
        margin: 0 auto;
        line-height: 1.6;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }

    /* --- KARTU METRIC (Fix Dark Mode & Tampilan Premium) --- */
    div[data-testid="stMetric"] {
        background-color: #ffffff !important; /* Paksa putih */
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    div[data-testid="stMetric"]:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        border-color: #10b981; /* Aksen hijau saat hover */
    }

    /* Label Metric (Judul kecil) - Paksa warna abu gelap */
    div[data-testid="stMetricLabel"] p {
        color: #64748b !important;
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Value Metric (Angka Besar) - Paksa warna hitam */
    div[data-testid="stMetricValue"] div {
        color: #0f172a !important;
        font-size: 2rem;
        font-weight: 700;
    }
    
    /* Delta Metric (Angka kecil) */
    div[data-testid="stMetricDelta"] svg, div[data-testid="stMetricDelta"] > div {
        color: #059669 !important; /* Hijau Emerald */
    }

    /* --- INFO BOX WILAYAH --- */
    .info-box {
        background: linear-gradient(to right, #ffffff, #f0fdf4);
        border-radius: 16px;
        padding: 24px;
        border-left: 6px solid #10b981;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .info-item {
        display: flex;
        justify-content: space-between;
        margin-bottom: 8px;
        font-size: 1rem;
        color: #334155;
    }
    .info-value {
        font-weight: 700;
        color: #0f172a;
    }

    /* Container Input agar lebih rapi */
    .input-wrapper {
        background-color: white;
        padding: 30px;
        border-radius: 20px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        margin-bottom: 30px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. KONSTANTA & DATA ---
TARIF_PLN = 1400 
FILE_DATA = 'produksi_emisi_provinsi.csv' 
WP_CHOICES = [300, 350, 400, 450, 500, 550] 
MIN_PV_MODULES = 1 
MAX_PV_MODULES = 50 
TAHUN_ANALISIS = 15 
ASUMSI_INFLASI_LISTRIK = 0.05 
BIAYA_AWAL_PV_PER_Wp = 15000 

def format_rupiah(x):
    if x >= 1e9: return f"Rp {x/1e9:,.2f} M"
    if x >= 1e6: return f"Rp {x/1e6:,.1f} Jt"
    return f"Rp {x:,.0f}"

@st.cache_data
def load_data(file_path):
    try:
        # Mencoba membaca dengan separator koma
        df = pd.read_csv(file_path, delimiter=',')
        
        # Jika kolom cuma 1, kemungkinan separatornya titik koma
        if df.shape[1] < 2:
            df = pd.read_csv(file_path, delimiter=';')

        # Bersihkan kolom 'No' jika ada
        if df.columns[0].lower() in ['no', 'no.']:
            df = df.iloc[:, 1:].copy()
        
        # Pastikan kolom sesuai urutan (Provinsi, Radiasi, Emisi)
        # Kita ambil 3 kolom pertama saja untuk keamanan
        if df.shape[1] >= 3:
            df = df.iloc[:, :3]
            df.columns = ['Provinsi', 'Produksi_Harian_kWh', 'Faktor_Emisi_kg_per_kWh']
        else:
            st.error("Format Data CSV Salah. Pastikan ada kolom Provinsi, Radiasi, dan Emisi.")
            return pd.DataFrame()

        # Konversi angka (handling koma vs titik)
        for col in ['Produksi_Harian_kWh', 'Faktor_Emisi_kg_per_kWh']:
            if df[col].dtype == object:
                df[col] = df[col].astype(str).str.replace(',', '.', regex=True)
                df[col] = df[col].astype(str).str.replace(' kWh/kWp', '', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce')

        return df.dropna()

    except Exception as e:
        st.error(f"Gagal memuat data: {e}. Pastikan file {FILE_DATA} ada di folder project.")
        return pd.DataFrame()

data_solar = load_data(FILE_DATA)
if data_solar.empty: st.stop()


# --- 4. HERO BANNER (HTML/CSS) ---
st.markdown("""
    <div class="hero-container">
        <h1 class="hero-title">☀️ Solar Eco-Cost Analyzer</h1>
        <p class="hero-subtitle">
            Transformasi energi rumah Anda. Hitung potensi <b>penghematan biaya</b> dan <b>reduksi jejak karbon</b> 
            dengan simulasi PV surya yang presisi dan elegan.
        </p>
    </div>
""", unsafe_allow_html=True)


# --- 5. PANEL INPUT (DESAIN MODERN) ---
if 'tagihan_bulanan' not in st.session_state: st.session_state['tagihan_bulanan'] = 500000
if 'pv_module_watt' not in st.session_state: st.session_state['pv_module_watt'] = 550
if 'pv_module_count' not in st.session_state: st.session_state['pv_module_count'] = 4 

st.markdown("### ⚙️ Konfigurasi Sistem")

# Wrapper container agar terlihat seperti kartu putih besar
with st.container():
    st.markdown('<div class="input-wrapper">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1.2])

    with col1:
        provinsi_pilihan = st.selectbox("📍 Pilih Lokasi:", data_solar['Provinsi'].tolist())
        
        # Mengambil data wilayah
        data_lokasi = data_solar[data_solar['Provinsi'] == provinsi_pilihan].iloc[0]
        radiasi = data_lokasi['Produksi_Harian_kWh']
        emisi = data_lokasi['Faktor_Emisi_kg_per_kWh']

    with col2:
        tagihan_input = st.number_input("💸 Tagihan Listrik (Rp/Bln):", min_value=10000, value=st.session_state['tagihan_bulanan'], step=50000)
        tagihan_bulanan = tagihan_input 

    with col3:
        c3_1, c3_2 = st.columns(2)
        with c3_1:
            wp_pilihan = st.selectbox("⚡ Panel (Wp):", WP_CHOICES, index=WP_CHOICES.index(550))
        with c3_2:
            jumlah_modul = st.number_input("📦 Jumlah:", min_value=MIN_PV_MODULES, max_value=MAX_PV_MODULES, value=st.session_state['pv_module_count'])
        
        kapasitas_pv_wp = wp_pilihan * jumlah_modul
        kapasitas_pv_kwp = kapasitas_pv_wp / 1000.0
        
        # Info Kapasitas Kecil
        st.caption(f"Total Kapasitas: **{kapasitas_pv_kwp:.2f} kWp**")

    # Baris baru untuk info wilayah agar lebih rapi
    st.markdown("---")
    c_info1, c_info2 = st.columns([2,1])
    with c_info1:
        st.info(f"💡 **Tips:** Kapasitas {kapasitas_pv_kwp:.2f} kWp memerlukan luas atap sekitar **{jumlah_modul * 2} m²**.")
    with c_info2:
        st.markdown(f"""
        <div style="display:flex; gap:15px; justify-content:center; align-items:center; height:100%;">
            <div style="text-align:center;">
                <div style="font-size:0.8rem; color:#64748b;">Potensi Surya</div>
                <div style="font-weight:bold; color:#0f172a;">{radiasi} <span style="font-size:0.8rem">kWh/kWp</span></div>
            </div>
            <div style="width:1px; height:30px; background:#e2e8f0;"></div>
            <div style="text-align:center;">
                <div style="font-size:0.8rem; color:#64748b;">Faktor Emisi</div>
                <div style="font-weight:bold; color:#0f172a;">{emisi} <span style="font-size:0.8rem">kg/kWh</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# --- 6. LOGIKA KALKULASI (ROBUST) ---
konsumsi_kwh = tagihan_bulanan / TARIF_PLN
produksi_pv_harian = radiasi * kapasitas_pv_kwp 
produksi_pv_bulanan = produksi_pv_harian * 30

penghematan_rp = produksi_pv_bulanan * TARIF_PLN
emisi_dicegah_total = produksi_pv_bulanan * emisi 
skor_kemandirian = min((produksi_pv_bulanan / konsumsi_kwh) * 100, 100) 
tagihan_baru = max(tagihan_bulanan - penghematan_rp, 0)

biaya_instalasi_pv = kapasitas_pv_wp * BIAYA_AWAL_PV_PER_Wp

# Kalkulasi Payback Loop
biaya_kumulatif_tanpa_pv = []
biaya_kumulatif_dengan_pv = []
total_biaya_tanpa = 0
total_biaya_dengan = biaya_instalasi_pv 
payback_tahun = TAHUN_ANALISIS + 1 
tagihan_curr = tagihan_bulanan
tagihan_baru_curr = tagihan_baru

for t in range(1, TAHUN_ANALISIS + 1):
    inflasi = (1 + ASUMSI_INFLASI_LISTRIK)
    tagihan_curr *= inflasi
    tagihan_baru_curr *= inflasi
    
    total_biaya_tanpa += tagihan_curr * 12
    total_biaya_dengan += tagihan_baru_curr * 12
    
    biaya_kumulatif_tanpa_pv.append(total_biaya_tanpa)
    biaya_kumulatif_dengan_pv.append(total_biaya_dengan)
    
    if total_biaya_dengan <= total_biaya_tanpa and payback_tahun > TAHUN_ANALISIS:
        payback_tahun = t

df_proyeksi = pd.DataFrame({'Tahun': range(1, TAHUN_ANALISIS + 1), 'Tanpa PV': biaya_kumulatif_tanpa_pv, 'Dengan PV': biaya_kumulatif_dengan_pv})
emisi_total_ton = emisi_dicegah_total * 12 * TAHUN_ANALISIS / 1000
emisi_awal_total = konsumsi_kwh * emisi 
emisi_dicegah_grafik = min(emisi_dicegah_total, emisi_awal_total) 
emisi_tersisa_pln = emisi_awal_total - emisi_dicegah_grafik


# --- 7. DASHBOARD METRICS (CARD UI) ---
st.subheader(f"📊 Hasil Analisis: {provinsi_pilihan}")

m1, m2, m3, m4 = st.columns(4)

with m1: st.metric("Hemat Biaya/Bulan", format_rupiah(penghematan_rp), delta=f"Tagihan: {format_rupiah(tagihan_baru)}")
with m2: st.metric("ROI (Balik Modal)", f"{payback_tahun} Tahun" if payback_tahun <= 15 else "> 15 Tahun", help=f"Modal: {format_rupiah(biaya_instalasi_pv)}")
with m3: st.metric("Reduksi CO₂/Bulan", f"{emisi_dicegah_total:.1f} kg", help="Emisi karbon yang dicegah.")
with m4: st.metric("Kemandirian Energi", f"{skor_kemandirian:.1f}%", help="% Kebutuhan listrik dari matahari.")

st.write("")


# --- 8. VISUALISASI GRAFIK (PLOTLY MODERN) ---
tab1, tab2, tab3, tab4 = st.tabs(["📉 Grafik Biaya", "📈 Proyeksi ROI", "🌍 Lingkungan", "ℹ️ Rincian"])

# Konfigurasi Font Plotly agar konsisten
font_config = dict(family="Plus Jakarta Sans, sans-serif", size=14, color="#334155")

with tab1:
    st.subheader("Komparasi Tagihan Bulanan")
    df_bar = pd.DataFrame({
        'Kategori': ['Sebelum', 'Sesudah'], 
        'Nilai': [tagihan_bulanan, tagihan_baru],
        'Label': [format_rupiah(tagihan_bulanan), format_rupiah(tagihan_baru)]
    })
    
    fig_bar = px.bar(df_bar, x='Kategori', y='Nilai', text='Label', color='Kategori',
                     color_discrete_map={'Sebelum': '#94a3b8', 'Sesudah': '#10b981'})
    
    fig_bar.update_layout(showlegend=False, xaxis_title=None, yaxis_visible=False, plot_bgcolor='rgba(0,0,0,0)', font=font_config)
    fig_bar.update_traces(textfont_size=16, textposition='auto')
    st.plotly_chart(fig_bar, use_container_width=True)

with tab2:
    st.subheader("Analisis Pengembalian Modal (ROI)")
    df_long = df_proyeksi.melt('Tahun', var_name='Skenario', value_name='Total Biaya')
    
    fig_line = px.line(df_long, x='Tahun', y='Total Biaya', color='Skenario', markers=True,
                       color_discrete_map={'Tanpa PV': '#ef4444', 'Dengan PV': '#10b981'})
    
    fig_line.update_layout(yaxis_tickformat=",.0f", plot_bgcolor='rgba(0,0,0,0)', font=font_config, 
                           legend=dict(orientation="h", y=1.1, x=1, xanchor='right'))
    
    if payback_tahun <= 15:
        # Tandai titik BEP
        bep_val = df_proyeksi.loc[df_proyeksi['Tahun'] == payback_tahun, 'Dengan PV'].values[0]
        fig_line.add_scatter(x=[payback_tahun], y=[bep_val], mode='markers', marker=dict(size=14, color='#3b82f6', symbol='diamond'), name='Titik BEP', showlegend=False)
        
    st.plotly_chart(fig_line, use_container_width=True)

with tab3:
    c_pie, c_txt = st.columns([1.5, 1])
    with c_pie:
        # Donut Chart Modern
        fig_donut = go.Figure(data=[go.Pie(
            labels=['Dicegah (PV)', 'Sisa (PLN)'], 
            values=[emisi_dicegah_grafik, emisi_tersisa_pln], 
            hole=.65, 
            marker_colors=['#10b981', '#cbd5e1'],
            textinfo='percent',
            hoverinfo='label+value+percent'
        )])
        
        fig_donut.update_layout(
            annotations=[dict(text=f"{skor_kemandirian:.0f}%", x=0.5, y=0.5, font_size=28, showarrow=False, font_family="Plus Jakarta Sans", font_color="#047857")],
            showlegend=True,
            font=font_config,
            margin=dict(t=20, b=0, l=0, r=0)
        )
        st.plotly_chart(fig_donut, use_container_width=True)
    
    with c_txt:
        st.markdown(f"""
        ### Dampak Lingkungan
        Sistem ini mencegah **{emisi_dicegah_total:.1f} kg CO₂** terlepas ke atmosfer setiap bulan.
        
        **Setara dengan:**
        - 🌳 Menanam **{int(emisi_dicegah_total/20)} pohon**
        - 🚗 Menghapus **{int(emisi_dicegah_total*5)} km** perjalanan mobil
        """)

with tab4:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Spesifikasi Sistem**")
        st.table(pd.DataFrame({
            "Parameter": ["Kapasitas Total", "Jumlah Modul", "Jenis Panel", "Produksi/Bulan"],
            "Nilai": [f"{kapasitas_pv_kwp:.2f} kWp", f"{jumlah_modul} Unit", f"{wp_pilihan} Wp", f"{produksi_pv_bulanan:.2f} kWh"]
        }).set_index('Parameter'))
    with c2:
        st.markdown("**Analisis Finansial**")
        st.table(pd.DataFrame({
            "Parameter": ["Investasi Awal", "Tagihan Baru", "Hemat/Bulan", "ROI"],
            "Nilai": [format_rupiah(biaya_instalasi_pv), format_rupiah(tagihan_baru), format_rupiah(penghematan_rp), payback_display]
        }).set_index('Parameter'))