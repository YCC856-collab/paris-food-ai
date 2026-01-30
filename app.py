import streamlit as st
import google.generativeai as genai
import urllib.parse
import time # 新增時間模組，用來處理重試

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

# --- 2. 函式區 (重大升級：優先抓 Flash 模型) ---
def get_best_model(api_key):
    """
    優先選擇 'gemini-1.5-flash'，因為它的免費額度最高 (15 RPM)。
    避開 'pro'，因為它每分鐘只能跑 2 次，很容易報錯。
    """
    try:
        genai.configure(api_key=api_key)
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 策略 1: 優先找 1.5 Flash (最穩)
        for m in models:
            if "gemini-1.5-flash" in m and "exp" not in m: # 避開實驗版，找正式版
                return m
        
        # 策略 2: 找不到正式版，找 Flash 任意版
        for m in models:
            if "flash" in m:
                return m
                
        # 策略 3: 真的沒有，才用其他的 (例如 Pro)
        return models[0] if models else None
    except Exception:
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
                valid_model_name = get_best_model(api_key) # 改用新的選擇器
                if not valid_model_name:
                    status_box.error("❌ 找不到可用模型")
                else:
                    # status_box.info(f"使用模型: {valid_model_name}") # 除錯用，確認是不是用到 Flash
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel(valid_model_name)
                    
                    with st.spinner("AI 正在交叉比對兩大平台數據..."):
                        prompt = f"""
                        你是一位專精於巴黎餐廳的數據分析師。使用者查詢餐廳 "{restaurant_name}"。
                        
                        【重要規則】
                        1. 你的分析範圍 **「嚴格僅限於」** TheFork 和 Le Fooding 這兩個平台的資料。
                        2. 若這兩個平台都無資料，請誠實告知「無資料」，不要硬編。
                        
                        請用繁體中文輸出結構化報告：
                        ### 1. 🍴 TheFork 數據
                        * **評分與人氣**：(若無資料請寫 N/A)
                        * **價格與優惠**：(若無資料請寫 N/A)
                        * **評論關鍵詞**：(若無資料請寫 N/A)

                        ### 2. 🍷 Le Fooding 風格
                        * **氛圍定位**：(若無資料請寫 N/A)
                        * **小編觀點**：(若無資料請寫 N/A)
                        * **必點推薦**：(若無資料請寫 N/A)

                        ### 3. ⚖️ 綜合結論
                        * **適合誰？**
                        * **決策建議**：(去還是不去？)
                        """
                        response = model.generate_content(prompt)
                        st.markdown(response.text)
            except Exception as e:
                if "429" in str(e):
                    st.error("🐢 抱歉，免費版 AI 累了 (429 Error)。請等待 30 秒後再試一次！")
                else:
                    st.error(f"發生錯誤: {e}")

# ==========================================
# 分頁 2: 嚴格篩選版附近探索
# ==========================================
with tab2:
    st.header("📍 尋找附近 100m 美食")
    st.caption("✅ 嚴格模式：必須能提供具體平台短評才會顯示")
    location_input = st.text_input("請輸入您現在的地點或景點", placeholder="例如: Louvre Museum (羅浮宮)")
    
    if st.button("搜尋附近餐廳", key="btn_explore"):
        if not api_key:
            st.error("請先設定 API Key！")
        elif not location_input:
            st.warning("請輸入地點喔！")
        else:
            try:
                valid_model_name = get_best_model(api_key) # 改用新的選擇器
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(valid_model_name)
                
                with st.spinner(f"正在 {location_input} 附近嚴格篩選 TheFork/Le Fooding 餐廳..."):
                    # Prompt 更新：要求「舉證」
                    explore_prompt = f"""
                    任務：找出巴黎地點 "{location_input}" 附近 **走路 5 分鐘內** 的餐廳。
                    
                    【🔥 嚴格篩選規則 🔥】
                    1. 你推薦的餐廳，必須 **確實在** TheFork 或 Le Fooding 上有資料。
                    2. 為了證明你有資料，請在 "Proof" 欄位中，寫出一句該平台對這家店的 **具體短評 (Quote)** 或 **特色描述**。
                    3. **如果你寫不出具體的 Proof，就代表你其實不確定，請直接剔除這家店，不要列出來。**
                    
                    【輸出格式】
                    每一行一家餐廳，格式如下(直立線分隔)：
                    Name: 餐廳名 | Style: 風格 | Rating: Google評分 | Proof: 來自Le Fooding/TheFork的具體短評

                    範例：
                    Name: Le Louvre | Style: 法式 | Rating: 4.2 | Proof: Le Fooding 形容它是「羅浮宮旁的避世天堂」
                    Name: Zen | Style: 拉麵 | Rating: 4.6 | Proof: TheFork 用戶大推它的豚骨湯頭，常有30%折扣
                    """
                    
                    response = model.generate_content(explore_prompt)
                    
                    st.success(f"✨ 在 {location_input} 附近找到以下「有憑有據」的餐廳：")
                    
                    lines = response.text.split('\n')
                    found_any = False
                    for line in lines:
                        if "Name:" in line:
                            found_any = True
                            clean_line = line.replace("*", "").strip()
                            parts = clean_line.split('|')
                            
                            r_name_raw = parts[0].replace("Name:", "").strip() if len(parts) > 0 else "未知餐廳"
                            r_style = parts[1].replace("Style:", "").strip() if len(parts) > 1 else "風格未知"
                            r_rating = parts[2].replace("Rating:", "").strip() if len(parts) > 2 else "N/A"
                            r_proof = parts[3].replace("Proof:", "").strip() if len(parts) > 3 else "資料驗證中..."
                            
                            col_a, col_b = st.columns([3, 1])
                            with col_a:
                                st.markdown(f"""
                                **{r_name_raw}** ⭐ **{r_rating}** <small style='color:#2E7D32'>📝 {r_proof}</small>  
                                <small style='color:gray'>類型: {r_style}</small>
                                """, unsafe_allow_html=True)
                                
                            with col_b:
                                def set_name(n=r_name_raw):
                                    st.session_state.target_restaurant = n
                                st.button("分析它 👉", key=f"btn_{r_name_raw}", on_click=set_name)
                            
                            st.divider()
                    
                    if not found_any:
                        st.warning("篩選過於嚴格，AI 找不到它敢保證有資料的附近餐廳。")
                                
            except Exception as e:
                if "429" in str(e):
                    st.error("🐢 抱歉，免費版 AI 累了 (429 Error)。請等待 30-60 秒後再試一次！")
                else:
                    st.error(f"發生錯誤: {e}")

    if st.session_state.target_restaurant:
        st.info(f"已選擇：**{st.session_state.target_restaurant}**，請回「🔍 直接搜尋餐廳」分頁查看詳情。")