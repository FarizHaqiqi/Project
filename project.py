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

# --- 2. CUSTOM CSS (UI MODERN, ELEGANT & PROFESSIONAL) ---
st.markdown("""
<style>
    /* IMPORT FONTS: Inter (Text) & Poppins (Headings) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Poppins:wght@500;600;700&display=swap');

    /* GLOBAL RESET & TEXT COLOR FIX */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #1e293b !important; /* Memaksa warna teks jadi gelap (Slate-800) */
    }
    
    /* BACKGROUND WEBSITE */
    .stApp {
        background-color: #f8fafc; /* Abu-abu sangat muda */
    }

    /* HEADERS (H1, H2, H3) */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Poppins', sans-serif;
        color: #0f172a !important; /* Memaksa Judul Hitam Pekat */
        font-weight: 700;
    }

    /* 1. HERO BANNER STYLE */
    .hero-banner {
        background-image: linear-gradient(135deg, rgba(15, 23, 42, 0.9), rgba(37, 99, 235, 0.8)), url('https://images.unsplash.com/photo-1509391366360-2e959784a276?q=80&w=2072');
        background-position: center;
        background-size: cover;
        border-radius: 16px;
        padding: 60px 40px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
    }
    
    /* JUDUL DALAM BANNER (Wajib Putih) */
    .hero-banner h1 {
        color: #ffffff !important; /* Override warna hitam global khusus banner */
        font-size: 2.2rem;
        text-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 15px;
        line-height: 1.3;
    }
    
    /* TEXT DALAM BANNER (Wajib Putih Abu) */
    .hero-banner p {
        color: #e2e8f0 !important; /* Override */
        font-size: 1.1rem;
        font-weight: 400;
        max-width: 900px;
        opacity: 0.95;
    }

    /* 2. CARD CONTAINER */
    .card-style {
        background-color: white;
        padding: 30px;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        border: 1px solid #e2e8f0;
        margin-bottom: 25px;
    }

    /* 3. METRIC BOX (Kotak Hasil) */
    div[data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #e2e8f0;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        transition: transform 0.2s;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        border-color: #3b82f6;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.9rem;
        color: #64748b !important; /* Abu-abu label */
        font-weight: 600;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        color: #0f172a !important; /* Angka Hitam */
        font-weight: 700;
    }
    div[data-testid="stMetricDelta"] {
        color: #1e293b !important; /* Warna Delta default */
    }

    /* 4. INFO BOX WILAYAH */
    .info-box {
        padding: 15px;
        border-radius: 8px;
        background-color: #eff6ff;
        border-left: 4px solid #3b82f6;
        color: #1e40af !important; /* Teks Biru Gelap */
        margin-top: 20px;
        font-size: 0.95rem;
    }
    .info-box b, .info-box strong {
        color: #1e3a8a !important;
    }

    /* 5. TABLE STYLING */
    .styled-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
    }
    .styled-table thead tr {
        background-color: #f8fafc;
        text-align: left;
    }
    .styled-table th {
        color: #334155 !important;
        padding: 12px 15px;
        border-bottom: 1px solid #e2e8f0;
    }
    .styled-table td {
        padding: 12px 15px;
        border-bottom: 1px solid #e2e8f0;
        color: #1e293b !important; /* Teks isi tabel */
    }
    .styled-table td strong {
        color: #0f172a !important;
    }

    /* 6. INPUT LABELS (Agar terlihat di dark mode) */
    .stSelectbox label, .stNumberInput label {
        color: #334155 !important;
        font-weight: 600;
    }
    
    /* 7. TABS */
    .stTabs [data-baseweb="tab"] {
        color: #64748b !important;
    }
    .stTabs [aria-selected="true"] {
        color: #3b82f6 !important; /* Tab aktif biru */
    }

    /* HIDE DEFAULT MENU */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# --- 3. KONSTANTA PROYEK ---
TARIF_PLN = 1400 
FILE_DATA = 'produksi_emisi_provinsi.csv' 
WP_CHOICES = [300, 350, 400, 450, 500, 550] 
MIN_PV_MODULES = 1 
MAX_PV_MODULES = 50 
TAHUN_ANALISIS = 15 
ASUMSI_INFLASI_LISTRIK = 0.05 
BIAYA_AWAL_PV_PER_Wp = 15000 

# --- 4. FUNGSI UTILITY ---
def format_rupiah(x):
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


# --- 5. HEADER (JUDUL ASLI) ---
st.markdown("""
    <div class="hero-banner">
        <h1>☀️ Analisis Penghematan Biaya dan Pengurangan Emisi Ketika Menggunakan PV Rumahan</h1>
        <p>Aplikasi ini membantu Anda menghitung potensi <b>penghematan biaya listrik (Rp)</b> dan <b>dampak lingkungan (emisi CO2)</b> dengan beralih ke energi surya mandiri.</p>
    </div>
""", unsafe_allow_html=True)


# --- 6. BAGIAN INPUT USER ---

if 'tagihan_bulanan' not in st.session_state: st.session_state['tagihan_bulanan'] = 500000
if 'pv_module_watt' not in st.session_state: st.session_state['pv_module_watt'] = 550
if 'pv_module_count' not in st.session_state: st.session_state['pv_module_count'] = 4 

st.markdown('<div class="card-style">', unsafe_allow_html=True)
st.subheader("⚙️ Data Input dan Instalasi")
st.write("---")

col_input1, col_input2, col_input3 = st.columns(3, gap="medium")

with col_input1:
    provinsi_pilihan = st.selectbox(
        "Pilih Lokasi (Provinsi):", 
        data_solar['Provinsi'].tolist(),
        key='provinsi_key' 
    )
    
    data_lokasi = data_solar[data_solar['Provinsi'] == provinsi_pilihan].iloc[0]
    radiasi_harian = data_lokasi['Produksi_Harian_kWh']
    faktor_emisi_lokal = data_lokasi['Faktor_Emisi_kg_per_kWh']
    
    st.markdown(f"""
    <div class="info-box">
        <b>Data Wilayah: {provinsi_pilihan}</b><br>
        ☀️ PV Out: {radiasi_harian} kWh/kWp<br>
        🏭 Emisi Grid: {faktor_emisi_lokal} kg/kWh
    </div>
    """, unsafe_allow_html=True)

with col_input2:
    tagihan_input = st.number_input(
        "Tagihan Listrik per Bulan (Rp):", 
        min_value=10000, 
        value=st.session_state['tagihan_bulanan'], 
        step=50000,
        key='tagihan_bulanan' 
    )
    tagihan_bulanan = tagihan_input 

with col_input3:
    wp_pilihan = st.selectbox(
        "Pilih Kapasitas 1 Modul PV (Watt Peak/Wp):",
        WP_CHOICES,
        index=WP_CHOICES.index(550),
        key='pv_module_watt'
    )
    
    jumlah_modul = st.number_input(
        "Jumlah Modul PV yang Dipasang:",
        min_value=MIN_PV_MODULES,
        max_value=MAX_PV_MODULES,
        value=st.session_state['pv_module_count'],
        step=1,
        key='pv_module_count'
    )
    
    kapasitas_pv_wp = wp_pilihan * jumlah_modul
    kapasitas_pv_kwp = kapasitas_pv_wp / 1000.0
    
    st.info(f"Kapasitas Total PV Anda: **{kapasitas_pv_kwp:.2f} kWp**")

st.markdown('</div>', unsafe_allow_html=True)


# --- BAGIAN 2: PROSES ALGORITMA ---

konsumsi_kwh = tagihan_bulanan / TARIF_PLN
produksi_pv_harian = radiasi_harian * kapasitas_pv_kwp 
produksi_pv_bulanan = produksi_pv_harian * 30

penghematan_rp = produksi_pv_bulanan * TARIF_PLN
emisi_dicegah_total = produksi_pv_bulanan * faktor_emisi_lokal 
skor_kemandirian = (produksi_pv_bulanan / konsumsi_kwh) * 100
skor_kemandirian = min(skor_kemandirian, 100) 
tagihan_baru = tagihan_bulanan - penghematan_rp
if tagihan_baru < 0: tagihan_baru = 0

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

emisi_awal_total = konsumsi_kwh * faktor_emisi_lokal 
emisi_dicegah_grafik = min(emisi_dicegah_total, emisi_awal_total) 
emisi_tersisa_pln = emisi_awal_total - emisi_dicegah_grafik


# --- BAGIAN 3: OUTPUT DASHBOARD METRIC ---

st.divider()
st.header(f"📊 Hasil Analisis Dampak untuk {provinsi_pilihan}")

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric(
        "💰 Hemat Biaya Bulanan", 
        f"{format_rupiah(int(penghematan_rp))}", 
        delta=f"Tagihan Akhir: {format_rupiah(int(tagihan_baru))}",
        delta_color="normal"
    )

with m2:
    payback_display = f"{payback_tahun} Tahun" if payback_tahun <= TAHUN_ANALISIS else f"> {TAHUN_ANALISIS} Tahun"
    st.metric(
        "⏳ Masa Balik Modal", 
        payback_display, 
        help=f"Total biaya sistem PV adalah {format_rupiah(biaya_instalasi_pv)}"
    )

with m3:
    st.metric(
        "🌱 Emisi CO₂ Dicegah (Bln)", 
        f"{emisi_dicegah_total:.1f} kg", 
        help=f"Total Emisi Dicegah selama {TAHUN_ANALISIS} tahun: {emisi_total_ton:.1f} ton CO₂"
    )

with m4:
    st.metric(
        "⚡ Skor Kemandirian Energi", 
        f"{skor_kemandirian:.1f}%", 
        help="Persentase kebutuhan listrik bulanan yang dipenuhi PV Anda."
    )

st.write("") 

# --- BAGIAN 4: VISUALISASI GRAFIK ---

tab1, tab2, tab3, tab4 = st.tabs(["📉 Analisis Biaya Bulanan", "📈 Proyeksi Jangka Panjang", "🌍 Analisis Lingkungan (Emisi)", "ℹ️ Detail Teknis"])

# KONFIGURASI WARNA AGAR KONSISTEN
COLOR_MAIN = "#10b981" # Emerald
COLOR_GRAY = "#94a3b8" # Slate

# GRAFIK 1
with tab1:
    col_gr, col_txt = st.columns([2, 1])
    with col_gr:
        st.subheader("Komparasi Tagihan Listrik Bulanan")
        data_biaya = pd.DataFrame({
            'Kategori': ['Tagihan Awal', 'Tagihan Akhir'],
            'Rupiah': [tagihan_bulanan, tagihan_baru],
            'Teks': [format_rupiah(tagihan_bulanan), format_rupiah(tagihan_baru)]
        })
        
        fig_bar = px.bar(
            data_biaya, 
            x='Kategori', 
            y='Rupiah', 
            text='Teks', 
            color='Kategori',
            color_discrete_map={'Tagihan Awal': COLOR_GRAY, 'Tagihan Akhir': COLOR_MAIN},
            title='Perbandingan Tagihan Listrik: Sebelum vs Sesudah PV'
        )
        
        fig_bar.update_layout(yaxis_title="", xaxis_title="", showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        
        if penghematan_rp > 0 and tagihan_baru < tagihan_bulanan:
            y_pos_annotasi = (tagihan_bulanan + tagihan_baru) / 2
            fig_bar.add_annotation(
                x=0.5, y=y_pos_annotasi, 
                text=f"Hemat: {format_rupiah(penghematan_rp)}",
                showarrow=False,
                font=dict(size=14, color="#15803d"),
                bgcolor="#dcfce7", borderpad=4
            )
        st.plotly_chart(fig_bar, use_container_width=True) 
    
    with col_txt:
        st.write("")
        st.markdown(f"#### Status Kemandirian")
        st.info(f"Sistem PV Anda menyuplai **{skor_kemandirian:.1f}%** dari total kebutuhan listrik.")
        st.progress(int(skor_kemandirian))

# GRAFIK 2
with tab2:
    st.subheader(f"Proyeksi Biaya Listrik Kumulatif Selama {TAHUN_ANALISIS} Tahun")
    df_plot_longterm = df_proyeksi.melt('Tahun', var_name='Skenario', value_name='Total Biaya Kumulatif')

    fig_proj = px.line(
        df_plot_longterm, x='Tahun', y='Total Biaya Kumulatif', color='Skenario',
        color_discrete_map={'Tanpa PV': '#ef4444', 'Dengan PV': COLOR_MAIN},
        title='Perbandingan Biaya Kumulatif Jangka Panjang', markers=True
    )
    
    fig_proj.update_layout(yaxis=dict(tickformat=",.0f", tickprefix="Rp "), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    if payback_tahun <= TAHUN_ANALISIS:
        payback_cost = df_proyeksi[df_proyeksi['Tahun'] == payback_tahun]['Dengan PV'].iloc[0]
        fig_proj.add_scatter(x=[payback_tahun], y=[payback_cost], mode='markers', marker=dict(size=10, color='#3b82f6'), name='Masa Balik Modal', showlegend=False)
    
    st.plotly_chart(fig_proj, use_container_width=True)
    st.markdown(f"* **Asumsi:** Kenaikan tarif listrik sebesar {ASUMSI_INFLASI_LISTRIK*100}% per tahun.")

# GRAFIK 3
with tab3:
    st.subheader("Porsi Pengurangan Jejak Karbon (CO₂)")
    c_don, c_txt = st.columns([1.5, 1])
    
    with c_don:
        labels = ['Dicegah (PV)', 'Sisa (PLN)']
        values = [emisi_dicegah_grafik, emisi_tersisa_pln]
        colors = [COLOR_MAIN, '#cbd5e1']
        
        fig_donut = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.7, marker_colors=colors, hoverinfo="label+value+percent", textinfo='percent')])
        fig_donut.update_layout(
            annotations=[dict(text=f"{skor_kemandirian:.0f}%", x=0.5, y=0.5, font_size=20, showarrow=False)],
            showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5), margin=dict(t=0, b=0, l=0, r=0)
        )
        st.plotly_chart(fig_donut, use_container_width=True)
    
    with c_txt:
        st.info(f"Dengan PV, Anda berhasil mengurangi emisi sebesar **{emisi_dicegah_grafik:.1f} kg CO₂** dari konsumsi rumah Anda.")
        st.markdown(f"**Setara dengan:**\n\n🌳 Menanam **{int(emisi_dicegah_total/20)} pohon**\n\n🚗 Menghapus **{int(emisi_dicegah_total*5)} km** perjalanan mobil")

# TAB 4: Detail Teknis (Custom HTML Table)
with tab4:
    col_tech1, col_tech2 = st.columns(2)
    
    def create_custom_table(title, data_dict):
        rows = ""
        for k, v in data_dict.items():
            rows += f"<tr><td>{k}</td><td><strong>{v}</strong></td></tr>"
        
        return f"""
        <div style="background:white; padding:15px; border-radius:10px; border:1px solid #e2e8f0; margin-bottom:15px;">
            <h4 style="margin-bottom:10px; font-family:'Poppins'; color:#334155;">{title}</h4>
            <table class="styled-table">{rows}</table>
        </div>
        """

    with col_tech1:
        table_html = create_custom_table("⚙️ Sistem & Energi", {
            "Kapasitas PV Total": f"{kapasitas_pv_kwp:.2f} kWp",
            "Jumlah Modul": f"{jumlah_modul} unit",
            "Kapasitas 1 Modul": f"{wp_pilihan} Wp",
            "Produksi Energi Bulanan": f"{produksi_pv_bulanan:.2f} kWh"
        })
        st.markdown(table_html, unsafe_allow_html=True)
        
    with col_tech2:
        table_html_2 = create_custom_table("💸 Finansial & Dampak", {
            "Biaya Instalasi Awal": format_rupiah(biaya_instalasi_pv),
            "Tagihan Bulanan Baru": format_rupiah(tagihan_baru),
            "Penghematan Bulanan": format_rupiah(penghematan_rp),
            "Masa Balik Modal": payback_display,
            f"Total Emisi Dicegah ({TAHUN_ANALISIS} Thn)": f"{emisi_total_ton:.1f} ton CO₂"
        })
        st.markdown(table_html_2, unsafe_allow_html=True)