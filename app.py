import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="巴黎美食 AI", page_icon="🇫🇷")

st.title("🇫🇷 巴黎餐廳 AI 分析器")
st.caption("輸入餐廳，一鍵比對 TheFork, Le Fooding 與 Google 評價")

# 左側輸入 API Key
with st.sidebar:
    api_key = st.text_input("輸入 Gemini API Key", type="password")
    st.markdown("[👉 按此取得免費 Key](https://aistudio.google.com/app/apikey)")

# --- 關鍵功能：自動偵測可用模型 (避免 429 錯誤) ---
def get_best_model(api_key):
    """
    自動向 Google 查詢目前可用的模型，優先選擇 1.5 Flash。
    """
    try:
        genai.configure(api_key=api_key)
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        # 1. 優先尋找最穩定的 1.5 flash
        for model in available_models:
            if 'gemini-1.5-flash' in model:
                return model
        
        # 2. 如果沒有，就找任何含有 flash 的 (通常較快且免費)
        for model in available_models:
            if 'flash' in model:
                return model
                
        # 3. 真的都沒有，就回傳清單中的第一個
        return available_models[0] if available_models else 'gemini-1.5-flash'
    except:
        # 如果查詢失敗，直接回傳最穩定的預設值
        return 'gemini-1.5-flash'

# 主畫面輸入框
restaurant_name = st.text_input("請輸入餐廳名稱 (例如: Septime)")

if st.button("開始分析") and restaurant_name:
    if not api_key:
        st.error("請先在左側輸入 API Key 喔！")
    else:
        # 1. 連結區
        st.subheader("🔗 快速傳送門")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.link_button("Google Maps", f"https://www.google.com/maps/search/{restaurant_name}+Paris")
        with col2:
            st.link_button("TheFork (訂位)", f"https://www.thefork.fr/search?q={restaurant_name}")
        with col3:
            st.link_button("Le Fooding (食評)", f"https://lefooding.com/en/search?query={restaurant_name}")

        # 2. AI 分析
        st.divider()
        try:
            # 呼叫自動偵測函式
            model_name = 'gemini-1.5-flash'
            
            # 建立模型
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash-001')
            
            with st.spinner(f"AI 正在連線分析中 (使用核心: {model_name})..."):
                prompt = f"""
                你是一位嚴格的巴黎美食評論家。使用者想去 "{restaurant_name}"。
                請用繁體中文分析：
                1.這家店的風格與定位？
                2.必點的 2 道菜是什麼？
                3.有什麼缺點或地雷？(例如難訂位、服務差、遊客太多)
                4.綜合評分 (1-10分) 與一句話結論。
                """
                response = model.generate_content(prompt)
                st.markdown(response.text)
        except Exception as e:
            st.error(f"發生錯誤: {e}")