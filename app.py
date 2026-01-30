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

# --- 3. Session State 管理 (這是新功能的核心) ---
# 用來記住使用者是不是從「推薦清單」點過來的
if 'target_restaurant' not in st.session_state:
    st.session_state.target_restaurant = ""

# --- 4. 介面分頁 (Tabs) ---
tab1, tab2 = st.tabs(["🔍 直接搜尋餐廳", "📍 尋找附近美食"])

# ==========================================
# 分頁 1: 原本的分析功能 (主要邏輯不變)
# ==========================================
with tab1:
    # 如果 Session 有紀錄 (從隔壁頁點過來的)，就自動填入
    default_val = st.session_state.target_restaurant if st.session_state.target_restaurant else ""
    
    restaurant_name = st.text_input("請輸入餐廳名稱", value=default_val, placeholder="例如: Septime")
    
    # 清除 session 避免卡住
    if restaurant_name != st.session_state.target_restaurant:
        st.session_state.target_restaurant = restaurant_name

    if st.button("開始分析", key="btn_analyze") and restaurant_name:
        if not api_key:
            st.error("請先設定 API Key！")
        else:
            # --- 快速傳送門 ---
            search_query = urllib.parse.quote_plus(f"{restaurant_name} Paris")
            st.subheader("🔗 快速傳送門")
            c1, c2, c3 = st.columns(3)
            with c1: st.link_button("📍 Google Maps", f"https://www.google.com/maps?q={search_query}")
            with c2: st.link_button("🍴 TheFork", f"https://www.thefork.fr/search?q={search_query}")
            with c3: st.link_button("🍷 Le Fooding", f"https://lefooding.com/en/search?query={search_query}")

            # --- AI 分析 ---
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
# 分頁 2: 新增的「附近探索」功能
# ==========================================
with tab2:
    st.header("📍 尋找附近 100m 美食")
    location_input = st.text_input("請輸入您現在的地點或景點", placeholder="例如: Louvre Museum (羅浮宮) 或 12 Rue de Rivoli")
    
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
                
                with st.spinner(f"正在搜尋 {location_input} 周圍 100-300m 的 TheFork/Le Fooding 餐廳..."):
                    # 這裡的 Prompt 是關鍵：要求 AI 當作地圖導航
                    explore_prompt = f"""
                    使用者目前在巴黎的地點："{location_input}"。
                    請推薦 3 到 5 家位於該地點 **「走路 3 分鐘內 (約 100-300公尺)」** 的餐廳。

                    【篩選條件】
                    1. 必須是 **TheFork** 或 **Le Fooding** 上找得到的餐廳 (不要推薦只有 Google Maps 有的速食店)。
                    2. 請優先推薦評價較好的店。
                    3. 請直接給我餐廳名稱列表，不要廢話。格式如下：
                    Name: 餐廳A | Style: 法式餐酒館
                    Name: 餐廳B | Style: 義大利麵
                    """
                    
                    response = model.generate_content(explore_prompt)
                    
                    st.success("✨ 找到以下餐廳 (點擊名稱即可分析)：")
                    
                    # 簡單的解析 AI 回傳的文字並做成按鈕
                    lines = response.text.split('\n')
                    for line in lines:
                        if "Name:" in line:
                            # 清理文字，取出餐廳名
                            clean_line = line.replace("*", "").strip()
                            parts = clean_line.split('|')
                            if len(parts) >= 1:
                                r_name_raw = parts[0].replace("Name:", "").strip()
                                r_style = parts[1].strip() if len(parts) > 1 else ""
                                
                                # 製作成按鈕，按下去會自動跳轉
                                col_a, col_b = st.columns([3, 1])
                                with col_a:
                                    st.markdown(f"**{r_name_raw}** \n<small style='color:gray'>{r_style}</small>", unsafe_allow_html=True)
                                with col_b:
                                    # 這是 Streamlit 的一個小技巧：用 callback 傳值
                                    def set_name(n=r_name_raw):
                                        st.session_state.target_restaurant = n
                                    
                                    st.button("分析它 👉", key=f"btn_{r_name_raw}", on_click=set_name)
                                st.divider()
                                
            except Exception as e:
                st.error(f"搜尋失敗: {e}")

    # 如果有選中餐廳，提示使用者回到第一頁 (或甚至可以自動顯示在下方，但這邊先引導回首頁比較不亂)
    if st.session_state.target_restaurant:
        st.info(f"已選擇餐廳：**{st.session_state.target_restaurant}**，請切換回「🔍 直接搜尋餐廳」分頁查看詳情 (或是直接按上面的分析它按鈕通常會自動重新整理)。")