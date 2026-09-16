from treys import Card, Evaluator, Deck
import random

evaluator = Evaluator()

def calculate_equity(hero_cards_str, board_cards_str, num_villains=1, iterations=1000):
    try:
        # 文字列表現がeval7は 'As', treysは 'As' なのでそのまま使える
        hero_cards = [Card.new(c) for c in hero_cards_str]
        board_cards = [Card.new(c) for c in board_cards_str] if board_cards_str else []
        
        if len(hero_cards) != 2:
            return 0.0, 0.0
            
        hero_wins = 0
        ties = 0
        
        for _ in range(iterations):
            deck = Deck()
            # 既知のカードを取り除くために、手札とボードのカードはdeckから引いたことにする
            deck.cards = [c for c in deck.cards if c not in hero_cards and c not in board_cards]
            
            # ボードに必要なカードを引く
            cards_to_draw = 5 - len(board_cards)
            drawn_board = deck.draw(cards_to_draw)
            if type(drawn_board) != list:
                drawn_board = [drawn_board] if drawn_board else []
                
            full_board = board_cards + drawn_board
            
            # 相手の手札を引く
            villains_cards = []
            for i in range(num_villains):
                v_cards = deck.draw(2)
                if type(v_cards) != list:
                    v_cards = [v_cards] # just in case
                villains_cards.append(v_cards)
                
            # treysはスコアが低い方が強い
            hero_score = evaluator.evaluate(full_board, hero_cards)
            
            villains_scores = [evaluator.evaluate(full_board, v) for v in villains_cards]
            best_villain_score = min(villains_scores)
            
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
