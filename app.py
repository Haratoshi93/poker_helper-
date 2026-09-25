import streamlit as st
import pandas as pd
import plotly.express as px
from poker_calc import calculate_equity, get_hand_type

st.set_page_config(page_title="Texas Hold'em Analyzer", layout="centered", initial_sidebar_state="collapsed")

# ゴージャスかつスマホ（モバイル）に最適化されたカスタムCSS
st.markdown("""
<style>
    /* Streamlit Cloud特有のロゴ、ヘッダー、フッターを完全に非表示 */
    header[data-testid="stHeader"] {display: none !important;}
    footer {visibility: hidden !important;}
    .stApp > header {display: none !important;}
    [data-testid="stHeader"] {display: none !important;}
    [data-testid="stToolbar"] {display: none !important;}
    div[data-testid="viewerBadge"] {display: none !important;}
    .viewerBadge_container__1QSob {display: none !important;}
    a[href*="streamlit"] {display: none !important;}
    #MainMenu {visibility: hidden !important;}
    
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
    
    /* 数字選択のピル（st.pills）のスタイルを復元・調整 */
    [data-testid="stPill"] {
        padding: 0.5rem 0.8rem !important;
    }
    [data-testid="stPill"] span {
        font-size: 1.3rem !important;
        font-weight: bold !important;
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
def format_card_full(c): return f"{suit_icon[c[1]]} {rank_map_display.get(c[0], c[0])}"

def get_card_image_url(card_code):
    rank = card_code[0].upper()
    suit = card_code[1].upper()
    if rank == 'T': rank = '0'
    return f"https://deckofcardsapi.com/static/img/{rank}{suit}.png"

# --- リセット処理 ---
def reset_cards():
    for key in list(st.session_state.keys()):
        if key.startswith("s_") or key.startswith("h_") or key.startswith("f_") or key.startswith("t_") or key.startswith("r_") or key.startswith("pill_"):
            del st.session_state[key]
    used_cards.clear()

used_cards = set()

# マークは巨大ボタン、数字はコンパクトなpills
def card_picker(label, prefix):
    suit_key = f"s_{prefix}_suit"
    final_key = f"s_{prefix}_final"
    edit_key = f"s_{prefix}_edit"
    
    current_card = st.session_state.get(final_key)
    # カードが選ばれていないか、編集モードになっている場合に True
    is_editing = st.session_state.get(edit_key, current_card is None)
    
    if current_card and not is_editing:
        # 選ばれた後の「たたまれた」状態
        with st.container(border=True):
            ec1, ec2 = st.columns([3, 1])
            ec1.markdown(f"**{label}** : {format_card_full(current_card)}")
            if ec2.button("変更", key=f"btn_edit_{prefix}", use_container_width=True):
                st.session_state[edit_key] = True
                st.rerun()
        used_cards.add(current_card)
        return current_card
        
    else:
        # 編集（選択）モード
        st.markdown(f"**{label}**")
        suit = st.session_state.get(suit_key)
        
        # マークボタン
        cols = st.columns(4)
        for i, s in enumerate(suits):
            btn_type = "primary" if suit == s else "secondary"
            if cols[i].button(format_suit(s), key=f"btn_{prefix}_suit_{s}", use_container_width=True, type=btn_type):
                st.session_state[suit_key] = s
                if f"pill_{prefix}_rank" in st.session_state:
                    del st.session_state[f"pill_{prefix}_rank"]
                st.rerun()
                
        # 数字ボタン
        if suit:
            # 自分のカードは選択肢から除外しない
            avail_ranks = [r for r in ranks if (f"{r}{suit}" not in used_cards) or (current_card and f"{r}{suit}" == current_card)]
            rank = st.radio(f"rank_{prefix}", avail_ranks, format_func=format_rank, key=f"pill_{prefix}_rank", label_visibility="collapsed", horizontal=True, index=None)
            if rank:
                card_code = f"{rank}{suit}"
                st.session_state[final_key] = card_code
                st.session_state[edit_key] = False # 選んだらたたむ
                used_cards.add(card_code)
                st.rerun()
                
        # 既に選んだカードがある場合はキャンセル（閉じる）ボタンを表示
        if current_card:
            if st.button("キャンセル", key=f"btn_cancel_{prefix}", use_container_width=True):
                st.session_state[edit_key] = False
                st.rerun()
                
        if current_card:
            used_cards.add(current_card)
        return current_card

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
        
        # HTML/CSSでスマホでも強制的に横並びにする
        img1_url = get_card_image_url(hero_cards[0])
        img2_url = get_card_image_url(hero_cards[1])
        html_code = f"""
        <div style="display: flex; justify-content: center; gap: 15px; margin-bottom: 20px;">
            <img src="{img1_url}" style="width: 40%; max-width: 120px; border-radius: 6px;">
            <img src="{img2_url}" style="width: 40%; max-width: 120px; border-radius: 6px;">
        </div>
        """
        st.markdown(html_code, unsafe_allow_html=True)
        
        st.metric("WIN % (勝率)", f"{win_rate*100:.1f}%")

    st.button("RESET CARDS", on_click=reset_cards, use_container_width=True, type="primary")

    # --- 4. オプション機能（フロップ以降） ---
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("POSTFLOP (フロップ以降)", expanded=False):
        st.markdown("場のカード (Community Cards) を展開して解析します。")
        
        board_cards = []
        with st.container(border=True):
            f1 = card_picker("Flop 1", "f1")
            if f1:
                board_cards.append(f1)
                f2 = card_picker("Flop 2", "f2")
                if f2:
                    board_cards.append(f2)
                    f3 = card_picker("Flop 3", "f3")
                    if f3:
                        board_cards.append(f3)
                        t = card_picker("Turn (4th)", "t")
                        if t:
                            board_cards.append(t)
                            r = card_picker("River (5th)", "r")
                            if r:
                                board_cards.append(r)
                                
            # 盤面のカードをHTMLで強制横並び表示
            if board_cards:
                st.markdown("**COMMUNITY CARDS**")
                imgs_html = "".join([f'<img src="{get_card_image_url(c)}" style="width: 18%; max-width: 80px; margin: 1%; border-radius: 4px;">' for c in board_cards])
                st.markdown(f'<div style="display: flex; justify-content: center; flex-wrap: wrap; margin-bottom: 10px;">{imgs_html}</div>', unsafe_allow_html=True)
        
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
