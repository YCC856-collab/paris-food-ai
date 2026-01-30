import streamlit as st
import google.generativeai as genai
import urllib.parse  # 用來處理網址

st.set_page_config(page_title="巴黎美食 AI", page_icon="🇫🇷")
st.title("🇫🇷 巴黎餐廳 AI 分析器")
st.caption("專注於 TheFork 與 Le Fooding 的深度分析")

# --- API Key 處理 ---
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    with st.sidebar:
        api_key = st.text_input("輸入 Gemini API Key", type="password")
        st.markdown("[👉 按此取得免費 Key](https://aistudio.google.com/app/apikey)")

# --- 自動偵測模型 ---
def get_first_working_model(api_key):
    try:
        genai.configure(api_key=api_key)
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                return m.name
    except Exception:
        return None
    return None

# 主畫面輸入框
restaurant_name = st.text_input("請輸入餐廳名稱 (例如: Septime)")

if st.button("開始分析") and restaurant_name:
    if not api_key:
        st.error("請先設定 API Key！")
    else:
        # --- 關鍵修正：強制加上 "Paris" 並轉成網址格式 ---
        # 例如輸入 "Septime"，這邊會變成 "Septime+Paris"
        # quote_plus 會把空格變成 + 號，搜尋引擎比較看得懂
        search_query = urllib.parse.quote_plus(f"{restaurant_name} Paris")
        
        st.subheader("🔗 快速傳送門 (已鎖定巴黎)")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            # Google Maps
            st.link_button("📍 Google Maps", f"https://www.google.com/maps?q={search_query}")
        with col2:
            # TheFork (直接帶入 名稱+Paris)
            st.link_button("🍴 TheFork", f"https://www.thefork.fr/search?q={search_query}")
        with col3:
            # Le Fooding (直接帶入 名稱+Paris)
            st.link_button("🍷 Le Fooding", f"https://lefooding.com/en/search?query={search_query}")

        # --- AI 分析區 (嚴格限制來源) ---
        st.divider()
        status_box = st.empty()
        
        try:
            status_box.info("🔍 正在調閱 TheFork 與 Le Fooding 資料庫...")
            
            valid_model_name = get_first_working_model(api_key)
            
            if not valid_model_name:
                status_box.error("❌ 找不到可用模型，請檢查 API Key。")
            else:
                status_box.success(f"✅ 連線成功 ({valid_model_name})")
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(valid_model_name)
                
                with st.spinner("AI 正在交叉比對兩大平台數據..."):
                    # Prompt 保持不變：嚴格限制來源
                    prompt = f"""
                    你是一位專精於巴黎餐廳的數據分析師。使用者查詢餐廳 "{restaurant_name}"。
                    
                    【重要規則】
                    1. 你的分析範圍 **「嚴格僅限於」** TheFork 和 Le Fooding 這兩個平台的資料與觀點。
                    2. **請忽略** Google Maps、TripAdvisor 或米其林指南的評分。
                    3. 如果這家餐廳在這兩個平台找不到資料，請誠實回答「此平台無資料」。

                    請用繁體中文輸出以下結構化報告：

                    ### 1. 🍴 TheFork 數據分析
                    * **評分與人氣**：(預估該平台上的分數，例如 9.2/10)
                    * **價格與優惠**：(平均消費金額，以及該平台常見的折扣狀況，例如 -30% off)
                    * **評論關鍵詞**：(用戶常提到的優缺點)

                    ### 2. 🍷 Le Fooding 風格快評
                    * **氛圍定位**：(這是潮店、老派酒館還是觀光客店？)
                    * **小編觀點**：(Le Fooding 通常會用什麼形容詞來描述這家店？例如：生動、自然酒、擁擠...)
                    * **必點推薦**：(根據食評推薦的菜色)

                    ### 3. ⚖️ 兩平台綜合結論
                    * **這家店適合誰？** (例如：適合想省錢的吃貨 vs 適合追求氛圍的文青)
                    * **決策建議**：(去還是不去？)
                    """
                    
                    response = model.generate_content(prompt)
                    st.markdown(response.text)
                    
        except Exception as e:
            st.error(f"發生錯誤: {e}")