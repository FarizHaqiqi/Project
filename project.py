import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Eco-Cost Analyzer",
    layout="wide",
    page_icon="☀️",
    initial_sidebar_state="collapsed"
)

# --- 2. CUSTOM CSS: UI MODERN, GAMBAR & DARK MODE FIX ---
st.markdown("""
<style>
    /* Import Font Premium */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Background Utama */
    .stApp {
        background: linear-gradient(180deg, #f1f5f9 0%, #e2e8f0 100%);
    }

    /* --- HERO BANNER (JUDUL MENGAMBANG) --- */
    .hero-container {
        position: relative;
        /* Gambar Background: Rumah dengan Panel Surya */
        background-image: linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.5)), url('https://images.unsplash.com/photo-1592833159057-65a284572477?q=80&w=2070');
        background-size: cover;
        background-position: center;
        border-radius: 20px;
        padding: 60px 20px;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.15);
        color: white !important;
    }

    .hero-title {
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 10px;
        color: #ffffff !important;
        text-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }

    .hero-subtitle {
        font-size: 1.2rem;
        font-weight: 500;
        margin: 0 auto;
        max-width: 800px;
        color: #e2e8f0 !important;
        text-shadow: 0 2px 5px rgba(0,0,0,0.5);
    }

    /* --- KARTU METRIC (DARK MODE PROOF) --- */
    div[data-testid="stMetric"] {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    
    /* Paksa warna teks di dalam kartu metric menjadi hitam/abu */
    div[data-testid="stMetricLabel"] p { color: #64748b !important; font-weight: 600; }
    div[data-testid="stMetricValue"] div { color: #0f172a !important; font-weight: 700; }
    div[data-testid="stMetricDelta"] svg, div[data-testid="stMetricDelta"] > div { color: #10b981 !important; }

    /* --- INPUT CONTAINER --- */
    .input-card {
        background-color: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.03);
        margin-bottom: 25px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. KONSTANTA & DATA ---
TARIF_PLN = 1400
FILE_DATA = 'produksi_emisi_provinsi.csv'
WP_CHOICES = [300, 350, 400, 450, 500, 550] # Batas 550
MIN_PV_MODULES = 1
MAX_PV_MODULES = 50 # Batas 50 Modul
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
        df = pd.read_csv(file_path, delimiter=',')
        if df.shape[1] < 2:
            df = pd.read_csv(file_path, delimiter=';')
        if df.columns[0].lower() in ['no', 'no.']:
            df = df.iloc[:, 1:].copy()
        df.columns = ['Provinsi', 'Produksi_Harian_kWh', 'Faktor_Emisi_kg_per_kWh']
        for col in ['Produksi_Harian_kWh', 'Faktor_Emisi_kg_per_kWh']:
            if df[col].dtype == object:
                df[col] = df[col].astype(str).str.replace(',', '.', regex=True)
                df[col] = df[col].astype(str).str.replace(' kWh/kWp', '', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce')
        return df.dropna()
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")
        return pd.DataFrame()

data_solar = load_data(FILE_DATA)
if data_solar.empty: st.stop()


# --- 4. HERO BANNER ---
st.markdown("""
    <div class="hero-container">
        <h1 class="hero-title">☀️ Solar Eco-Cost Analyzer</h1>
        <p class="hero-subtitle">
            Optimalkan penghematan listrik dan reduksi emisi karbon rumah Anda dengan kalkulasi energi surya yang presisi.
        </p>
    </div>
""", unsafe_allow_html=True)


# --- 5. INPUT SECTION (DESIGN KARTU) ---
if 'tagihan_bulanan' not in st.session_state: st.session_state['tagihan_bulanan'] = 500000
if 'pv_module_watt' not in st.session_state: st.session_state['pv_module_watt'] = 550
if 'pv_module_count' not in st.session_state: st.session_state['pv_module_count'] = 4

st.subheader("⚙️ Konfigurasi Sistem")

with st.container():
    st.markdown('<div class="input-card">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1.2])

    with col1:
        provinsi_pilihan = st.selectbox("📍 Pilih Lokasi:", data_solar['Provinsi'].tolist())
        # Ambil data
        data_lokasi = data_solar[data_solar['Provinsi'] == provinsi_pilihan].iloc[0]
        radiasi = data_lokasi['Produksi_Harian_kWh']
        emisi = data_lokasi['Faktor_Emisi_kg_per_kWh']

    with col2:
        tagihan_input = st.number_input("💸 Tagihan Listrik (Rp/Bln):", min_value=10000, value=st.session_state['tagihan_bulanan'], step=50000)
        tagihan_bulanan = tagihan_input

    with col3:
        c3a, c3b = st.columns(2)
        with c3a:
            wp_pilihan = st.selectbox("⚡ Panel (Wp):", WP_CHOICES, index=WP_CHOICES.index(550))
        with c3b:
            jumlah_modul = st.number_input("📦 Jumlah:", min_value=MIN_PV_MODULES, max_value=MAX_PV_MODULES, value=st.session_state['pv_module_count'])
        
        kapasitas_pv_wp = wp_pilihan * jumlah_modul
        kapasitas_pv_kwp = kapasitas_pv_wp / 1000.0
        st.caption(f"Total Kapasitas: **{kapasitas_pv_kwp:.2f} kWp**")

    # Info Wilayah
    st.markdown("---")
    st.markdown(f"""
    <div style="display: flex; justify-content: space-around; color: #334155;">
        <div>☀️ Potensi Surya: <b>{radiasi}</b> kWh/kWp</div>
        <div>🏭 Faktor Emisi: <b>{emisi}</b> kg/kWh</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)


# --- 6. LOGIKA KALKULASI UTAMA ---
konsumsi_kwh = tagihan_bulanan / TARIF_PLN
produksi_pv_harian = radiasi * kapasitas_pv_kwp
produksi_pv_bulanan = produksi_pv_harian * 30

penghematan_rp = produksi_pv_bulanan * TARIF_PLN
emisi_dicegah_total = produksi_pv_bulanan * emisi
skor_kemandirian = min((produksi_pv_bulanan / konsumsi_kwh) * 100, 100)
tagihan_baru = max(tagihan_bulanan - penghematan_rp, 0)

biaya_instalasi_pv = kapasitas_pv_wp * BIAYA_AWAL_PV_PER_Wp

# Payback Loop
biaya_kumulatif_tanpa = []
biaya_kumulatif_dengan = []
total_tanpa = 0
total_dengan = biaya_instalasi_pv
payback_tahun = TAHUN_ANALISIS + 1
curr_tagihan = tagihan_bulanan
curr_tagihan_baru = tagihan_baru

for t in range(1, TAHUN_ANALISIS + 1):
    inflasi = (1 + ASUMSI_INFLASI_LISTRIK)
    curr_tagihan *= inflasi
    curr_tagihan_baru *= inflasi
    
    total_tanpa += curr_tagihan * 12
    total_dengan += curr_tagihan_baru * 12
    
    biaya_kumulatif_tanpa.append(total_tanpa)
    biaya_kumulatif_dengan.append(total_dengan)
    
    if total_dengan <= total_tanpa and payback_tahun > TAHUN_ANALISIS:
        payback_tahun = t

# [PENTING] DEFINISI VARIABEL DI SCOPE UTAMA AGAR TIDAK ERROR
payback_display = f"{payback_tahun} Tahun" if payback_tahun <= TAHUN_ANALISIS else f"> {TAHUN_ANALISIS} Tahun"

df_proyeksi = pd.DataFrame({'Tahun': range(1, TAHUN_ANALISIS + 1), 'Tanpa PV': biaya_kumulatif_tanpa, 'Dengan PV': biaya_kumulatif_dengan})
emisi_total_ton = emisi_dicegah_total * 12 * TAHUN_ANALISIS / 1000
emisi_sisa = max((konsumsi_kwh * emisi) - emisi_dicegah_total, 0)


# --- 7. METRICS ---
st.subheader(f"📊 Analisis Dampak: {provinsi_pilihan}")

m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("Hemat/Bulan", format_rupiah(penghematan_rp), delta=f"Tagihan Baru: {format_rupiah(tagihan_baru)}")
with m2: st.metric("ROI (Balik Modal)", payback_display, help=f"Modal: {format_rupiah(biaya_instalasi_pv)}")
with m3: st.metric("Reduksi CO₂/Bulan", f"{emisi_dicegah_total:.1f} kg", help="Jejak karbon yang hilang.")
with m4: st.metric("Kemandirian", f"{skor_kemandirian:.1f}%", help="% Energi dari Matahari.")

st.write("")


# --- 8. VISUALISASI ---
tab1, tab2, tab3, tab4 = st.tabs(["📉 Grafik Biaya", "📈 Proyeksi ROI", "🌍 Lingkungan", "ℹ️ Rincian"])

# Font Config
font_style = dict(family="Plus Jakarta Sans, sans-serif", size=14, color="#334155")

with tab1:
    st.subheader("Komparasi Tagihan")
    df_bar = pd.DataFrame({
        'Kategori': ['Sebelum', 'Sesudah'], 
        'Nilai': [tagihan_bulanan, tagihan_baru],
        'Label': [format_rupiah(tagihan_bulanan), format_rupiah(tagihan_baru)]
    })
    # Fix Angka Tidak Muncul: text='Label' dan textposition='auto'
    fig_bar = px.bar(df_bar, x='Kategori', y='Nilai', text='Label', color='Kategori',
                     color_discrete_map={'Sebelum': '#94a3b8', 'Sesudah': '#10b981'})
    fig_bar.update_layout(showlegend=False, yaxis_visible=False, xaxis_title=None, plot_bgcolor='rgba(0,0,0,0)', font=font_style)
    fig_bar.update_traces(textposition='auto', textfont_size=16)
    st.plotly_chart(fig_bar, use_container_width=True)

with tab2:
    st.subheader("Kapan Modal Kembali?")
    df_long = df_proyeksi.melt('Tahun', var_name='Skenario', value_name='Total')
    fig_line = px.line(df_long, x='Tahun', y='Total', color='Skenario', markers=True, 
                       color_discrete_map={'Tanpa PV': '#ef4444', 'Dengan PV': '#10b981'})
    fig_line.update_layout(yaxis_tickformat=",.0f", plot_bgcolor='rgba(0,0,0,0)', font=font_style, legend=dict(orientation="h", y=1.1))
    
    if payback_tahun <= 15:
        val_bep = df_proyeksi.loc[df_proyeksi['Tahun'] == payback_tahun, 'Dengan PV'].values[0]
        fig_line.add_scatter(x=[payback_tahun], y=[val_bep], mode='markers', marker=dict(size=12, color='#3b82f6'), name='Titik BEP', showlegend=False)
        
    st.plotly_chart(fig_line, use_container_width=True)

with tab3:
    c_pie, c_txt = st.columns([1.5, 1])
    with c_pie:
        fig_donut = go.Figure(data=[go.Pie(
            labels=['Dicegah (PV)', 'Sisa (PLN)'], 
            values=[emisi_dicegah_total, emisi_sisa], 
            hole=.65, 
            marker_colors=['#10b981', '#cbd5e1'],
            textinfo='percent'
        )])
        fig_donut.update_layout(
            annotations=[dict(text=f"{skor_kemandirian:.0f}%", x=0.5, y=0.5, font_size=26, showarrow=False, font_family="Plus Jakarta Sans", font_color="#047857")],
            showlegend=True, margin=dict(t=20, b=0, l=0, r=0), font=font_style
        )
        st.plotly_chart(fig_donut, use_container_width=True)
    
    with c_txt:
        st.info(f"Anda mencegah **{emisi_dicegah_total:.1f} kg CO₂** per bulan.")
        st.markdown(f"""
        **Setara dengan:**
        \n🌳 Menanam **{int(emisi_dicegah_total/20)} pohon**
        \n🚗 Menghapus **{int(emisi_dicegah_total*5)} km** perjalanan mobil
        """)

with tab4:
    col_t1, col_t2 = st.columns(2)
    
    with col_t1:
        st.markdown("### ⚙️ Spesifikasi")
        st.write("---")
        dict_sistem = {
            "Parameter": ["Kapasitas Total", "Jumlah Modul", "Jenis Panel", "Produksi Energi"],
            "Nilai": [f"{kapasitas_pv_kwp:.2f} kWp", f"{jumlah_modul} Unit", f"{wp_pilihan} Wp", f"{produksi_pv_bulanan:.2f} kWh/bln"]
        }
        df_sistem = pd.DataFrame(dict_sistem).set_index('Parameter')
        st.table(df_sistem)
        
    with col_t2:
        st.markdown("### 💸 Finansial")
        st.write("---")
        # Menggunakan payback_display yang sudah didefinisikan di line 210
        dict_finansial = {
            "Parameter": ["Investasi Awal", "Tagihan Baru", "Hemat/Bulan", "ROI", f"Total Emisi ({TAHUN_ANALISIS} Thn)"],
            "Nilai": [format_rupiah(biaya_instalasi_pv), format_rupiah(tagihan_baru), format_rupiah(penghematan_rp), payback_display, f"{emisi_total_ton:.1f} ton"]
        }
        df_finansial = pd.DataFrame(dict_finansial).set_index('Parameter')
        st.table(df_finansial)