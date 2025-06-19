import streamlit as st
import geopandas as gpd
import osmnx as ox
import networkx as nx
import zipfile
import os
from streamlit_folium import st_folium
import folium
from folium.plugins import BeautifyIcon
from ortools.constraint_solver import routing_enums_pb2, pywrapcp

st.set_page_config(page_title="Kadıköy Rota Planlayıcı", page_icon="🧭", layout="wide")
st.title("Kadıköy Turistik Rota Planlayıcı")

# ZIP içeriğini aç (ilk çalıştırmada çıkarılır)
if not os.path.exists("kadikoy_turistik.shp"):
    with zipfile.ZipFile("kadikoy_turistik.zip", 'r') as zip_ref:
        zip_ref.extractall(".")
if not os.path.exists("kadikoy_oteller.shp"):
    with zipfile.ZipFile("kadikoy_oteller.zip", 'r') as zip_ref:
        zip_ref.extractall(".")

# Veri yükleme
turistik_noktalar = gpd.read_file("kadikoy_turistik.shp").dropna(subset=["kategori"])
kategori_listesi = sorted(turistik_noktalar["kategori"].unique())
oteller = gpd.read_file("kadikoy_oteller.shp")
otel_isimleri = sorted(oteller["name"].dropna().unique())

# Session state başlat
for key, default in {
    "secili_poi": None,
    "rota_basildi": False,
    "rota_sonuc": None,
    "yer_etiketleri": [],
    "toplam_uzunluk_km": 0,
    "tsp_path": [],
    "G": None,
    "prev_network_type": None
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# Otel seçimi
secili_otel_adi = st.sidebar.selectbox("Başlangıç Noktası (Otel Seçimi)", otel_isimleri)
secili_otel = oteller[oteller["name"] == secili_otel_adi].iloc[0]

# Sidebar yer seçimi
st.sidebar.title("📍 Turistik Yerler")
for kategori in kategori_listesi:
    alt_kume = turistik_noktalar[turistik_noktalar["kategori"] == kategori]
    yerler = sorted(alt_kume["name"].unique())
    with st.sidebar.expander(kategori):
        for yer in yerler:
            if st.button(yer, key=f"buton_{yer}"):
                st.session_state.secili_poi = turistik_noktalar[turistik_noktalar["name"] == yer].iloc[0]

if st.sidebar.button("❌ Seçimi Temizle"):
    st.session_state.secili_poi = None

# Rota için yer seçimi
secili_yerler_listesi = st.multiselect(
    "Rota için yer seçimi yapınız:",
    sorted(turistik_noktalar["name"].unique()),
    key="rota_secimi"
)

# Ulaşım tipi ve butonlar
col1, col2, col3 = st.columns([1.2, 1, 1])
with col1:
    transport_mode = st.radio("Ulaşım türü", ["Yürüyüş", "Araç"], horizontal=True, label_visibility="collapsed")
    network_type = "walk" if transport_mode == "Yürüyüş" else "drive"
with col2:
    if st.button("📍 Rotayı Oluştur", use_container_width=True):
        st.session_state.rota_basildi = True
        st.session_state.rota_sonuc = None
with col3:
    if st.button("❌ Rotayı Temizle", use_container_width=True):
        for key in ["rota_basildi", "rota_sonuc", "yer_etiketleri", "toplam_uzunluk_km", "tsp_path", "G"]:
            st.session_state[key] = None

# Harita merkezi
harita_merkez = [40.9902, 29.0275]
zoom = 14
if st.session_state.secili_poi is not None:
    harita_merkez = [st.session_state.secili_poi.geometry.y, st.session_state.secili_poi.geometry.x]
    zoom = 17

m = folium.Map(location=harita_merkez, zoom_start=zoom)
if st.session_state.secili_poi is not None:
    folium.Marker(
        location=[st.session_state.secili_poi.geometry.y, st.session_state.secili_poi.geometry.x],
        popup=st.session_state.secili_poi["name"],
        icon=folium.Icon(color='blue', icon='info-sign')
    ).add_to(m)

# Rota hesapla (sadece bir kez)
if st.session_state.rota_basildi and secili_yerler_listesi and st.session_state.rota_sonuc is None:
    st.info(f"{transport_mode} ağı yükleniyor...")

    # network_type değişmişse G sıfırla
    if st.session_state.prev_network_type != network_type:
        st.session_state.G = None
        st.session_state.prev_network_type = network_type

    if st.session_state.G is None:
        st.session_state.G = ox.graph_from_place("Kadıköy, İstanbul, Türkiye", network_type=network_type)
    G = st.session_state.G

    secili_yerler = turistik_noktalar[turistik_noktalar["name"].isin(secili_yerler_listesi)].copy()
    start_node = ox.distance.nearest_nodes(G, secili_otel.geometry.x, secili_otel.geometry.y)
    nearest_nodes = ox.distance.nearest_nodes(G, X=secili_yerler.geometry.x, Y=secili_yerler.geometry.y)
    secili_yerler["nearest_node"] = nearest_nodes
    node_list = [start_node] + list(secili_yerler["nearest_node"])

    # Mesafe matrisi
    distance_matrix = []
    for i in node_list:
        row = []
        for j in node_list:
            try:
                length = nx.shortest_path_length(G, i, j, weight='length')
            except:
                length = 1e6
            row.append(int(length))
        distance_matrix.append(row)

    # OR-Tools ile TSP
    manager = pywrapcp.RoutingIndexManager(len(distance_matrix), 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return distance_matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

    solution = routing.SolveWithParameters(search_parameters)

    tsp_path = []
    if solution:
        index = routing.Start(0)
        while not routing.IsEnd(index):
            tsp_path.append(node_list[manager.IndexToNode(index)])
            index = solution.Value(routing.NextVar(index))
        tsp_path.append(node_list[manager.IndexToNode(index)])
    st.session_state.tsp_path = tsp_path

    # Rota çizimi
    route = []
    for i in range(len(tsp_path) - 1):
        try:
            route += nx.shortest_path(G, tsp_path[i], tsp_path[i + 1], weight='length')
        except:
            pass

    route_coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in route]
    st.session_state.rota_sonuc = route_coords

    yer_etiketleri = []
    for i, node in enumerate(tsp_path, start=1):
        row = secili_yerler[secili_yerler['nearest_node'] == node]
        if node == start_node:
            yer_etiketleri.append(f"Başlangıç noktası: {secili_otel_adi}")
        else:
            label = row.iloc[0]['name'] if not row.empty else f"Nokta {i}"
            yer_etiketleri.append(f"{i}: {label}")
    st.session_state.yer_etiketleri = yer_etiketleri

    # Mesafe hesapla
    toplam = 0
    for u, v in zip(route, route[1:]):
        edge_data = G.get_edge_data(u, v)
        if edge_data:
            try:
                d = min([e.get("length", 0) for e in edge_data.values()])
                toplam += d
            except:
                pass
    st.session_state.toplam_uzunluk_km = toplam / 1000

# Harita üzerine çizim
if st.session_state.rota_sonuc:
    m = folium.Map(location=st.session_state.rota_sonuc[0], zoom_start=15)
    folium.PolyLine(st.session_state.rota_sonuc, color="red", weight=5).add_to(m)

    G = st.session_state.G
    start_node = ox.distance.nearest_nodes(G, secili_otel.geometry.x, secili_otel.geometry.y)

    for i, node in enumerate(st.session_state.tsp_path, start=1):
        label = secili_otel_adi if node == start_node else f"{i}"
        icon_color = 'green' if node == start_node else '#007AFF'
        folium.Marker(
            location=[G.nodes[node]['y'], G.nodes[node]['x']],
            popup=label,
            icon=BeautifyIcon(
                number=None if node == start_node else str(i),
                icon_shape='marker',
                border_color='white',
                background_color=icon_color,
                text_color='white',
                border_width=2,
                radius=12,
                shadow=True
            )
        ).add_to(m)

    st.success(f"🛣️ Toplam Rota Uzunluğu: {st.session_state.toplam_uzunluk_km:.2f} km")
    with st.expander("📌 Ziyaret Noktası Sıralaması"):
        for etiket in st.session_state.yer_etiketleri:
            st.markdown(f"- {etiket}")

# Harita göster
st.markdown("## 🌍 Harita")
st_folium(m, width=950, height=600)
