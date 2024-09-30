import requests, json
from find_players import *


# # r = requests.get("https://api.chess.com/pub/player/jimmyjia/games/archives")
# r = requests.get("https://api.chess.com/pub/player/jimmyjia.jsonld")
# month_urls = r.json()


## debug pgn issue
TABULATED_GAME_DIR = 'data/games_csv/'
METADATA_FILEPATH = 'data/players_metadata.csv'
GAME_COUNTS_DIR = 'data/parsed_intermediate_data/game_counts_data/'
MONTHLY_ARCHIVE_DIR = 'data/parsed_intermediate_data/monthly_archive_data/'
USER_CATEGORY_DIR = 'data/parsed_intermediate_data/user_category_data/'
# for dir_itr in [TABULATED_GAME_DIR, GAME_COUNTS_DIR, MONTHLY_ARCHIVE_DIR, USER_CATEGORY_DIR]:
#     os.makedirs(dir_itr, exist_ok=True)
# get_all_games(TABULATED_GAME_DIR, 'eric42429', MONTHLY_ARCHIVE_DIR)

## debug freezing
# x = fetch(user_game_counts_url('daveybo'))

## debug json parse
x = parsed_selected_player_game_count_data = get_intermediate_data(GAME_COUNTS_DIR, 'sureshkumardhanda', user_game_counts_url, parse_game_counts_data)
