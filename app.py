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
        font-size: 2.4rem !important; 
        color: #d4af37 !important; 
        font-family: 'Georgia', serif;
    }
    [data-testid="stMetricLabel"] {
        color: #a0a0a0 !important;
        font-weight: bold;
        letter-spacing: 1px;
        font-size: 0.9rem !important;
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
    /* ピル（タップボタン）のフォントと余白を大きくして親指で押しやすく */
    [data-testid="stPill"] {
        font-size: 1.1rem !important;
        padding: 0.5rem 1rem !important;
    }
    /* ラジオボタンやピルのコンテナの隙間を調整 */
    .stRadio > div { flex-wrap: wrap; gap: 8px; }
    
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
    keys_to_reset = [
        'h1_suit', 'h1_rank', 'h2_suit', 'h2_rank',
        'f1_suit', 'f1_rank', 'f2_suit', 'f2_rank', 'f3_suit', 'f3_rank',
        't_suit', 't_rank', 'r_suit', 'r_rank'
    ]
    for k in keys_to_reset:
        if k in st.session_state:
            st.session_state[k] = None

used_cards = set()

def card_picker(label_prefix, key_prefix):
    st.markdown(f"**{label_prefix}**")
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
st.markdown("### VILLAINS (対戦人数)")
num_villains = st.slider("対戦人数を選択してください", min_value=1, max_value=8, value=1, label_visibility="collapsed")

# --- 2. 手札設定 (メイン機能) ---
st.markdown("### HOLE CARDS")
hero_cards = []
with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
        hero1 = card_picker("Card 1", "h1")
        if hero1:
            st.image(get_card_image_url(hero1), width=120)
            hero_cards.append(hero1)
    with col2:
        if hero1:
            hero2 = card_picker("Card 2", "h2")
            if hero2:
                st.image(get_card_image_url(hero2), width=120)
                hero_cards.append(hero2)

# --- 3. プリフロップ判定（最重要機能） ---
if len(hero_cards) == 2:
    st.markdown("### PREFLOP ANALYSIS")
    
    with st.spinner('Calculating Equity...'):
        win_rate, tie_rate = calculate_equity(hero_cards, [], num_villains, iterations=2000)

    def get_preflop_advice(win_rate, num_villains):
        fair_share = 1.0 / (num_villains + 1)
        if win_rate >= fair_share * 1.5:
            return "[Tier 1] 非常に強い手札です (Premium Hand)"
        elif win_rate >= fair_share * 1.1:
            return "[Tier 2] 平均より強い手札です (Strong Hand)"
        elif win_rate >= fair_share * 0.8:
            return "[Tier 3] やや弱めの手札です (Marginal Hand)"
        else:
            return "[Tier 4] 弱い手札です (Weak Hand)"

    with st.container(border=True):
        st.markdown(f"**Analysis Result**\n\n{get_preflop_advice(win_rate, num_villains)}")
        res_col1, res_col2 = st.columns(2)
        res_col1.metric("WIN %", f"{win_rate*100:.1f}%")
        res_col2.metric("TIE %", f"{tie_rate*100:.1f}%")

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
                st.metric("WIN %", f"{wr_board*100:.1f}%")
                
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
