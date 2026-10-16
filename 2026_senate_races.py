import json
import time
import urllib.request
from datetime import datetime

DEM_SYMBOL = " DEM "
REP_SYMBOL = " REP "

#
#    State              Kalshi Ticker           Current Incumbent
#
CONTRACTS = [
    ("Alabama",         "SENATEAL-26-D",        REP_SYMBOL),
    ("Alaska",          "SENATEAK-26-D",        REP_SYMBOL),
    ("Arkansas",        "SENATEAR-26-D",        REP_SYMBOL),
    ("Colorado",        "SENATECO-26-D",        DEM_SYMBOL),
    ("Deleware",        "SENATEDE-26-D",        DEM_SYMBOL),
    ("Florida",         "SENATEFLS-26-D",       REP_SYMBOL),
    ("Georgia",         "SENATEGA-26-D",        DEM_SYMBOL),
    ("Idaho",           "SENATEID-26-D",        REP_SYMBOL),
    ("Illinois",        "SENATEIL-26-D",        DEM_SYMBOL),
    ("Iowa",            "SENATEIA-26-D",        REP_SYMBOL),
    ("Kansas",          "SENATEKS-26-D",        REP_SYMBOL),
    ("Kentucky",        "SENATELA-26-D",        REP_SYMBOL),
    ("Louisiana",       "KXSENATELA-26NOV-D",   REP_SYMBOL),
    ("Maine",           "SENATEME-26-D",        REP_SYMBOL),
    ("Massachusetts",   "SENATEMA-26-D",        DEM_SYMBOL),
    ("Michigan",        "SENATEMI-26-D",        DEM_SYMBOL),
    ("Minnesota",       "SENATEMN-26-D",        DEM_SYMBOL),
    ("Mississippi",     "SENATEMS-26-D",        REP_SYMBOL),
    ("Montana",         "SENATEMT-26-IND",      REP_SYMBOL),
    ("Nebraska",        "SENATENE-26-DOSB",     REP_SYMBOL),
    ("New Hampshire",   "SENATENH-26-D",        DEM_SYMBOL),
    ("New Jersey",      "SENATENJ-26-D",        DEM_SYMBOL),
    ("New Mexico",      "SENATENM-26-D",        DEM_SYMBOL),
    ("North Carolina",  "SENATENC-26-D",        REP_SYMBOL),
    ("Ohio",            "SENATEOHS-26-D",       REP_SYMBOL),
    ("Oklahoma",        "SENATEOK-26-D",        REP_SYMBOL),
    ("Oregon",          "SENATEOR-26-D",        DEM_SYMBOL),
    ("Rhode Island",    "SENATERI-26-D",        DEM_SYMBOL),
    ("South Carolina",  "SENATESC-26-D",        REP_SYMBOL),
    ("South Dakota",    "SENATESD-26-BBEN",     REP_SYMBOL),
    ("Tennessee",       "SENATETN-26-D",        REP_SYMBOL),
    ("Texas",           "SENATETX-26-D",        REP_SYMBOL),
    ("Virginia",        "SENATEVA-26-D",        DEM_SYMBOL),
    ("West Virginia",   "SENATEWV-26-D",        REP_SYMBOL),
    ("Wyoming",         "SENATEWY-26-D",        REP_SYMBOL),
]

BASE_URL = "https://external-api.kalshi.com/trade-api/v2/markets/"

# Baseline Senate composition before contract outcomes
BASELINE_DEM = 47
BASELINE_REP = 53

# ANSI Escape Sequences for background and text styling
BG_DARK_BLUE = "\033[44m"
BG_DARK_RED = "\033[41m"
BG_DARK_GREEN = "\033[42m"
FG_WHITE = "\033[97m"
FG_BLACK = "\033[30m"
ANSI_RESET = "\033[0m"

def get_market_percentage(ticker: str) -> float:
    url = f"{BASE_URL}{ticker}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json",
    }
    
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            raw_body = response.read().decode("utf-8")
            data = json.loads(raw_body)
            market = data.get("market", {})
            
            # Kalshi provides dollar fields (e.g. "0.7400" = 74.0%)
            last_price_str = market.get("last_price_dollars")
            yes_bid_str = market.get("yes_bid_dollars")
            yes_ask_str = market.get("yes_ask_dollars")
            
            if last_price_str:
                return float(last_price_str) * 100.0
            elif yes_bid_str and yes_ask_str:
                return ((float(yes_bid_str) + float(yes_ask_str)) / 2.0) * 100.0
            elif yes_bid_str:
                return float(yes_bid_str) * 100.0
            elif yes_ask_str:
                return float(yes_ask_str) * 100.0
                
    except Exception:
        pass
        
    return 0.0

def calculate_impact(holding_party: str, dem_pct: float) -> tuple[str, int]:
    """
    Returns (Impact Label, Net Dem Seat Change)
    """
    if holding_party == REP_SYMBOL:
        if dem_pct > 50.0:
            return ("FLIP +1", 1)   # Democrat gains a seat (+1 Dem)
        else:
            return ("HOLD", 0)      # Republican retains seat
    elif holding_party == DEM_SYMBOL:
        if dem_pct < 50.0:
            return ("FLIP -1", -1)  # Republican gains a seat (-1 Dem)
        else:
            return ("HOLD", 0)      # Democrat retains seat
            
    return ("N/A", 0)

def main():
    results = []
    net_dem_change = 0
    
    for state, ticker, holding_party in CONTRACTS:
        pct = get_market_percentage(ticker)
        impact, seat_change = calculate_impact(holding_party, pct)
        net_dem_change += seat_change
        results.append((state, holding_party, pct, impact))
        time.sleep(0.1)

    # Sort results by percentage in descending order (highest % first)
    results.sort(key=lambda item: item[2], reverse=True)

    # Calculate predicted overall composition
    projected_dem = BASELINE_DEM + net_dem_change
    projected_rep = BASELINE_REP - net_dem_change

    # Apply ANSI color coding based on election outcome for Result line
    if projected_dem > projected_rep:
        result_bg = BG_DARK_BLUE
    else:
        result_bg = BG_DARK_RED

    result_str = f"Result: {projected_dem}-{projected_rep}"
    colored_result = f"{result_bg}{FG_WHITE} {result_str} {ANSI_RESET}"

    timestamp = datetime.now().strftime("%H:%M:%S")
    
    # Column width specifications for perfect table alignment:
    # State Name: 14 | Incumbent: 9 | Market %: 10 | Impact: 8
    print("+----------------+-------------+-------------+----------+")
    print("| State Name     | Incumbent   | Market %    | Impact   |")
    print("+----------------+-------------+-------------+----------+")
    
    for state, party, pct, impact in results:
        # 1. State Name Column (14 chars)
        col_state = f"{state:<14}"
        
        # 2. Incumbent Column (9 chars: "    D    " / "    R    ")
        if party == DEM_SYMBOL:
            col_incumbent = f"   {BG_DARK_BLUE}{FG_WHITE}{DEM_SYMBOL}{ANSI_RESET}   "
        elif party == REP_SYMBOL:
            col_incumbent = f"   {BG_DARK_RED}{FG_WHITE}{REP_SYMBOL}{ANSI_RESET}   "
        else:
            col_incumbent = f"    {party}    "

        # 3. Market % Column (10 chars: "   95.4%  ")
        raw_pct = f"{pct:>5.1f}%"
        if pct > 50.0:
            col_market = f"   {BG_DARK_BLUE}{FG_WHITE}{raw_pct}{ANSI_RESET}  "
        else:
            col_market = f"   {raw_pct}  "

        # 4. Impact Column (8 chars: "FLIP +1 " / "HOLD    ")
        if impact == "FLIP +1":
            col_impact = f"{BG_DARK_GREEN}{FG_BLACK}FLIP +1{ANSI_RESET} "
        elif impact == "FLIP -1":
            col_impact = f"{BG_DARK_RED}{FG_BLACK}FLIP -1{ANSI_RESET} "
        else:
            col_impact = f"{impact:<8}"
            
        print(f"| {col_state} | {col_incumbent} | {col_market} | {col_impact} |")
        
    print("+----------------+-------------+-------------+----------+")
    print(colored_result)
    print(f"Last Updated: {timestamp}")
    print("=========================================================")

if __name__ == "__main__":
    main()

