import streamlit as st
import pandas as pd
import plotly.express as px
from poker_calc import calculate_equity, get_hand_type

# スマホ向けに中央寄せ（centered）、サイドバーは最初から閉じるか使わない
st.set_page_config(page_title="Poker Helper", layout="centered", initial_sidebar_state="collapsed")

# カスタムCSSで全体をおしゃれに
st.markdown("""
<style>
    /* 全体のフォントや余白の微調整 */
    .main {
        background-color: #f8fafc;
    }
    /* メトリクス（勝率などの数字）を大きく見やすく */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem !important;
        color: #1e3a8a;
    }
    h1, h2, h3 {
        color: #0f172a;
    }
</style>
""", unsafe_allow_html=True)

st.title("🃏 Poker Helper")
st.markdown("スマホでサクサク使える！ポーカー勝率計算アプリ")

# --- 定義 ---
ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
suits = ['s', 'h', 'd', 'c']
suit_icon = {'s': '♠', 'h': '♥', 'd': '♦', 'c': '♣'}
rank_map_display = {'T': '10'} 

def format_suit(s): return suit_icon[s]
def format_rank(r): return rank_map_display.get(r, r)
def format_card_full(card_code):
    return f"{suit_icon[card_code[1]]} {format_rank(card_code[0])}"

def get_card_image_url(card_code):
    rank = card_code[0].upper()
    suit = card_code[1].upper()
    if rank == 'T': rank = '0'
    return f"https://deckofcardsapi.com/static/img/{rank}{suit}.png"

used_cards = set()

# --- 1. 人数設定 ---
st.markdown("### 👥 1. 対戦相手の人数")
num_villains = st.slider("あなた以外のプレイヤー数を設定してください", min_value=1, max_value=8, value=1)

# --- 2. 手札設定 ---
st.markdown("### 🎴 2. あなたの手札")
# 枠付きコンテナで囲んでカードっぽく見せる
with st.container(border=True):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**1枚目**")
        suit1 = st.radio("マーク1", suits, format_func=format_suit, key="s1", horizontal=True, label_visibility="collapsed")
        avail_ranks1 = [r for r in ranks if f"{r}{suit1}" not in used_cards]
        rank1 = st.selectbox("数字1", avail_ranks1, format_func=format_rank, key="r1", label_visibility="collapsed")
        hero1 = f"{rank1}{suit1}"
        used_cards.add(hero1)
        # 選択したカードの画像をすぐに表示（スマホでも見やすいサイズに）
        st.image(get_card_image_url(hero1), width=120)

    with col2:
        st.markdown("**2枚目**")
        suit2 = st.radio("マーク2", suits, format_func=format_suit, key="s2", horizontal=True, label_visibility="collapsed")
        avail_ranks2 = [r for r in ranks if f"{r}{suit2}" not in used_cards]
        rank2 = st.selectbox("数字2", avail_ranks2, format_func=format_rank, key="r2", label_visibility="collapsed")
        hero2 = f"{rank2}{suit2}"
        used_cards.add(hero2)
        st.image(get_card_image_url(hero2), width=120)

hero_cards = [hero1, hero2]

# --- 3. 場のカード設定 ---
st.markdown("### 🌐 3. 場の共通カード")
with st.container(border=True):
    available_board_cards = [f"{r}{s}" for s in suits for r in ranks if f"{r}{s}" not in used_cards]
    board_cards = st.multiselect("開かれたカードを選んでください（最大5枚）", available_board_cards, format_func=format_card_full, max_selections=5)
    
    if board_cards:
        b_cols = st.columns(5)
        for i, card in enumerate(board_cards):
            with b_cols[i]:
                st.image(get_card_image_url(card), use_container_width=True)
    else:
        st.caption("※まだ場のカードが開かれていない（プリフロップ）状態です")

# --- 4. 結果表示 ---
st.markdown("---")
st.markdown("### 📊 分析結果")

with st.spinner('AIが数千回のシミュレーションを実行中...'):
    win_rate, tie_rate = calculate_equity(hero_cards, board_cards, num_villains)

def get_strength_text(win_rate, num_villains):
    fair_share = 1.0 / (num_villains + 1)
    if win_rate >= fair_share * 1.5: return "🔥 かなり強い！"
    elif win_rate >= fair_share * 1.0: return "👍 平均より少し強い"
    elif win_rate >= fair_share * 0.7: return "⚠️ 注意 (少し不利)"
    else: return "❄️ 厳しい (フォールド推奨)"

# 結果を大きく表示するコンテナ
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
    # おしゃれな白いテーマのグラフ
    fig = px.line(df, x="フェーズ", y="勝率", markers=True, range_y=[0, 100], template="plotly_white")
    fig.update_traces(
        line=dict(color="#2563eb", width=4), # 線の色と太さ
        marker=dict(size=10, color="#ef4444"), # マーカーの色と大きさ
        textposition="top center"
    )
    # スマホで見やすいように余白を調整
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)
