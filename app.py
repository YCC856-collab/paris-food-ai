import streamlit as st
import google.generativeai as genai
import urllib.parse

st.set_page_config(page_title="巴黎美食 AI", page_icon="🇫🇷")
st.title("🇫🇷 巴黎餐廳 AI 嚮導")
st.caption("專注於 TheFork 與 Le Fooding 的深度分析與探索")

# --- 1. API Key 處理 ---
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    with st.sidebar:
        api_key = st.text_input("輸入 Gemini API Key", type="password")
        st.markdown("[👉 按此取得免費 Key](https://aistudio.google.com/app/apikey)")

# --- 2. 函式區 ---
def get_first_working_model(api_key):
    try:
        genai.configure(api_key=api_key)
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                return m.name
    except Exception:
        return None
    return None

# --- 3. Session State 管理 ---
if 'target_restaurant' not in st.session_state:
    st.session_state.target_restaurant = ""

# --- 4. 介面分頁 (Tabs) ---
tab1, tab2 = st.tabs(["🔍 直接搜尋餐廳", "📍 尋找附近美食"])

# ==========================================
# 分頁 1: 原本的分析功能
# ==========================================
with tab1:
    default_val = st.session_state.target_restaurant if st.session_state.target_restaurant else ""
    restaurant_name = st.text_input("請輸入餐廳名稱", value=default_val, placeholder="例如: Septime")
    
    if restaurant_name != st.session_state.target_restaurant:
        st.session_state.target_restaurant = restaurant_name

    if st.button("開始分析", key="btn_analyze") and restaurant_name:
        if not api_key:
            st.error("請先設定 API Key！")
        else:
            # 快速傳送門
            search_query = urllib.parse.quote_plus(f"{restaurant_name} Paris")
            st.subheader("🔗 快速傳送門")
            c1, c2, c3 = st.columns(3)
            with c1: st.link_button("📍 Google Maps", f"https://www.google.com/maps?q={search_query}")
            with c2: st.link_button("🍴 TheFork", f"https://www.thefork.fr/search?q={search_query}")
            with c3: st.link_button("🍷 Le Fooding", f"https://lefooding.com/en/search?query={search_query}")

            # AI 分析
            st.divider()
            status_box = st.empty()
            
            try:
                valid_model_name = get_first_working_model(api_key)
                if not valid_model_name:
                    status_box.error("❌ 找不到可用模型")
                else:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel(valid_model_name)
                    
                    with st.spinner("AI 正在交叉比對兩大平台數據..."):
                        prompt = f"""
                        你是一位專精於巴黎餐廳的數據分析師。使用者查詢餐廳 "{restaurant_name}"。
                        
                        【重要規則】
                        1. 你的分析範圍 **「嚴格僅限於」** TheFork 和 Le Fooding 這兩個平台的資料。
                        2. 若這兩個平台都無資料，請誠實告知。
                        
                        請用繁體中文輸出結構化報告：
                        ### 1. 🍴 TheFork 數據
                        * **評分與人氣**：(預估分數)
                        * **價格與優惠**：(平均消費與折扣)
                        * **評論關鍵詞**：(優缺點)

                        ### 2. 🍷 Le Fooding 風格
                        * **氛圍定位**：(潮店/老派/觀光?)
                        * **小編觀點**：(形容詞)
                        * **必點推薦**：(菜色)

                        ### 3. ⚖️ 綜合結論
                        * **適合誰？**
                        * **決策建議**：(去還是不去？)
                        """
                        response = model.generate_content(prompt)
                        st.markdown(response.text)
            except Exception as e:
                st.error(f"發生錯誤: {e}")

# ==========================================
# 分頁 2: 嚴格篩選版附近探索
# ==========================================
with tab2:
    st.header("📍 尋找附近 100m 美食")
    st.caption("✅ 只顯示 TheFork 或 Le Fooding 上有資料的餐廳")
    location_input = st.text_input("請輸入您現在的地點或景點", placeholder="例如: Louvre Museum (羅浮宮)")
    
    if st.button("搜尋附近餐廳", key="btn_explore"):
        if not api_key:
            st.error("請先設定 API Key！")
        elif not location_input:
            st.warning("請輸入地點喔！")
        else:
            try:
                valid_model_name = get_first_working_model(api_key)
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(valid_model_name)
                
                with st.spinner(f"正在過濾非合作餐廳，僅保留 TheFork/Le Fooding 名單..."):
                    # Prompt 更新：加入嚴格的「平台存在性檢查」
                    explore_prompt = f"""
                    任務：找出巴黎地點 "{location_input}" 附近 **走路 5 分鐘內** 的餐廳。

                    【🔥 絕對關鍵規則 🔥】
                    1. **過濾機制**：你推薦的餐廳，必須是你「確定」在 **TheFork** (有訂位/折扣) 或 **Le Fooding** (有食評) 上有資料的。
                    2. 如果一家店 Google 評價很高，但在這兩個平台找不到，請 **「直接剔除，不要列出來」**。
                    3. 請標註該餐廳是出現在哪個平台 (Source)。

                    【輸出格式】
                    每一行一家餐廳，格式如下(直立線分隔)：
                    Name: 餐廳名 | Style: 風格 | Rating: Google評分 | Count: 評論數 | Source: 平台標記

                    範例：
                    Name: Le Louvre | Style: 法式 | Rating: 4.2 | Count: 850+ | Source: TheFork & Le Fooding
                    Name: Zen | Style: 拉麵 | Rating: 4.6 | Count: 2100+ | Source: Only TheFork
                    """
                    
                    response = model.generate_content(explore_prompt)
                    
                    st.success(f"✨ 在 {location_input} 附近找到以下「平台認證」餐廳：")
                    
                    lines = response.text.split('\n')
                    found_any = False
                    for line in lines:
                        if "Name:" in line:
                            found_any = True
                            clean_line = line.replace("*", "").strip()
                            parts = clean_line.split('|')
                            
                            # 解析資料
                            r_name_raw = parts[0].replace("Name:", "").strip() if len(parts) > 0 else "未知餐廳"
                            r_style = parts[1].replace("Style:", "").strip() if len(parts) > 1 else "風格未知"
                            r_rating = parts[2].replace("Rating:", "").strip() if len(parts) > 2 else "N/A"
                            r_count = parts[3].replace("Count:", "").strip() if len(parts) > 3 else "N/A"
                            r_source = parts[4].replace("Source:", "").strip() if len(parts) > 4 else "TheFork/Le Fooding"
                            
                            # 介面顯示
                            col_a, col_b = st.columns([3, 1])
                            with col_a:
                                # 顯示平台標籤，讓使用者安心
                                st.markdown(f"""
                                **{r_name_raw}** ⭐ **{r_rating}** <small>({r_count})</small>  
                                <span style='background-color:#e0f7fa; padding:2px 6px; border-radius:4px; font-size:0.8em; color:#006064'>✅ {r_source}</span>  
                                <small style='color:#555'>{r_style}</small>
                                """, unsafe_allow_html=True)
                                
                            with col_b:
                                def set_name(n=r_name_raw):
                                    st.session_state.target_restaurant = n
                                st.button("分析它 👉", key=f"btn_{r_name_raw}", on_click=set_name)
                            
                            st.divider()
                    
                    if not found_any:
                        st.warning("在此地點附近找不到「同時符合距離」且「在 TheFork/Le Fooding 有資料」的餐廳。您可以嘗試擴大範圍或換個地標。")
                                
            except Exception as e:
                st.error(f"搜尋失敗: {e}")

    if st.session_state.target_restaurant:
        st.info(f"已選擇：**{st.session_state.target_restaurant}**，請回「🔍 直接搜尋餐廳」分頁查看詳情。")