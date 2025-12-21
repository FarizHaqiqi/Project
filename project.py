import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go 

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Eco-Cost Analyzer", 
    layout="wide",
    page_icon="☀️"
)

# --- 2. CUSTOM CSS (MODERN UI, FONTS, & ELEGANCE) ---
st.markdown("""
<style>
    /* Import Font Modern: Plus Jakarta Sans */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Background Utama yang lebih bersih */
    .stApp {
        background-color: #f8fcf9; /* Hijau sangat muda/putih */
    }

    /* 1. HERO BANNER: Foto Rumah PV + Alam */
    .hero-banner {
        /* Gambar baru: Rumah dengan PV dan pemandangan alam */
        background-image: linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.7)), url('https://images.unsplash.com/photo-1592833159057-65a284572477?q=80&w=2070');
        height: 350px;
        background-position: center;
        background-size: cover;
        border-radius: 20px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.15);
        padding: 20px;
    }
    
    .hero-banner h1 {
        color: #ffffff !important;
        font-size: 3rem;
        font-weight: 800;
        letter-spacing: -1px;
        margin-bottom: 10px;
        text-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }
    
    .hero-banner p {
        color: #e0e0e0 !important;
        font-size: 1.2rem;
        font-weight: 400;
        max-width: 700px;
        line-height: 1.6;
    }

    /* 2. CARD METRICS YANG ELEGAN */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #edf2f7;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.02);
        transition: all 0.3s ease;
    }
    
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 15px rgba(0, 0, 0, 0.05);
        border-color: #48bb78; /* Aksen hijau saat hover */
    }

    /* Label Metric */
    div[data-testid="stMetricLabel"] {
        font-size: 0.9rem;
        color: #718096;
        font-weight: 600;
    }

    /* Value Metric */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        color: #2d3748;
        font-weight: 700;
    }

    /* 3. INFO BOX WILAYAH MODERN */
    .info-box-elegant {
        background: linear-gradient(135deg, #e6fffa 0%, #ffffff 100%);
        padding: 20px;
        border-radius: 12px;
        border-left: 5px solid #38b2ac;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        color: #2c7a7b;
    }

    /* 4. CONTAINER INPUT DENGAN FRAME */
    .input-container {
        background-color: white;
        padding: 25px;
        border-radius: 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.03);
        margin-bottom: 30px;
    }

</style>
""", unsafe_allow_html=True)


# --- 3. KONSTANTA PROYEK ---
TARIF_PLN = 1400 
FILE_DATA = 'produksi_emisi_provinsi.csv' 
# [REQUEST] Batas Wp sampai 550
WP_CHOICES = [300, 350, 400, 450, 500, 550] 
MIN_PV_MODULES = 1 
# [REQUEST] Batas Modul sampai 50
MAX_PV_MODULES = 50 
TAHUN_ANALISIS = 15 
ASUMSI_INFLASI_LISTRIK = 0.05 
BIAYA_AWAL_PV_PER_Wp = 15000 

# --- 4. FUNGSI UTILITY ---
def format_rupiah(x):
    """Format angka menjadi Rupiah untuk label grafik dan tampilan."""
    if x >= 1e9:
        return f"Rp {x/1e9:,.2f} M"
    if x >= 1e6:
        return f"Rp {x/1e6:,.1f} Jt"
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
        if df.empty:
            st.error("Data tidak valid. Pastikan kolom data Anda terisi angka.")
        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

# Panggil fungsi untuk memuat data
data_solar = load_data(FILE_DATA)
if data_solar.empty:
    st.stop()


# --- 5. HERO BANNER (Title Mengambang) ---
st.markdown("""
    <div class="hero-banner">
        <h1>☀️ Solar Eco-Cost Analyzer</h1>
        <p>Solusi cerdas untuk masa depan berkelanjutan. Hitung potensi <b>penghematan biaya</b> dan <b>reduksi karbon</b> dari atap rumah Anda.</p>
    </div>
""", unsafe_allow_html=True)


# --- 6. BAGIAN INPUT USER (DIBUAT LEBIH RAPI) ---

if 'tagihan_bulanan' not in st.session_state: st.session_state['tagihan_bulanan'] = 500000
if 'pv_module_watt' not in st.session_state: st.session_state['pv_module_watt'] = 550
if 'pv_module_count' not in st.session_state: st.session_state['pv_module_count'] = 4 

st.subheader("⚙️ Konfigurasi Sistem")

# Container putih agar input terlihat terpisah dan rapi
with st.container():
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    col_input1, col_input2, col_input3 = st.columns(3)

    with col_input1:
        provinsi_pilihan = st.selectbox(
            "📍 Pilih Lokasi (Provinsi):", 
            data_solar['Provinsi'].tolist(),
            key='provinsi_key' 
        )
        
        # [REQUEST] Tampilkan Info Wilayah
        data_lokasi = data_solar[data_solar['Provinsi'] == provinsi_pilihan].iloc[0]
        radiasi_harian = data_lokasi['Produksi_Harian_kWh']
        faktor_emisi_lokal = data_lokasi['Faktor_Emisi_kg_per_kWh']
        
        st.markdown(f"""
        <div class="info-box-elegant">
            <div style="font-weight: bold; margin-bottom: 5px;">Data Wilayah: {provinsi_pilihan}</div>
            <div style="display:flex; justify-content:space-between;">
                <span>☀️ PV Out:</span> <b>{radiasi_harian}</b> kWh/kWp
            </div>
            <div style="display:flex; justify-content:space-between;">
                <span>🏭 Emisi Grid:</span> <b>{faktor_emisi_lokal}</b> kg/kWh
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_input2:
        tagihan_input = st.number_input(
            "💸 Tagihan Listrik (Rp/Bulan):", 
            min_value=10000, 
            value=st.session_state['tagihan_bulanan'], 
            step=50000,
            key='tagihan_bulanan' 
        )
        tagihan_bulanan = tagihan_input 

    with col_input3:
        wp_pilihan = st.selectbox(
            "⚡ Kapasitas Panel (Wp):",
            WP_CHOICES, # [REQUEST] List cuma sampai 550
            index=WP_CHOICES.index(550),
            key='pv_module_watt'
        )
        
        jumlah_modul = st.number_input(
            "📦 Jumlah Modul (Max 50):",
            min_value=MIN_PV_MODULES,
            max_value=MAX_PV_MODULES, # [REQUEST] Max 50
            value=st.session_state['pv_module_count'],
            step=1,
            key='pv_module_count'
        )
        
        kapasitas_pv_wp = wp_pilihan * jumlah_modul
        kapasitas_pv_kwp = kapasitas_pv_wp / 1000.0
        
        st.success(f"**Total Kapasitas Terpasang:** {kapasitas_pv_kwp:.2f} kWp")
    
    st.markdown('</div>', unsafe_allow_html=True)


# --- BAGIAN 2: PROSES ALGORITMA (TIDAK DIUBAH) ---

# A. Lookup Data (Sudah diambil diatas)
# radiasi_harian & faktor_emisi_lokal

# B. Perhitungan Konsumsi & Produksi
konsumsi_kwh = tagihan_bulanan / TARIF_PLN
produksi_pv_harian = radiasi_harian * kapasitas_pv_kwp 
produksi_pv_bulanan = produksi_pv_harian * 30

# C. Hitung Output Kritis Bulanan
penghematan_rp = produksi_pv_bulanan * TARIF_PLN
emisi_dicegah_total = produksi_pv_bulanan * faktor_emisi_lokal 
skor_kemandirian = (produksi_pv_bulanan / konsumsi_kwh) * 100
skor_kemandirian = min(skor_kemandirian, 100) 
tagihan_baru = tagihan_bulanan - penghematan_rp
if tagihan_baru < 0: tagihan_baru = 0

# D. Hitung Output Kritis Jangka Panjang
biaya_instalasi_pv = kapasitas_pv_wp * BIAYA_AWAL_PV_PER_Wp
biaya_kumulatif_tanpa_pv = []
biaya_kumulatif_dengan_pv = []

tagihan_bulanan_saat_ini = tagihan_bulanan
tagihan_baru_saat_ini = tagihan_baru

total_biaya_tanpa_pv = 0
total_biaya_dengan_pv = biaya_instalasi_pv 

payback_tahun = TAHUN_ANALISIS + 1 

for tahun in range(1, TAHUN_ANALISIS + 1):
    tagihan_bulanan_saat_ini *= (1 + ASUMSI_INFLASI_LISTRIK)
    tagihan_baru_saat_ini *= (1 + ASUMSI_INFLASI_LISTRIK)

    total_biaya_tanpa_pv += tagihan_bulanan_saat_ini * 12
    total_biaya_dengan_pv += tagihan_baru_saat_ini * 12

    biaya_kumulatif_tanpa_pv.append(total_biaya_tanpa_pv)
    biaya_kumulatif_dengan_pv.append(total_biaya_dengan_pv)

    if total_biaya_dengan_pv <= total_biaya_tanpa_pv and payback_tahun > TAHUN_ANALISIS:
        payback_tahun = tahun
    
emisi_total_ton = emisi_dicegah_total * 12 * TAHUN_ANALISIS / 1000 
df_proyeksi = pd.DataFrame({
    'Tahun': range(1, TAHUN_ANALISIS + 1),
    'Tanpa PV': biaya_kumulatif_tanpa_pv,
    'Dengan PV': biaya_kumulatif_dengan_pv
})

# E. VARIABEL CHART
emisi_awal_total = konsumsi_kwh * faktor_emisi_lokal 
emisi_dicegah_grafik = min(emisi_dicegah_total, emisi_awal_total) 
emisi_tersisa_pln = emisi_awal_total - emisi_dicegah_grafik


# --- BAGIAN 3: DASHBOARD METRIC (STYLE BARU) ---

st.divider()
st.subheader(f"📊 Analisis Dampak: {provinsi_pilihan}")

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric(
        "💰 Hemat Biaya/Bulan", 
        f"{format_rupiah(int(penghematan_rp))}", 
        delta=f"Sisa Tagihan: {format_rupiah(int(tagihan_baru))}"
    )

with m2:
    payback_display = f"{payback_tahun} Tahun" if payback_tahun <= TAHUN_ANALISIS else f"> {TAHUN_ANALISIS} Tahun"
    st.metric(
        "⏳ ROI (Balik Modal)", 
        payback_display, 
        help=f"Total biaya sistem PV adalah {format_rupiah(biaya_instalasi_pv)}"
    )

with m3:
    st.metric(
        "🌱 Reduksi CO₂/Bulan", 
        f"{emisi_dicegah_total:.1f} kg", 
        help=f"Total 15 Tahun: {emisi_total_ton:.1f} ton CO₂"
    )

with m4:
    st.metric(
        "⚡ Kemandirian Energi", 
        f"{skor_kemandirian:.1f}%", 
        help="Persentase kebutuhan listrik yang dipenuhi sendiri."
    )

st.write("") 

# --- BAGIAN 4: VISUALISASI CHART (STYLE CLEAN & MODERN) ---

tab1, tab2, tab3, tab4 = st.tabs(["📉 Analisis Biaya", "📈 Proyeksi ROI", "🌍 Dampak Lingkungan", "ℹ️ Detail Teknis"])

# GRAFIK 1: Bar Chart (Plotly)
with tab1:
    st.subheader("Komparasi Tagihan Listrik Bulanan")
    
    data_biaya = pd.DataFrame({
        'Kategori': ['Sebelum Pasang PV', 'Sesudah Pasang PV'],
        'Rupiah': [tagihan_bulanan, tagihan_baru],
        'Teks': [format_rupiah(tagihan_bulanan), format_rupiah(tagihan_baru)]
    })
    
    fig_bar = px.bar(
        data_biaya, 
        x='Kategori', 
        y='Rupiah', 
        text='Teks', 
        color='Kategori',
        color_discrete_map={'Sebelum Pasang PV': '#718096', 'Sesudah Pasang PV': '#48bb78'}, # Abu & Hijau Modern
    )
    
    fig_bar.update_layout(
        yaxis_title=None, 
        xaxis_title=None, 
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Plus Jakarta Sans, sans-serif")
    )
    
    if penghematan_rp > 0 and tagihan_baru < tagihan_bulanan:
        y_pos_annotasi = (tagihan_bulanan + tagihan_baru) / 2
        fig_bar.add_annotation(
            x=0.5, y=y_pos_annotasi, 
            text=f"Hemat: {format_rupiah(penghematan_rp)}",
            showarrow=False,
            font=dict(size=14, color="#1a202c"),
            bgcolor="#ffffff",
            bordercolor="#48bb78",
            borderwidth=1,
            borderpad=4
        )
    
    st.plotly_chart(fig_bar, use_container_width=True) 
    st.progress(int(skor_kemandirian))

# GRAFIK 2: Line Chart (Plotly)
with tab2:
    st.subheader(f"Proyeksi Kumulatif {TAHUN_ANALISIS} Tahun")

    df_plot_longterm = df_proyeksi.melt('Tahun', var_name='Skenario', value_name='Total Biaya Kumulatif')

    fig_proj = px.line(
        df_plot_longterm,
        x='Tahun',
        y='Total Biaya Kumulatif',
        color='Skenario',
        color_discrete_map={'Tanpa PV': '#e53e3e', 'Dengan PV': '#38a169'}, # Merah & Hijau Modern
        markers=True
    )
    
    fig_proj.update_layout(
        yaxis=dict(tickformat=",.0f", tickprefix="Rp "),
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Plus Jakarta Sans, sans-serif"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    if payback_tahun <= TAHUN_ANALISIS:
        payback_cost = df_proyeksi[df_proyeksi['Tahun'] == payback_tahun]['Dengan PV'].iloc[0]
        fig_proj.add_scatter(
            x=[payback_tahun], y=[payback_cost], 
            mode='markers', marker=dict(size=12, color='#3182ce', symbol='diamond'),
            name='Titik Balik Modal', showlegend=False
        )
    
    st.plotly_chart(fig_proj, use_container_width=True)

# GRAFIK 3: Donut Chart (Plotly)
with tab3:
    st.subheader("Porsi Pengurangan Jejak Karbon")
    
    c_don, c_txt = st.columns([1.5, 1])
    
    with c_don:
        labels = ['Dicegah (PV)', 'Sisa (PLN)']
        values = [emisi_dicegah_grafik, emisi_tersisa_pln]
        colors = ['#48bb78', '#cbd5e0'] # Hijau Fresh & Abu Soft
        
        fig_donut = go.Figure(data=[go.Pie(
            labels=labels, 
            values=values, 
            hole=.65, 
            marker_colors=colors,
            hoverinfo="label+value+percent",
            textinfo='percent'
        )])
        
        fig_donut.update_layout(
            annotations=[dict(text=f"{skor_kemandirian:.0f}%", x=0.5, y=0.5, font_size=28, showarrow=False, font_family="Plus Jakarta Sans", font_color="#2f855a")],
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            margin=dict(t=20, b=0, l=0, r=0),
            font=dict(family="Plus Jakarta Sans, sans-serif")
        )
        st.plotly_chart(fig_donut, use_container_width=True)
    
    with c_txt:
        st.info(f"Sistem Anda mencegah **{emisi_dicegah_grafik:.1f} kg CO₂** per bulan.")
        st.markdown(f"""
        **Dampak Positif Setara:**
        \n🌳 Menanam **{int(emisi_dicegah_grafik/20)}** pohon/bulan.
        \n🚗 Menghapus **{int(emisi_dicegah_grafik*5)} km** perjalanan mobil bensin.
        """)

# TAB 4: Detail Teknis (Tabel)
with tab4:
    col_t1, col_t2 = st.columns(2)
    
    with col_t1:
        st.markdown("### ⚙️ Spesifikasi Sistem")
        st.write("---")
        data_sistem = pd.DataFrame({
            "Keterangan": ["Kapasitas PV Total", "Jumlah Modul", "Kapasitas 1 Modul", "Produksi Energi Bulanan"],
            "Nilai": [f"{kapasitas_pv_kwp:.2f} kWp", f"{jumlah_modul} unit", f"{wp_pilihan} Wp", f"{produksi_pv_bulanan:.2f} kWh"]
        }).set_index('Keterangan')
        st.table(data_sistem)
        
    with col_t2:
        st.markdown("### 💸 Analisis Finansial")
        st.write("---")
        data_finansial = pd.DataFrame({
            "Keterangan": ["Biaya Instalasi Awal", "Tagihan Baru", "Penghematan/Bulan", "Masa Balik Modal", f"Total Emisi Dicegah ({TAHUN_ANALISIS} Thn)"],
            "Nilai": [format_rupiah(biaya_instalasi_pv), format_rupiah(tagihan_baru), format_rupiah(penghematan_rp), payback_display, f"{emisi_total_ton:.1f} ton CO₂"]
        }).set_index('Keterangan')
        st.table(data_finansial)