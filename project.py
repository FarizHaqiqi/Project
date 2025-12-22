import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Eco-Cost Analyzer Pro",
    layout="wide",
    page_icon="☀️",
    initial_sidebar_state="collapsed"
)

# --- 2. CUSTOM CSS (MODERN UI & PROFESSIONAL LOOK) ---
st.markdown("""
<style>
    /* IMPORT FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Poppins:wght@500;700&display=swap');

    /* GLOBAL THEME */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #1e293b;
    }
    
    h1, h2, h3 {
        font-family: 'Poppins', sans-serif;
        font-weight: 700;
    }

    /* BACKGROUND GRADIENT */
    .stApp {
        background: linear-gradient(to bottom right, #f8fafc, #eef2f6);
    }

    /* 1. HERO BANNER RE-DESIGN */
    .hero-container {
        position: relative;
        background-image: linear-gradient(120deg, rgba(16, 185, 129, 0.9), rgba(15, 23, 42, 0.9)), 
                          url('https://images.unsplash.com/photo-1509391366360-2e959784a276?q=80&w=2072');
        background-size: cover;
        background-position: center;
        border-radius: 20px;
        padding: 60px 40px;
        color: white;
        margin-bottom: 30px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
    .hero-title {
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 15px;
        letter-spacing: -1px;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    .hero-subtitle {
        font-size: 1.2rem;
        opacity: 0.9;
        font-weight: 400;
        max-width: 700px;
        margin: 0 auto;
    }

    /* 2. CARD CONTAINER STYLE (Untuk Input & Info) */
    .card-style {
        background-color: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        border: 1px solid #e2e8f0;
        margin-bottom: 20px;
    }
    
    /* 3. METRIC BOX STYLING (OVERRIDE STREAMLIT DEFAULT) */
    div[data-testid="stMetric"] {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #f1f5f9;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        transition: transform 0.2s;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px rgba(0,0,0,0.05);
        border-color: #10b981;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.9rem;
        color: #64748b;
        font-weight: 600;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.6rem;
        color: #0f172a;
        font-weight: 700;
    }

    /* 4. INFO BOX WILAYAH */
    .info-box-modern {
        background-color: #eff6ff;
        border-left: 4px solid #3b82f6;
        padding: 15px;
        border-radius: 0 8px 8px 0;
        color: #1e3a8a;
        font-size: 0.9rem;
    }

    /* 5. TABS CUSTOMIZATION */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: white;
        border-radius: 8px;
        padding: 10px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
    }
    .stTabs [aria-selected="true"] {
        background-color: #10b981 !important;
        color: white !important;
        border: 1px solid #10b981 !important;
    }

    /* HIDE DEFAULT STREAMLIT MENU */
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


# --- 5. HEADER (NEW DESIGN) ---
st.markdown("""
    <div class="hero-container">
        <div class="hero-title">Solar Energy Analyzer</div>
        <div class="hero-subtitle">Simulasi cerdas penghematan biaya listrik dan pengurangan jejak karbon untuk hunian masa depan Anda.</div>
    </div>
""", unsafe_allow_html=True)


# --- 6. BAGIAN INPUT USER (CARD LAYOUT) ---

if 'tagihan_bulanan' not in st.session_state: st.session_state['tagihan_bulanan'] = 500000
if 'pv_module_watt' not in st.session_state: st.session_state['pv_module_watt'] = 550
if 'pv_module_count' not in st.session_state: st.session_state['pv_module_count'] = 4 

# Container styling
st.markdown('<div class="card-style">', unsafe_allow_html=True)
st.markdown("### 🛠️ Konfigurasi Sistem")
st.write("Sesuaikan parameter instalasi di bawah ini untuk melihat potensi penghematan.")

col_input1, col_input2, col_input3 = st.columns(3, gap="large")

with col_input1:
    st.markdown("##### 📍 Lokasi")
    provinsi_pilihan = st.selectbox(
        "Pilih Provinsi Domisili", 
        data_solar['Provinsi'].tolist(),
        key='provinsi_key' 
    )
    
    data_lokasi = data_solar[data_solar['Provinsi'] == provinsi_pilihan].iloc[0]
    radiasi_harian = data_lokasi['Produksi_Harian_kWh']
    faktor_emisi_lokal = data_lokasi['Faktor_Emisi_kg_per_kWh']
    
    st.markdown(f"""
    <div class="info-box-modern">
        <strong>Data Wilayah: {provinsi_pilihan}</strong><br>
        <span style="font-size:0.8em; color: #64748b;">Potensi PV: {radiasi_harian} kWh/kWp</span><br>
        <span style="font-size:0.8em; color: #64748b;">Emisi Grid: {faktor_emisi_lokal} kg/kWh</span>
    </div>
    """, unsafe_allow_html=True)

with col_input2:
    st.markdown("##### 💵 Tagihan Listrik")
    tagihan_input = st.number_input(
        "Rata-rata Tagihan per Bulan (Rp)", 
        min_value=10000, 
        value=st.session_state['tagihan_bulanan'], 
        step=50000,
        key='tagihan_bulanan',
        format="%d"
    )
    tagihan_bulanan = tagihan_input 

with col_input3:
    st.markdown("##### ☀️ Spesifikasi Panel")
    wp_pilihan = st.selectbox(
        "Kapasitas per Modul (Wp)",
        WP_CHOICES,
        index=WP_CHOICES.index(550),
        key='pv_module_watt'
    )
    
    jumlah_modul = st.number_input(
        "Jumlah Modul",
        min_value=MIN_PV_MODULES,
        max_value=MAX_PV_MODULES,
        value=st.session_state['pv_module_count'],
        step=1,
        key='pv_module_count'
    )
    
    kapasitas_pv_wp = wp_pilihan * jumlah_modul
    kapasitas_pv_kwp = kapasitas_pv_wp / 1000.0
    
    st.caption(f"Total Kapasitas Terpasang: **{kapasitas_pv_kwp:.2f} kWp**")

st.markdown('</div>', unsafe_allow_html=True) # End Card


# --- BAGIAN 2: PROSES ALGORITMA (ASLI) ---

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


# --- BAGIAN 3: OUTPUT DASHBOARD METRIC (RE-STYLED) ---

st.header(f"📊 Hasil Analisis Dampak")
st.write("")

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric(
        "💰 Hemat Bulanan", 
        f"{format_rupiah(int(penghematan_rp))}", 
        delta=f"Sisa Tagihan: {format_rupiah(int(tagihan_baru))}",
        delta_color="normal" # Hijau jika positif (default)
    )

with m2:
    payback_display = f"{payback_tahun} Tahun" if payback_tahun <= TAHUN_ANALISIS else f"> {TAHUN_ANALISIS} Tahun"
    st.metric(
        "⏳ Balik Modal (ROI)", 
        payback_display, 
        help=f"Investasi Awal: {format_rupiah(biaya_instalasi_pv)}"
    )

with m3:
    st.metric(
        "🌱 Reduksi CO₂/Bln", 
        f"{emisi_dicegah_total:.1f} kg", 
        delta=f"Total 15 Thn: {emisi_total_ton:.1f} Ton",
        delta_color="off"
    )

with m4:
    st.metric(
        "⚡ Kemandirian Energi", 
        f"{skor_kemandirian:.1f}%", 
        help="Persentase kebutuhan listrik yang disuplai mandiri."
    )

st.write("---") 

# --- BAGIAN 4: VISUALISASI GRAFIK (PROFESSIONAL THEME) ---

tab1, tab2, tab3, tab4 = st.tabs(["📉 Biaya & Hemat", "📈 Proyeksi ROI", "🌍 Emisi Lingkungan", "ℹ️ Rincian Teknis"])

# THEME COLORS
COLOR_PRIMARY = "#10b981" # Emerald Green
COLOR_SECONDARY = "#334155" # Slate
COLOR_ACCENT = "#3b82f6" # Blue

# GRAFIK 1: Analisis Biaya Bulanan
with tab1:
    col_chart, col_text = st.columns([2, 1])
    with col_chart:
        data_biaya = pd.DataFrame({
            'Kategori': ['Tagihan Lama', 'Tagihan Baru'],
            'Rupiah': [tagihan_bulanan, tagihan_baru],
            'Teks': [format_rupiah(tagihan_bulanan), format_rupiah(tagihan_baru)]
        })
        
        fig_bar = px.bar(
            data_biaya, 
            x='Kategori', 
            y='Rupiah', 
            text='Teks', 
            color='Kategori',
            color_discrete_map={'Tagihan Lama': COLOR_SECONDARY, 'Tagihan Baru': COLOR_PRIMARY},
        )
        
        fig_bar.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            yaxis_title="", 
            xaxis_title="", 
            showlegend=False,
            height=350,
            margin=dict(l=20, r=20, t=30, b=20)
        )
        fig_bar.update_traces(textposition='auto', width=0.5)
        
        if penghematan_rp > 0 and tagihan_baru < tagihan_bulanan:
            y_pos_annotasi = (tagihan_bulanan + tagihan_baru) / 2
            fig_bar.add_annotation(
                x=0.5, y=y_pos_annotasi, 
                text=f"SAVE {format_rupiah(penghematan_rp)}",
                showarrow=False,
                font=dict(size=14, color="#15803d", family="Inter"),
                bgcolor="#dcfce7",
                borderpad=6,
                bordercolor="#15803d",
                borderwidth=1,
                rx=5 # Rounded corner annotation
            )
        
        st.plotly_chart(fig_bar, use_container_width=True) 
    
    with col_text:
        st.markdown("#### Analisis Penghematan")
        st.info(f"""
        Dengan sistem **{kapasitas_pv_kwp:.2f} kWp**, Anda memangkas tagihan sebesar **{format_rupiah(penghematan_rp)}** setiap bulan.
        """)
        st.markdown(f"**Tingkat Kemandirian Energi:**")
        st.progress(int(skor_kemandirian))
        st.caption(f"{skor_kemandirian:.1f}% kebutuhan rumah dipenuhi oleh matahari.")

# GRAFIK 2: Proyeksi Jangka Panjang
with tab2:
    st.markdown("#### 🚀 Kapan modal Anda kembali?")
    
    df_plot_longterm = df_proyeksi.melt('Tahun', var_name='Skenario', value_name='Total Biaya Kumulatif')

    fig_proj = px.line(
        df_plot_longterm,
        x='Tahun',
        y='Total Biaya Kumulatif',
        color='Skenario',
        color_discrete_map={'Tanpa PV': '#ef4444', 'Dengan PV': COLOR_PRIMARY},
        markers=True
    )
    
    fig_proj.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(240,249,255,0.3)',
        yaxis=dict(tickformat=",.0f", tickprefix="Rp ", gridcolor='#e2e8f0'),
        xaxis=dict(gridcolor='#e2e8f0'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified"
    )

    if payback_tahun <= TAHUN_ANALISIS:
        payback_cost = df_proyeksi[df_proyeksi['Tahun'] == payback_tahun]['Dengan PV'].iloc[0]
        fig_proj.add_annotation(
            x=payback_tahun, y=payback_cost,
            text="Break Even Point (BEP)",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            ax=0, ay=-40,
            bgcolor="white",
            bordercolor=COLOR_ACCENT,
            font=dict(color=COLOR_ACCENT, size=12)
        )
    
    st.plotly_chart(fig_proj, use_container_width=True)
    st.caption(f"*Asumsi inflasi tarif listrik: {ASUMSI_INFLASI_LISTRIK*100}% per tahun.")

# GRAFIK 3: Analisis Emisi
with tab3:
    c_don, c_txt = st.columns([1.5, 1], gap="large")
    
    with c_don:
        labels = ['Emisi Dicegah (Solar)', 'Emisi Grid (PLN)']
        values = [emisi_dicegah_grafik, emisi_tersisa_pln]
        colors = [COLOR_PRIMARY, '#cbd5e1'] # Hijau vs Abu-abu
        
        fig_donut = go.Figure(data=[go.Pie(
            labels=labels, 
            values=values, 
            hole=.7, 
            marker_colors=colors,
            textinfo='none',
            hoverinfo="label+value+percent"
        )])
        
        fig_donut.update_layout(
            annotations=[dict(text=f"{skor_kemandirian:.0f}%<br>Clean", x=0.5, y=0.5, font_size=24, showarrow=False, font_family="Poppins", font_color=COLOR_PRIMARY)],
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
            margin=dict(t=0, b=0, l=0, r=0),
            height=300
        )
        st.plotly_chart(fig_donut, use_container_width=True)
    
    with c_txt:
        st.markdown("#### Dampak Nyata")
        st.success(f"Anda mencegah **{emisi_dicegah_total:.1f} kg CO₂** terlepas ke atmosfer setiap bulan.")
        
        st.markdown("##### Setara dengan:")
        st.markdown(f"""
        - 🌳 Menanam **{int(emisi_dicegah_total/20)} pohon**
        - 🚗 Menghapus **{int(emisi_dicegah_total*5)} km** perjalanan mobil bensin
        - 💡 Menghemat daya untuk **{int(emisi_dicegah_total*10)} lampu LED** seharian
        """)

# TAB 4: Detail Teknis (Table Styling)
with tab4:
    col_tech1, col_tech2 = st.columns(2, gap="large")
    
    # CSS Table Custom
    st.markdown("""
    <style>
    .styled-table {
        width: 100%;
        border-collapse: collapse;
        margin: 10px 0;
        font-size: 0.9em;
        font-family: 'Inter', sans-serif;
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.05);
    }
    .styled-table thead tr {
        background-color: #f1f5f9;
        color: #334155;
        text-align: left;
    }
    .styled-table th, .styled-table td {
        padding: 12px 15px;
        border-bottom: 1px solid #e2e8f0;
    }
    .styled-table tbody tr:last-of-type {
        border-bottom: 2px solid #10b981;
    }
    .highlight-val {
        font-weight: 700;
        color: #0f172a;
    }
    </style>
    """, unsafe_allow_html=True)

    def create_html_table(title, data_dict):
        rows = ""
        for k, v in data_dict.items():
            rows += f"<tr><td>{k}</td><td class='highlight-val'>{v}</td></tr>"
        
        return f"""
        <div style="background:white; padding:15px; border-radius:10px; border:1px solid #e2e8f0;">
            <h4 style="margin-bottom:10px; color:#334155;">{title}</h4>
            <table class="styled-table">
                {rows}
            </table>
        </div>
        """

    # BOX 1: Sistem & Energi
    with col_tech1:
        html_sistem = create_html_table("⚙️ Spesifikasi Sistem", {
            "Total Kapasitas PV": f"{kapasitas_pv_kwp:.2f} kWp",
            "Jumlah Modul": f"{jumlah_modul} unit",
            "Rating per Modul": f"{wp_pilihan} Wp",
            "Estimasi Produksi": f"{produksi_pv_bulanan:.2f} kWh/bulan"
        })
        st.markdown(html_sistem, unsafe_allow_html=True)
        
    # BOX 2: Finansial
    with col_tech2:
        html_fin = create_html_table("💸 Ringkasan Finansial", {
            "Investasi Awal": format_rupiah(biaya_instalasi_pv),
            "Tagihan Baru": format_rupiah(tagihan_baru),
            "Penghematan": format_rupiah(penghematan_rp) + " /bulan",
            "BEP (Balik Modal)": payback_display,
            "Total Emisi Dicegah": f"{emisi_total_ton:.1f} Ton CO₂"
        })
        st.markdown(html_fin, unsafe_allow_html=True)