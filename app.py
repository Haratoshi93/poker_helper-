import streamlit as st
import pandas as pd
import plotly.express as px
from poker_calc import calculate_equity, get_hand_type

st.set_page_config(page_title="Poker Helper", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .main { background-color: #f8fafc; }
    [data-testid="stMetricValue"] { font-size: 2.5rem !important; color: #1e3a8a; }
    h1, h2, h3, h4 { color: #0f172a; }
    /* pillsやradioの隙間を調整 */
    .stRadio > div { flex-wrap: wrap; }
</style>
""", unsafe_allow_html=True)

st.title("🃏 Poker Helper")
st.markdown("スマホでサクサク使える！ポーカー勝率計算アプリ")

ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
suits = ['s', 'h', 'd', 'c']
suit_icon = {'s': '♠', 'h': '♥', 'd': '♦', 'c': '♣'}
rank_map_display = {'T': '10'} 

def format_suit(s): return suit_icon[s]
def format_rank(r): return rank_map_display.get(r, r)

def get_card_image_url(card_code):
    rank = card_code[0].upper()
    suit = card_code[1].upper()
    if rank == 'T': rank = '0'
    return f"https://deckofcardsapi.com/static/img/{rank}{suit}.png"

used_cards = set()

# --- 究極に簡単なカードピッカー関数 ---
# プルダウンを一切使わず、ボタン（pills）を押すだけで選べるようにする
def card_picker(label_prefix, key_prefix):
    st.markdown(f"**{label_prefix}**")
    # Streamlitのpillsコンポーネント（タップしやすいボタン群）を使用
    suit = st.pills(f"{key_prefix}_suit_label", suits, format_func=format_suit, key=f"{key_prefix}_suit", label_visibility="collapsed")
    if suit:
        avail_ranks = [r for r in ranks if f"{r}{suit}" not in used_cards]
        rank = st.pills(f"{key_prefix}_rank_label", avail_ranks, format_func=format_rank, key=f"{key_prefix}_rank", label_visibility="collapsed")
        if rank:
            card_code = f"{rank}{suit}"
            used_cards.add(card_code)
            return card_code
    return None

# --- 1. 人数設定 ---
st.markdown("### 👥 1. 対戦相手の人数")
num_villains = st.slider("あなた以外のプレイヤー数を設定してください", min_value=1, max_value=8, value=1)

# --- 2. 手札設定 ---
st.markdown("### 🎴 2. あなたの手札")
hero_cards = []
with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
        hero1 = card_picker("1枚目", "h1")
        if hero1:
            st.image(get_card_image_url(hero1), width=100)
            hero_cards.append(hero1)
    with col2:
        if hero1: # 1枚目が選ばれたら2枚目を出せるようにする
            hero2 = card_picker("2枚目", "h2")
            if hero2:
                st.image(get_card_image_url(hero2), width=100)
                hero_cards.append(hero2)

# --- 3. 場のカード設定 ---
board_cards = []
st.markdown("### 🌐 3. 場の共通カード")
with st.container(border=True):
    if len(hero_cards) == 2:
        # 画像表示エリア（上部）
        st.markdown("**現在のボード**")
        b_cols = st.columns(5)
        
        # フロップ1枚目
        f1 = card_picker("フロップ 1枚目", "f1")
        if f1:
            board_cards.append(f1)
            b_cols[0].image(get_card_image_url(f1), use_container_width=True)
            
            # フロップ2枚目
            f2 = card_picker("フロップ 2枚目", "f2")
            if f2:
                board_cards.append(f2)
                b_cols[1].image(get_card_image_url(f2), use_container_width=True)
                
                # フロップ3枚目
                f3 = card_picker("フロップ 3枚目", "f3")
                if f3:
                    board_cards.append(f3)
                    b_cols[2].image(get_card_image_url(f3), use_container_width=True)
                    
                    # ターン
                    t = card_picker("ターン (4枚目)", "t")
                    if t:
                        board_cards.append(t)
                        b_cols[3].image(get_card_image_url(t), use_container_width=True)
                        
                        # リバー
                        r = card_picker("リバー (最後の5枚目)", "r")
                        if r:
                            board_cards.append(r)
                            b_cols[4].image(get_card_image_url(r), use_container_width=True)
                            
        if not board_cards:
            st.caption("※まだ場のカードは開かれていません（プリフロップ）")
    else:
        st.info("※まずはあなたの手札を2枚選んでください！")

# --- 4. 結果表示 ---
st.markdown("---")
st.markdown("### 📊 分析結果")

if len(hero_cards) == 2:
    with st.spinner('AIが数千回のシミュレーションを実行中...'):
        win_rate, tie_rate = calculate_equity(hero_cards, board_cards, num_villains)

    def get_strength_text(win_rate, num_villains):
        fair_share = 1.0 / (num_villains + 1)
        if win_rate >= fair_share * 1.5: return "🔥 かなり強い！"
        elif win_rate >= fair_share * 1.0: return "👍 平均より少し強い"
        elif win_rate >= fair_share * 0.7: return "⚠️ 注意 (少し不利)"
        else: return "❄️ 厳しい (フォールド推奨)"

    with st.container(border=True):
        res_col1, res_col2 = st.columns(2)
        res_col1.metric("👑 現在の勝率", f"{win_rate*100:.1f}%")
        res_col2.metric("🤝 引き分け率", f"{tie_rate*100:.1f}%")
        
        if len(board_cards) >= 3:
            hand_type = get_hand_type(hero_cards, board_cards)
            st.success(f"**現在の役:** {hand_type}")
        else:
            st.info(f"**手札の強さ目安:** {get_strength_text(win_rate, num_villains)}")

    # --- 5. グラフ ---
    st.markdown("#### 📈 勝率の推移")
    phases = ["プリフロップ (0枚)", "フロップ (3枚)", "ターン (4枚)", "リバー (5枚)"]
    equity_history = []

    for i in [0, 3, 4, 5]:
        if len(board_cards) >= i:
            current_board = board_cards[:i]
            wr, _ = calculate_equity(hero_cards, current_board, num_villains, iterations=1000)
            equity_history.append({"フェーズ": phases[[0, 3, 4, 5].index(i)], "勝率": wr * 100})

    if equity_history:
        df = pd.DataFrame(equity_history)
        fig = px.line(df, x="フェーズ", y="勝率", markers=True, range_y=[0, 100], template="plotly_white")
        fig.update_traces(
            line=dict(color="#2563eb", width=4), 
            marker=dict(size=10, color="#ef4444"), 
            textposition="top center"
        )
        fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("手札を2枚選ぶと、勝率の分析結果が表示されます。")
