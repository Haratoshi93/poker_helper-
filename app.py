import streamlit as st
import pandas as pd
import plotly.express as px
from poker_calc import calculate_equity, get_hand_type

st.set_page_config(page_title="Poker Helper", layout="wide")

st.title("ポーカー 勝率可視化アプリ")
st.markdown("自分の手札と場のカードを設定して、勝率がどう変化するか確認しましょう。")

# --- 定義 ---
ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
suits = ['s', 'h', 'd', 'c']

# 表示用の変換ルール
suit_map = {'s': '♠ (スペード)', 'h': '♥ (ハート)', 'd': '♦ (ダイヤ)', 'c': '♣ (クラブ)'}
suit_icon = {'s': '♠', 'h': '♥', 'd': '♦', 'c': '♣'}
rank_map_display = {'T': '10'} 

def format_suit(s): return suit_icon[s]
def format_rank(r): return rank_map_display.get(r, r)
def format_card_full(card_code):
    return f"{suit_icon[card_code[1]]} の {format_rank(card_code[0])}"

# 画像URL取得関数
def get_card_image_url(card_code):
    rank = card_code[0].upper()
    suit = card_code[1].upper()
    if rank == 'T':
        rank = '0'
    return f"https://deckofcardsapi.com/static/img/{rank}{suit}.png"


# --- サイドバー：カード設定 ---
st.sidebar.header("🎴 カード設定")

# 使用済みのカードを記憶するセット（重複を防ぐため）
used_cards = set()

st.sidebar.subheader("あなたの手札（2枚）")

# 1枚目
st.sidebar.markdown("**1枚目**")
# マークを横並びのボタンで選択
suit1 = st.sidebar.radio("マーク1", suits, format_func=format_suit, key="s1", horizontal=True, label_visibility="collapsed")
# 選ばれたマークの中で、まだ使われていない数字だけを選択肢にする
avail_ranks1 = [r for r in ranks if f"{r}{suit1}" not in used_cards]
rank1 = st.sidebar.selectbox("数字1", avail_ranks1, format_func=format_rank, key="r1", label_visibility="collapsed")
hero1 = f"{rank1}{suit1}"
used_cards.add(hero1)

# 2枚目
st.sidebar.markdown("**2枚目**")
suit2 = st.sidebar.radio("マーク2", suits, format_func=format_suit, key="s2", horizontal=True, label_visibility="collapsed")
# 1枚目で選んだカードは、ここの選択肢から自動的に消える
avail_ranks2 = [r for r in ranks if f"{r}{suit2}" not in used_cards]
rank2 = st.sidebar.selectbox("数字2", avail_ranks2, format_func=format_rank, key="r2", label_visibility="collapsed")
hero2 = f"{rank2}{suit2}"
used_cards.add(hero2)

hero_cards = [hero1, hero2]

st.sidebar.markdown("---")
st.sidebar.subheader("場の共通カード（ボード）")
st.sidebar.markdown("開かれたカードを選んでください（最大5枚）")

# すでに手札で選ばれたカードを「除く」すべてのカードリスト
available_board_cards = [f"{r}{s}" for s in suits for r in ranks if f"{r}{s}" not in used_cards]

# ボードカードはマルチセレクトで。選んだ端からリストから消えるので重複しない
board_cards = st.sidebar.multiselect("共通カードを選択", available_board_cards, format_func=format_card_full, max_selections=5)

st.sidebar.markdown("---")
num_villains = st.sidebar.slider("対戦相手の人数", min_value=1, max_value=8, value=1)


# --- ビジュアル表示エリア ---
st.markdown("### 🃏 現在のカード")
col_hero, col_board = st.columns([1, 2])

with col_hero:
    st.markdown("**あなたの手札**")
    hc1, hc2, _ = st.columns([1, 1, 1])
    with hc1:
        st.image(get_card_image_url(hero1), use_container_width=True)
    with hc2:
        st.image(get_card_image_url(hero2), use_container_width=True)

with col_board:
    st.markdown("**場の共通カード**")
    if board_cards:
        b_cols = st.columns(5)
        for i, card in enumerate(board_cards):
            with b_cols[i]:
                st.image(get_card_image_url(card), use_container_width=True)
    else:
        st.info("まだ場のカードは開かれていません。")

st.markdown("---")

# --- 勝率計算と結果表示 ---
with st.spinner('勝率を計算中...'):
    win_rate, tie_rate = calculate_equity(hero_cards, board_cards, num_villains)

def get_strength_text(win_rate, num_villains):
    fair_share = 1.0 / (num_villains + 1)
    if win_rate >= fair_share * 1.5:
        return "🔥 かなり強い！ (有利)"
    elif win_rate >= fair_share * 1.0:
        return "👍 平均より少し強い"
    elif win_rate >= fair_share * 0.7:
        return "⚠️ 注意 (少し不利)"
    else:
        return "❄️ 厳しい (フォールド推奨)"

col1, col2, col3 = st.columns(3)
col1.metric("現在の勝率", f"{win_rate*100:.1f}%")
col2.metric("引き分け率", f"{tie_rate*100:.1f}%")
if len(board_cards) >= 3:
    hand_type = get_hand_type(hero_cards, board_cards)
    col3.metric("現在の役", hand_type)
else:
    col3.metric("手札の強さ目安", get_strength_text(win_rate, num_villains))

st.markdown("---")
st.subheader("📈 勝率の推移")
st.markdown("これまでのカードの開き具合による、勝率の変化グラフです。")

phases = ["プリフロップ (0枚)", "フロップ (3枚)", "ターン (4枚)", "リバー (5枚)"]
equity_history = []

for i in [0, 3, 4, 5]:
    if len(board_cards) >= i:
        current_board = board_cards[:i]
        wr, _ = calculate_equity(hero_cards, current_board, num_villains, iterations=1000)
        equity_history.append({"フェーズ": phases[[0, 3, 4, 5].index(i)], "勝率": wr * 100})

if equity_history:
    df = pd.DataFrame(equity_history)
    fig = px.line(df, x="フェーズ", y="勝率", markers=True, title="ゲーム進行に伴う勝率の変化", range_y=[0, 100])
    fig.update_traces(textposition="top center")
    st.plotly_chart(fig)
