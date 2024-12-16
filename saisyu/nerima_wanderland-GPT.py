import streamlit as st
import requests
import folium
import pandas as pd
from datetime import datetime  # 日付取得用
from streamlit_folium import st_folium
import time
import openai  # GPTコメント生成用ライブラリ

# OpenAI APIキー
openai.api_key =  st.secrets["openai"]["api_key"]  # ここに有効なAPIキーを記入

API_KEY = "AIzaSyAf_qxaXszMB2YmNUYrSlocBrf53b7Al6U"  # ここに有効なAPIキーを記入

# APIのURLと都市コード（東京固定）
city_code = "130010"  # 東京の都市コード
url = f"https://weather.tsukumijima.net/api/forecast/city/{city_code}"  # リクエストURL

# 天気情報を取得する関数
def get_weather(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        st.sidebar.error("天気情報を取得できませんでした。")
        return None

# コメント生成関数
def generate_gpt_comment(destinations):
    try:
        # プロンプトの作成
        messages = [
            {"role": "system", "content": "あなたは練馬の地元旅行ガイドのネリーです。"},
            {"role": "user", "content": (
                f"以下の情報を元に、場所1と場所2を組み合わせた冒険や旅行の提案を、100字以内でユニークでわくわくするコメントを作成してください。\n\n" +
                f"場所1: {destinations[0]['場所']}\n解説: {destinations[0]['解説']}\n\n" +
                f"場所2: {destinations[1]['場所']}\n解説: {destinations[1]['解説']}\n\n" +
                "まとめコメント:"
            )}
        ]

        # OpenAIのAPI呼び出し
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # または "gpt-4"
            messages=messages,
            max_tokens=150,
            temperature=0.7
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"コメント生成中にエラーが発生しました: {e}"

# CSVデータを読み込み
data = pd.read_csv("destinations.csv")

# 固定された出発地
fixed_origin = "豊島園駅"
st.session_state.setdefault("fixed_origin", fixed_origin)

# Streamlitアプリ
st.title("練馬ワンダーランド")

# サイドバーにウィジェットを配置
with st.sidebar:
    st.header("設定")
    
    # 気分の選択肢を表示
    if "今の気持ち" in data.columns:
        selected_mood = st.selectbox("今の気分を選んでください", data["今の気持ち"].unique())
    else:
        st.error("CSVファイルに「今の気持ち」カラムが見つかりません。")
    
    # 移動手段の選択肢を表示
    transport_mode = st.radio("移動手段を選んでください", ["徒歩", "自転車", "タクシー"])
    mode_map = {"徒歩": "walking", "自転車": "bicycling", "タクシー": "driving"}
    selected_mode = mode_map[transport_mode]
    
    # 食事の希望をチェック
    food_preference = st.checkbox("食事の希望がありますか？")
    if food_preference:
        st.write("食事希望: あり")
    else:
        st.write("食事希望: なし")
    
    # 確定ボタン
    search_button = st.button("ルートを検索")

    # サイドバーの下部に天気情報を表示
    st.markdown("---")  # 水平線で区切りを追加
    st.subheader("練馬の天気（3日分）")

    # 天気情報の取得と表示
    weather_json = get_weather(url)
    if weather_json:
        # 天気情報を3日分表示
        for i in range(3):  # 今日、明日、明後日
            forecast_date = weather_json['forecasts'][i]['dateLabel']
            weather = weather_json['forecasts'][i]['telop']
            icon_url = weather_json['forecasts'][i]['image']['url']
            st.image(icon_url, width=85)
            st.write(f"{forecast_date}: {weather}")
    else:
        st.write("天気情報を取得できませんでした。")

# 以下はスライドショーやルート検索の処理
if "search_completed" not in st.session_state:
    st.session_state["search_completed"] = False

if not search_button and not st.session_state["search_completed"]:
    image_placeholder = st.empty()
    images = ["pic/0.png", "pic/1.png", "pic/2.png"]
    for img in images:
        image_placeholder.image(img, use_container_width=True)
        time.sleep(1)
        if st.session_state["search_completed"]:
            break
else:
    st.session_state["search_completed"] = True

if search_button:
    st.session_state["search_completed"] = True

    if selected_mood:
        selected_data = data[data["今の気持ち"] == selected_mood].iloc[0]

        # 保存用データをセッションに記録
        st.session_state["selected_data"] = {
            "場所1": selected_data["場所1"],
            "画像1": selected_data["画像1"],
            "解説1": selected_data["解説1"],
            "場所2": selected_data["場所2"],
            "画像2": selected_data["画像2"],
            "解説2": selected_data["解説2"]
        }

        origin = fixed_origin
        destination1 = selected_data["住所1"]
        destination2 = selected_data["住所2"]

        directions_url1 = (
            f"https://maps.googleapis.com/maps/api/directions/json"
            f"?origin={origin}&destination={destination1}&mode={selected_mode}&key={API_KEY}"
        )
        directions_url2 = (
            f"https://maps.googleapis.com/maps/api/directions/json"
            f"?origin={destination1}&destination={destination2}&mode={selected_mode}&key={API_KEY}"
        )
        directions_url3 = (
            f"https://maps.googleapis.com/maps/api/directions/json"
            f"?origin={destination2}&destination={origin}&mode={selected_mode}&key={API_KEY}"
        )

        res1 = requests.get(directions_url1)
        res2 = requests.get(directions_url2)
        res3 = requests.get(directions_url3)

        if res1.status_code == 200 and res2.status_code == 200 and res3.status_code == 200:
            data1 = res1.json()
            data2 = res2.json()
            data3 = res3.json()

            if "routes" in data1 and len(data1["routes"]) > 0 and "routes" in data2 and len(data2["routes"]) > 0 and "routes" in data3 and len(data3["routes"]) > 0:
                route1 = data1["routes"][0]["overview_polyline"]["points"]
                route2 = data2["routes"][0]["overview_polyline"]["points"]
                route3 = data3["routes"][0]["overview_polyline"]["points"]

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
                        shift, result = 0, 0
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

                route_coords1 = decode_polyline(route1)
                route_coords2 = decode_polyline(route2)
                route_coords3 = decode_polyline(route3)

                # セッションにルートデータ保存
                st.session_state["route_coords1"] = route_coords1
                st.session_state["route_coords2"] = route_coords2
                st.session_state["route_coords3"] = route_coords3

                # 移動時間を取得
                duration1 = data1["routes"][0]["legs"][0]["duration"]["text"]
                duration2 = data2["routes"][0]["legs"][0]["duration"]["text"]
                duration3 = data3["routes"][0]["legs"][0]["duration"]["text"]

                st.session_state["route_table"] = pd.DataFrame({
                    "出発地": [fixed_origin, selected_data["場所1"], selected_data["場所2"]],
                    "目的地": [selected_data["場所1"], selected_data["場所2"], fixed_origin],
                    "所要時間": [duration1, duration2, duration3]
                })


                # 地図データを保存
                m = folium.Map(location=route_coords1[0], zoom_start=13)
                folium.PolyLine(route_coords1, color="blue", weight=5, opacity=0.7).add_to(m)
                folium.PolyLine(route_coords2, color="purple", weight=5, opacity=0.7).add_to(m)
                folium.PolyLine(route_coords3, color="red", weight=5, opacity=0.7).add_to(m)

                # Add markers
                folium.Marker(
                    location=route_coords1[0], popup="出発地: " + origin, icon=folium.Icon(color="green")
                ).add_to(m)
                folium.Marker(
                    location=route_coords1[-1], popup="目的地1: " + selected_data["場所1"], icon=folium.Icon(color="orange")
                ).add_to(m)
                folium.Marker(
                    location=route_coords2[-1], popup="目的地2: " + selected_data["場所2"], icon=folium.Icon(color="red")
                ).add_to(m)
                folium.Marker(
                    location=route_coords3[-1], popup="戻り: " + origin, icon=folium.Icon(color="blue")
                ).add_to(m)

                st.session_state["map"] = m
                
# メイン画面に状態を再表示
if "selected_data" in st.session_state:
    selected_data = st.session_state["selected_data"]

    st.write("### あなたの気分にあった冒険プランは、こちらです！")
    # 目的地情報リスト
    destinations = [
        {"場所": selected_data["場所1"], "解説": selected_data["解説1"]},
        {"場所": selected_data["場所2"], "解説": selected_data["解説2"]},
    ]
    
    # GPTコメント生成中にスピナーを表示
    with st.spinner("コメントを生成中です。しばらくお待ちください..."):
        adventure_comment = generate_gpt_comment(destinations)

    # 場所1の情報を表示
    st.write(f"#### {selected_data['場所1']}")
    col1, col2 = st.columns([1, 3])  # カラムを分割してレイアウト調整
    with col1:
        st.image(selected_data['画像1'], caption=selected_data['場所1'], width=150)
    with col2:
        st.write(selected_data['解説1'])
    
    # 場所2の情報を表示
    st.write(f"#### {selected_data['場所2']}")
    col1, col2 = st.columns([1, 3])
    with col1:
        st.image(selected_data['画像2'], caption=selected_data['場所2'], width=150)
    with col2:
        st.write(selected_data['解説2'])

    # GPTコメントを表示
    st.write("### ネリーからの提案")
    st.write(adventure_comment)

# 保存された表を表示
if "route_table" in st.session_state:
    st.write("### ルート情報")
    st.table(st.session_state["route_table"])

if "map" in st.session_state:
    st.write("### 地図")
    st_folium(st.session_state["map"], width=725)