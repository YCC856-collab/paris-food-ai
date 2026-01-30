import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="巴黎美食 AI", page_icon="🇫🇷")
st.title("🇫🇷 巴黎餐廳 AI 分析器")
st.caption("輸入餐廳，AI 自動調用您帳號可用的模型進行分析")

# 左側輸入 API Key
with st.sidebar:
    api_key = st.text_input("輸入 Gemini API Key", type="password")
    st.markdown("[👉 按此取得免費 Key](https://aistudio.google.com/app/apikey)")

# --- 關鍵功能：直接問系統有哪些模型可用 ---
def get_first_working_model(api_key):
    """
    不猜測模型名稱，直接列出帳號下可用的模型，並回傳第一個。
    """
    try:
        genai.configure(api_key=api_key)
        # 列出所有模型
        for m in genai.list_models():
            # 只要該模型支援「文字生成 (generateContent)」，就直接選它
            if 'generateContent' in m.supported_generation_methods:
                return m.name # 直接回傳系統給的名稱 (例如 models/gemini-pro)
    except Exception as e:
        return None
    return None

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
        status_box = st.empty() # 建立一個狀態顯示框
        
        try:
            status_box.info("🔍 正在尋找您帳號可用的 AI 模型...")
            
            # 自動抓取正確的模型名稱
            valid_model_name = get_first_working_model(api_key)
            
            if not valid_model_name:
                status_box.error("❌ 找不到任何可用模型！請確認您的 API Key 是否正確，或是否已在 Google AI Studio 開通權限。")
            else:
                status_box.success(f"✅ 成功連線！使用模型：{valid_model_name}")
                
                # 建立模型
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(valid_model_name)
                
                with st.spinner("AI 正在撰寫分析報告..."):
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
            st.error(f"發生未預期的錯誤: {e}")