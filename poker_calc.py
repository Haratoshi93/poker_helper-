from treys import Card, Evaluator, Deck
import random
import os
import json

evaluator = Evaluator()

PREFLOP_TABLE = None

def get_normalized_hand(hero_cards_str):
    ranks_order = 'AKQJT98765432'
    r1, s1 = hero_cards_str[0][0].upper(), hero_cards_str[0][1].lower()
    r2, s2 = hero_cards_str[1][0].upper(), hero_cards_str[1][1].lower()
    
    if r1 == '0': r1 = 'T'
    if r2 == '0': r2 = 'T'
    
    idx1 = ranks_order.index(r1)
    idx2 = ranks_order.index(r2)
    
    if idx1 > idx2:
        r1, r2 = r2, r1
        s1, s2 = s2, s1
        
    if r1 == r2:
        return f"{r1}{r2}"
    elif s1 == s2:
        return f"{r1}{r2}s"
    else:
        return f"{r1}{r2}o"

def calculate_equity(hero_cards_str, board_cards_str, num_villains=1, iterations=1000):
    global PREFLOP_TABLE
    try:
        # プリフロップなら事前計算データを優先使用する
        if len(hero_cards_str) == 2 and not board_cards_str:
            if PREFLOP_TABLE is None:
                # ブラウザ（stlite）環境ではカレントディレクトリ、それ以外はスクリプトディレクトリ
                table_path = "preflop_table.json"
                if not os.path.exists(table_path):
                    table_path = os.path.join(os.path.dirname(__file__), "preflop_table.json")
                
                if os.path.exists(table_path):
                    with open(table_path, "r") as f:
                        PREFLOP_TABLE = json.load(f)
                else:
                    PREFLOP_TABLE = {}
                    
            hand_key = get_normalized_hand(hero_cards_str)
            v_key = str(num_villains)
            if hand_key in PREFLOP_TABLE and v_key in PREFLOP_TABLE[hand_key]:
                data = PREFLOP_TABLE[hand_key][v_key]
                return data["win"], data["tie"]

        hero_cards = [Card.new(c) for c in hero_cards_str]
        board_cards = [Card.new(c) for c in board_cards_str] if board_cards_str else []
        
        if len(hero_cards) != 2:
            return 0.0, 0.0
            
        hero_wins = 0
        ties = 0
        
        # --- ループ外での事前準備（高速化の鍵） ---
        full_deck = Deck().GetFullDeck() # 全カードのリストを取得
        known_cards = set(hero_cards + board_cards)
        # 既知のカードを取り除いた「山札」をリストとして用意
        remaining_cards = [c for c in full_deck if c not in known_cards]
        
        cards_to_draw_for_board = 5 - len(board_cards)
        cards_to_draw_for_villains = num_villains * 2
        total_cards_to_draw = cards_to_draw_for_board + cards_to_draw_for_villains
        
        for _ in range(iterations):
            # random.sample を使って必要なカードを一度にすべて引く（圧倒的に高速）
            drawn_cards = random.sample(remaining_cards, total_cards_to_draw)
            
            # 引いたカードをボードと敵の手札に分配
            drawn_board = drawn_cards[:cards_to_draw_for_board]
            full_board = board_cards + drawn_board
            
            villains_flat = drawn_cards[cards_to_draw_for_board:]
            
            # スコア判定 (treysはスコアが低い方が強い)
            hero_score = evaluator.evaluate(full_board, hero_cards)
            
            # 最強の敵のスコアを探す
            best_villain_score = 99999
            for i in range(num_villains):
                v_cards = [villains_flat[i*2], villains_flat[i*2 + 1]]
                score = evaluator.evaluate(full_board, v_cards)
                if score < best_villain_score:
                    best_villain_score = score
            
            if hero_score < best_villain_score:
                hero_wins += 1
            elif hero_score == best_villain_score:
                ties += 1

        win_rate = hero_wins / iterations
        tie_rate = ties / iterations
        
        return win_rate, tie_rate
        
    except Exception as e:
        print(f"Error in equity calc: {e}")
        return 0.0, 0.0

def get_hand_type(hero_cards_str, board_cards_str):
    try:
        hero_cards = [Card.new(c) for c in hero_cards_str]
        board_cards = [Card.new(c) for c in board_cards_str] if board_cards_str else []
        
        if len(board_cards) >= 3:
            score = evaluator.evaluate(board_cards, hero_cards)
            rank_class = evaluator.get_rank_class(score)
            return evaluator.class_to_string(rank_class)
        return "High Card"
    except Exception as e:
        return "Unknown"
