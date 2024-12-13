import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

# Google Maps APIキー
API_KEY = "AIzaSyAf_qxaXszMB2YmNUYrSlocBrf53b7Al6U"  # ここに有効なAPIキーを記入

# セッション状態の初期化
if "route_data" not in st.session_state:
    st.session_state.route_data = None

# Streamlitアプリ
st.title("ルート検索アプリ")
st.write("出発地と目的地を入力してください")

# 出発地と目的地を入力
origin = st.text_input("出発地", "東京駅")
destination = st.text_input("目的地", "東京スカイツリー")

if st.button("ルートを検索"):
    # Directions APIでルートを取得
    directions_url = (
        f"https://maps.googleapis.com/maps/api/directions/json"
        f"?origin={origin}&destination={destination}&key={API_KEY}"
    )
    res = requests.get(directions_url)

    if res.status_code == 200:
        data = res.json()

        if "routes" in data and len(data["routes"]) > 0:
            st.session_state.route_data = data  # セッション状態に保存
        else:
            st.error("ルートが見つかりませんでした。")
            st.session_state.route_data = None
    else:
        st.error(f"APIリクエストに失敗しました。ステータスコード: {res.status_code}")
        st.session_state.route_data = None

# セッション状態にルートデータがあれば地図を表示
if st.session_state.route_data:
    route = st.session_state.route_data["routes"][0]["overview_polyline"]["points"]

    # Decode polyline
    def decode_polyline(polyline_str):
        index, lat, lng, coordinates = 0, 0, 0, []
        while index < len(polyline_str):
            b, shift, result = 0, 0, 0
            while True:
                b = ord(polyline_str[index]) - 63
                index += 1
                result |= (b & 0x1F) << shift
                shift += 5
                if b < 0x20:
                    break
            dlat = ~(result >> 1) if result & 1 else (result >> 1)
            lat += dlat
            shift, result = 0, 0  # Reset shift and result for lng
            while True:
                b = ord(polyline_str[index]) - 63
                index += 1
                result |= (b & 0x1F) << shift
                shift += 5
                if b < 0x20:
                    break
            dlng = ~(result >> 1) if result & 1 else (result >> 1)
            lng += dlng
            coordinates.append((lat / 1e5, lng / 1e5))
        return coordinates

    # ルートの座標を取得
    route_coords = decode_polyline(route)

    # 地図を作成
    m = folium.Map(location=route_coords[0], zoom_start=13)

    # ルートを地図に描画
    folium.PolyLine(route_coords, color="blue", weight=5).add_to(m)

    # 出発地にカスタムアイコンを追加
    folium.Marker(
        location=route_coords[0],
        popup="出発地: " + origin,
        icon=folium.Icon(color="green", icon="play", prefix="fa")
    ).add_to(m)

    # 目的地にカスタムアイコンを追加
    folium.Marker(
        location=route_coords[-1],
        popup="目的地: " + destination,
        icon=folium.Icon(color="red", icon="flag", prefix="fa")
    ).add_to(m)

    # 地図をStreamlitで表示
    st_folium(m, width=725)
