import streamlit as st
import pandas as pd
import plotly.express as px
from poker_calc import calculate_equity, get_hand_type

st.set_page_config(page_title="Poker Helper", layout="wide")

st.title("ポーカー 勝率可視化アプリ")
st.markdown("自分の手札と場のカードを設定して、勝率がどう変化するか確認しましょう。")

# カードを初心者向けに表示するための関数
def format_card(card_code):
    suit_map = {'s': '♠ (スペード)', 'h': '♥ (ハート)', 'd': '♦ (ダイヤ)', 'c': '♣ (クラブ)'}
    rank_map = {'T': '10', 'J': 'J', 'Q': 'Q', 'K': 'K', 'A': 'A'}
    rank = card_code[0]
    suit = card_code[1]
    display_rank = rank_map.get(rank, rank)
    display_suit = suit_map.get(suit, suit)
    return f"{display_suit} の {display_rank}"

# カードの画像URLを取得する関数 (Deck of Cards APIを利用)
def get_card_image_url(card_code):
    rank = card_code[0].upper()
    suit = card_code[1].upper()
    # APIの仕様上、10は'0'で表される
    if rank == 'T':
        rank = '0'
    return f"https://deckofcardsapi.com/static/img/{rank}{suit}.png"

# カード設定
st.sidebar.header("🎴 カード設定")

ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
suits = ['s', 'h', 'd', 'c']
all_cards = [r+s for r in ranks for s in suits]

st.sidebar.subheader("あなたの手札（2枚）")
hero_card_1 = st.sidebar.selectbox("1枚目", all_cards, index=all_cards.index('As'), format_func=format_card)
hero_card_2 = st.sidebar.selectbox("2枚目", all_cards, index=all_cards.index('Ks'), format_func=format_card)

st.sidebar.markdown("---")
st.sidebar.subheader("場の共通カード（ボード）")
st.sidebar.markdown("開かれたカードを選んでください（最大5枚）")

board_cards = st.sidebar.multiselect("共通カードを選択", all_cards, format_func=format_card, max_selections=5)

st.sidebar.markdown("---")
num_villains = st.sidebar.slider("対戦相手の人数", min_value=1, max_value=8, value=1)

# Main area
hero_cards = [hero_card_1, hero_card_2]

# Duplicate check
selected_all = hero_cards + board_cards
if len(selected_all) != len(set(selected_all)):
    st.error("⚠️ エラー：同じカードが複数選択されています。別のカードを選んでください。")
    st.stop()

# --- ビジュアル表示エリア ---
st.markdown("### 🃏 現在のカード")
col_hero, col_board = st.columns([1, 2])

with col_hero:
    st.markdown("**あなたの手札**")
    hc1, hc2, _ = st.columns([1, 1, 1]) # 見栄えを調整
    with hc1:
        st.image(get_card_image_url(hero_card_1), use_container_width=True)
    with hc2:
        st.image(get_card_image_url(hero_card_2), use_container_width=True)

with col_board:
    st.markdown("**場の共通カード**")
    if board_cards:
        # 最大5枚分のカラムを作成
        b_cols = st.columns(5)
        for i, card in enumerate(board_cards):
            with b_cols[i]:
                st.image(get_card_image_url(card), use_container_width=True)
    else:
        st.info("まだ場のカードは開かれていません。")

st.markdown("---")

# Equity calculation
with st.spinner('勝率を計算中...'):
    win_rate, tie_rate = calculate_equity(hero_cards, board_cards, num_villains)

# 初心者向けのアドバイス表示
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
