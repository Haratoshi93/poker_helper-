import streamlit as st
import pandas as pd
import plotly.express as px
from poker_calc import calculate_equity, get_hand_type

st.set_page_config(page_title="Texas Hold'em Analyzer", layout="centered", initial_sidebar_state="collapsed")

# ゴージャスかつスマホ（モバイル）に最適化されたカスタムCSS
st.markdown("""
<style>
    /* 全体の余白を極限まで詰めてスマホの画面を広く使う */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
    }
    /* 勝率などの数値をスマホでも1行に収まるスタイリッシュなサイズに */
    [data-testid="stMetricValue"] { 
        font-size: 2.8rem !important; 
        color: #d4af37 !important; 
        font-weight: bold;
    }
    [data-testid="stMetricLabel"] {
        color: #a0a0a0 !important;
        font-weight: bold;
        letter-spacing: 1px;
        font-size: 1.0rem !important;
    }
    /* 見出しのデザインとフォントサイズのスマホ最適化 */
    h1 { font-size: 1.8rem !important; }
    h2 { font-size: 1.5rem !important; }
    h3 { font-size: 1.2rem !important; letter-spacing: 1px; }
    h4 { font-size: 1.0rem !important; }
    h1, h2, h3, h4 { 
        color: #d4af37 !important; 
        font-family: 'Georgia', serif;
        border-bottom: 1px solid #333;
        padding-bottom: 5px;
        margin-bottom: 10px;
    }
    
    /* 自作ボタンピッカー（st.button）のフォントをさらに大きく */
    button[data-testid="baseButton-secondary"],
    button[data-testid="baseButton-primary"] {
        min-height: 3.5rem !important;
    }
    button[data-testid="baseButton-secondary"] p,
    button[data-testid="baseButton-primary"] p {
        font-size: 1.6rem !important;
        font-weight: bold !important;
    }
    
    /* カード画像を中央寄せにする */
    [data-testid="stImage"] {
        display: flex;
        justify-content: center;
    }
    [data-testid="stImage"] img {
        margin: 0 auto;
    }
    
    /* 区切り線をさりげなく */
    hr {
        border-color: #333 !important;
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("Texas Hold'em Analyzer")

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

# --- リセット処理 ---
def reset_cards():
    for key in list(st.session_state.keys()):
        if key.startswith("s_") or key.startswith("h_") or key.startswith("f_") or key.startswith("t_") or key.startswith("r_"):
            del st.session_state[key]
    used_cards.clear()

used_cards = set()

# 確実に大きく押しやすい自作ボタンピッカー（CSSハック不要）
def card_picker(label, prefix):
    st.markdown(f"**{label}**")
    suit_key = f"s_{prefix}_suit"
    final_key = f"s_{prefix}_final"
    
    # 既に確定している場合
    if final_key in st.session_state and st.session_state[final_key]:
        return st.session_state[final_key]
        
    # マークの選択
    suit = st.session_state.get(suit_key)
    cols = st.columns(4)
    for i, s in enumerate(suits):
        btn_type = "primary" if suit == s else "secondary"
        if cols[i].button(format_suit(s), key=f"btn_{prefix}_suit_{s}", use_container_width=True, type=btn_type):
            st.session_state[suit_key] = s
            st.rerun()
            
    # マークが選ばれたら数字の選択を表示
    if suit:
        avail_ranks = [r for r in ranks if f"{r}{suit}" not in used_cards]
        rank_cols = st.columns(5) # 5列のグリッド
        for i, r in enumerate(avail_ranks):
            if rank_cols[i % 5].button(format_rank(r), key=f"btn_{prefix}_rank_{r}", use_container_width=True):
                card_code = f"{r}{suit}"
                st.session_state[final_key] = card_code
                used_cards.add(card_code)
                st.rerun()
    return None

# --- 1. 人数設定 ---
st.markdown("### VILLAINS (対戦人数)")
num_villains = st.slider("対戦人数を選択してください", min_value=1, max_value=8, value=1, label_visibility="collapsed")

# --- 2. 手札設定 ---
st.markdown("### HOLE CARDS")
hero_cards = []
with st.container(border=True):
    hero1 = card_picker("Card 1", "h1")
    if hero1:
        hero_cards.append(hero1)
        # 1枚目が選ばれたら2枚目を表示
        st.markdown("---")
        hero2 = card_picker("Card 2", "h2")
        if hero2:
            hero_cards.append(hero2)

# --- 3. プリフロップ判定（最重要機能） ---
if len(hero_cards) == 2:
    st.markdown("### PREFLOP ANALYSIS")
    
    with st.spinner('Calculating Equity...'):
        win_rate, tie_rate = calculate_equity(hero_cards, [], num_villains, iterations=2000)

    def get_preflop_advice(win_rate, num_villains):
        fair_share = 1.0 / (num_villains + 1)
        if win_rate >= fair_share * 1.5:
            return "success", "Rank S : 非常に有利 (トップクラス)"
        elif win_rate >= fair_share * 1.1:
            return "info", "Rank A : 有利 (平均以上の強さ)"
        elif win_rate >= fair_share * 0.8:
            return "warning", "Rank B : 注意 (平均以下の強さ)"
        else:
            return "error", "Rank C : 厳しい (勝つのは困難)"

    with st.container(border=True):
        st.markdown("**Hand Potential (手札のポテンシャル)**")
        msg_type, msg_text = get_preflop_advice(win_rate, num_villains)
        if msg_type == "success": st.success(msg_text)
        elif msg_type == "info": st.info(msg_text)
        elif msg_type == "warning": st.warning(msg_text)
        elif msg_type == "error": st.error(msg_text)
        
        # 画像と勝率を横に並べて表示（画像サイズを小さく）
        res_c1, res_c2, res_c3 = st.columns([1, 1, 2])
        with res_c1:
            st.image(get_card_image_url(hero_cards[0]), use_container_width=True)
        with res_c2:
            st.image(get_card_image_url(hero_cards[1]), use_container_width=True)
        with res_c3:
            st.metric("WIN % (勝率)", f"{win_rate*100:.1f}%")

    st.button("RESET CARDS", on_click=reset_cards, use_container_width=True, type="primary")

    # --- 4. オプション機能（フロップ以降） ---
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("ADVANCED: Postflop Simulation (フロップ以降の解析)", expanded=False):
        st.markdown("場の共通カード (Community Cards) を展開して解析します。")
        
        board_cards = []
        with st.container(border=True):
            st.markdown("**COMMUNITY CARDS**")
            b_cols = st.columns(5)
            
            f1 = card_picker("Flop 1", "f1")
            if f1:
                board_cards.append(f1)
                b_cols[0].image(get_card_image_url(f1), use_container_width=True)
                
                f2 = card_picker("Flop 2", "f2")
                if f2:
                    board_cards.append(f2)
                    b_cols[1].image(get_card_image_url(f2), use_container_width=True)
                    
                    f3 = card_picker("Flop 3", "f3")
                    if f3:
                        board_cards.append(f3)
                        b_cols[2].image(get_card_image_url(f3), use_container_width=True)
                        
                        t = card_picker("Turn (4th)", "t")
                        if t:
                            board_cards.append(t)
                            b_cols[3].image(get_card_image_url(t), use_container_width=True)
                            
                            r = card_picker("River (5th)", "r")
                            if r:
                                board_cards.append(r)
                                b_cols[4].image(get_card_image_url(r), use_container_width=True)
        
        if board_cards:
            st.markdown("#### Postflop Analysis Result")
            with st.spinner('Simulating...'):
                wr_board, tr_board = calculate_equity(hero_cards, board_cards, num_villains, iterations=1000)
            
            with st.container(border=True):
                hand_type = get_hand_type(hero_cards, board_cards)
                st.markdown(f"**Current Made Hand:** {hand_type}")
                st.metric("WIN % (勝率)", f"{wr_board*100:.1f}%")
                
            st.markdown("#### Equity Chart")
            phases = ["Preflop", "Flop", "Turn", "River"]
            equity_history = []
            
            equity_history.append({"Phase": phases[0], "Equity": win_rate * 100})
            
            for i in [3, 4, 5]:
                if len(board_cards) >= i:
                    current_board = board_cards[:i]
                    wr, _ = calculate_equity(hero_cards, current_board, num_villains, iterations=1000)
                    equity_history.append({"Phase": phases[[3, 4, 5].index(i) + 1], "Equity": wr * 100})

            if len(equity_history) > 1:
                df = pd.DataFrame(equity_history)
                # グラフもダークテーマに合わせる
                fig = px.line(df, x="Phase", y="Equity", markers=True, range_y=[0, 100], template="plotly_dark")
                fig.update_traces(line=dict(color="#d4af37", width=4), marker=dict(size=10, color="#ffffff"), textposition="top center")
                fig.update_layout(
                    margin=dict(l=20, r=20, t=20, b=20),
                    paper_bgcolor="#121212",
                    plot_bgcolor="#1e1e1e"
                )
                st.plotly_chart(fig, use_container_width=True)
