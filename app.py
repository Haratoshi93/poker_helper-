import streamlit as st
import pandas as pd
import plotly.express as px
from poker_calc import calculate_equity, get_hand_type

st.set_page_config(page_title="Poker Helper", layout="wide")

st.title("ポーカー 勝率可視化アプリ")
st.markdown("自分の手札と場のカードを設定して、勝率がどう変化するか確認しましょう。")

# Sidebar
st.sidebar.header("カード設定")

ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
suits = ['s', 'h', 'd', 'c']
all_cards = [r+s for r in ranks for s in suits]

hero_card_1 = st.sidebar.selectbox("手札1枚目", all_cards, index=all_cards.index('As'))
hero_card_2 = st.sidebar.selectbox("手札2枚目", all_cards, index=all_cards.index('Ks'))

st.sidebar.markdown("---")
st.sidebar.subheader("ボード（共通カード）")
st.sidebar.markdown("フロップ(3枚)→ターン(4枚)→リバー(5枚)の順で設定してください")

board_cards = st.sidebar.multiselect("ボードカードを選択", all_cards, max_selections=5)

st.sidebar.markdown("---")
num_villains = st.sidebar.slider("対戦相手の人数", min_value=1, max_value=8, value=1)

# Main area
hero_cards = [hero_card_1, hero_card_2]

# Duplicate check
selected_all = hero_cards + board_cards
if len(selected_all) != len(set(selected_all)):
    st.error("エラー：同じカードが複数選択されています。別のカードを選んでください。")
    st.stop()

# Equity calculation
with st.spinner('勝率を計算中...'):
    win_rate, tie_rate = calculate_equity(hero_cards, board_cards, num_villains)

col1, col2, col3 = st.columns(3)
col1.metric("現在の勝率", f"{win_rate*100:.1f}%")
col2.metric("引き分け率", f"{tie_rate*100:.1f}%")
if len(board_cards) >= 3:
    hand_type = get_hand_type(hero_cards, board_cards)
    col3.metric("現在の役", hand_type)
else:
    col3.metric("現在の役", "プリフロップ")

st.markdown("---")
st.subheader("勝率の推移")
st.markdown("これまでのカードの開き具合による、勝率の変化グラフです。")

phases = ["プリフロップ (0枚)", "フロップ (3枚)", "ターン (4枚)", "リバー (5枚)"]
equity_history = []

for i in [0, 3, 4, 5]:
    if len(board_cards) >= i:
        current_board = board_cards[:i]
        # Calculate equity for historical phases
        wr, _ = calculate_equity(hero_cards, current_board, num_villains, iterations=2000)
        equity_history.append({"フェーズ": phases[[0, 3, 4, 5].index(i)], "勝率": wr * 100})

if equity_history:
    df = pd.DataFrame(equity_history)
    fig = px.line(df, x="フェーズ", y="勝率", markers=True, title="ゲーム進行に伴う勝率の変化", range_y=[0, 100])
    st.plotly_chart(fig)
