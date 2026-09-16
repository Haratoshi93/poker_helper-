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
    .stRadio > div { flex-wrap: wrap; }
</style>
""", unsafe_allow_html=True)

st.title("🃏 Poker Helper")
st.markdown("初心者のための「参加すべきか？」がすぐ分かるアプリ")

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
st.markdown("### 👥 1. 対戦相手の人数")
num_villains = st.slider("あなた以外のプレイヤー数を設定してください", min_value=1, max_value=8, value=1)

# --- 2. 手札設定 (メイン機能) ---
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
        if hero1:
            hero2 = card_picker("2枚目", "h2")
            if hero2:
                st.image(get_card_image_url(hero2), width=100)
                hero_cards.append(hero2)

# --- 3. プリフロップ判定（最重要機能） ---
if len(hero_cards) == 2:
    st.markdown("---")
    st.markdown("### 🎯 手札のポテンシャル（強さの目安）")
    
    with st.spinner('勝率を計算中...'):
        win_rate, tie_rate = calculate_equity(hero_cards, [], num_villains, iterations=2000)

    def get_preflop_advice(win_rate, num_villains):
        fair_share = 1.0 / (num_villains + 1)
        if win_rate >= fair_share * 1.5:
            return "🔥 非常に強い手札です (勝率上位クラス)"
        elif win_rate >= fair_share * 1.1:
            return "👍 平均より強い手札です"
        elif win_rate >= fair_share * 0.8:
            return "⚠️ やや弱めの手札です (平均を下回っています)"
        else:
            return "❄️ 弱い手札です (厳しい戦いが予想されます)"

    with st.container(border=True):
        st.success(f"**【手札の強さの目安】**\n\n{get_preflop_advice(win_rate, num_villains)}")
        res_col1, res_col2 = st.columns(2)
        res_col1.metric("現在の勝率", f"{win_rate*100:.1f}%")
        res_col2.metric("引き分け率", f"{tie_rate*100:.1f}%")

    st.button("🔄 カードをリセットして次のゲームへ", on_click=reset_cards, use_container_width=True, type="primary")

    # --- 4. オプション機能（フロップ以降） ---
    st.markdown("---")
    with st.expander("🔍 オプション：フロップ以降の勝率シミュレーション", expanded=False):
        st.markdown("場に共通カードが出た後の展開を分析したい場合は、こちらに入力してください。")
        
        board_cards = []
        with st.container(border=True):
            st.markdown("**現在のボード**")
            b_cols = st.columns(5)
            
            f1 = card_picker("フロップ 1枚目", "f1")
            if f1:
                board_cards.append(f1)
                b_cols[0].image(get_card_image_url(f1), use_container_width=True)
                
                f2 = card_picker("フロップ 2枚目", "f2")
                if f2:
                    board_cards.append(f2)
                    b_cols[1].image(get_card_image_url(f2), use_container_width=True)
                    
                    f3 = card_picker("フロップ 3枚目", "f3")
                    if f3:
                        board_cards.append(f3)
                        b_cols[2].image(get_card_image_url(f3), use_container_width=True)
                        
                        t = card_picker("ターン (4枚目)", "t")
                        if t:
                            board_cards.append(t)
                            b_cols[3].image(get_card_image_url(t), use_container_width=True)
                            
                            r = card_picker("リバー (5枚目)", "r")
                            if r:
                                board_cards.append(r)
                                b_cols[4].image(get_card_image_url(r), use_container_width=True)
        
        if board_cards:
            st.markdown("#### 分析結果 (フロップ以降)")
            with st.spinner('最新のボードで計算中...'):
                wr_board, tr_board = calculate_equity(hero_cards, board_cards, num_villains, iterations=1000)
            
            with st.container(border=True):
                hand_type = get_hand_type(hero_cards, board_cards)
                st.info(f"**あなたの現在の役:** {hand_type}")
                st.metric("現在の勝率", f"{wr_board*100:.1f}%")
                
            st.markdown("#### 📈 勝率の推移グラフ")
            phases = ["プリフロップ", "フロップ", "ターン", "リバー"]
            equity_history = []
            
            # プリフロップは計算済み
            equity_history.append({"フェーズ": phases[0], "勝率": win_rate * 100})
            
            # それ以降の計算
            for i in [3, 4, 5]:
                if len(board_cards) >= i:
                    current_board = board_cards[:i]
                    wr, _ = calculate_equity(hero_cards, current_board, num_villains, iterations=1000)
                    equity_history.append({"フェーズ": phases[[3, 4, 5].index(i) + 1], "勝率": wr * 100})

            if len(equity_history) > 1:
                df = pd.DataFrame(equity_history)
                fig = px.line(df, x="フェーズ", y="勝率", markers=True, range_y=[0, 100], template="plotly_white")
                fig.update_traces(line=dict(color="#2563eb", width=4), marker=dict(size=10, color="#ef4444"), textposition="top center")
                fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig, use_container_width=True)
