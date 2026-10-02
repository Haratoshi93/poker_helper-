import json
import time
from poker_calc import calculate_equity

ranks = 'AKQJT98765432'

def get_representative_cards(hand_type):
    # hand_type: "AA", "AKs", "AKo" etc.
    if len(hand_type) == 2:
        # Pair
        return [f"{hand_type[0]}s", f"{hand_type[0]}h"]
    elif hand_type[2] == 's':
        # Suited
        return [f"{hand_type[0]}s", f"{hand_type[1]}s"]
    else:
        # Offsuit
        return [f"{hand_type[0]}s", f"{hand_type[1]}h"]

def generate_table():
    hand_types = []
    for i, r1 in enumerate(ranks):
        for j, r2 in enumerate(ranks[i:]):
            if r1 == r2:
                hand_types.append(f"{r1}{r2}")
            else:
                hand_types.append(f"{r1}{r2}s")
                hand_types.append(f"{r1}{r2}o")
                
    table = {}
    total = len(hand_types) * 8
    count = 0
    
    start_time = time.time()
    for hand_type in hand_types:
        hero_cards = get_representative_cards(hand_type)
        table[hand_type] = {}
        for v in range(1, 9):
            # 2000回で十分に高い精度が出るため時間を短縮
            win, tie = calculate_equity(hero_cards, [], num_villains=v, iterations=2000)
            table[hand_type][str(v)] = {"win": win, "tie": tie}
            count += 1
            if count % 100 == 0:
                print(f"Progress: {count}/{total} ({(count/total)*100:.1f}%)", flush=True)
                
    print(f"Done in {time.time() - start_time:.1f}s")
    
    with open("preflop_table.json", "w") as f:
        json.dump(table, f, indent=2)

if __name__ == "__main__":
    generate_table()
