from find_players import *

import argparse


FIRST_PLAYER = 'jimmyjia'
k = 5
n = 3000
TABULATED_GAME_DIR = 'data/games_csv/'
METADATA_FILEPATH = 'data/players_metadata.csv'
GAME_COUNTS_DIR = 'data/parsed_intermediate_data/game_counts_data/'
MONTHLY_ARCHIVE_DIR = 'data/parsed_intermediate_data/monthly_archive_data/'
USER_CATEGORY_DIR = 'data/parsed_intermediate_data/user_category_data/'
GAME_TYPES = ['rapid']
MIN_GAME_COUNTS = {'rapid': 200}
MIN_MONTHS = 3
MULTIPLE_SELECTION_REDUCTION_FACTOR = 1/4
MULTIPLE_SELECTION_INCREMENT_FACTOR = 1.1

for dir_itr in [TABULATED_GAME_DIR, GAME_COUNTS_DIR, MONTHLY_ARCHIVE_DIR, USER_CATEGORY_DIR]:
    os.makedirs(dir_itr, exist_ok=True)

parser = argparse.ArgumentParser(description="Script to mine independent player data from chess.com API")
parser.add_argument('--resume', action='store_true', help="assumes the data is already populated with previous run data, and we continue running for more data")
args = parser.parse_args()
resume = args.resume

if not resume:
    print('INITIALIZED FOR BLANK DATA')
    initialize_metadata(METADATA_FILEPATH)
    first_player_parsed_game_counts_data = get_intermediate_data(GAME_COUNTS_DIR, FIRST_PLAYER, user_game_counts_url, parse_game_counts_data)
    first_player_monthly_archive_data = get_intermediate_data(MONTHLY_ARCHIVE_DIR, FIRST_PLAYER, user_monthly_archive_url, parse_monthly_archive_data)
    append_metadata(METADATA_FILEPATH, first_player_parsed_game_counts_data, first_player_monthly_archive_data, FIRST_PLAYER)

    selected_players = {FIRST_PLAYER: 1.0}  # {playerName: extensionWeight}
    forbidden_players = {FIRST_PLAYER}
else:
    # take the players from metadata as all the selected players, and re-assign weight to be 1.0
    print('RESUMING FROM PREVIOUS DATA')
    metadata_df = pd.read_csv(METADATA_FILEPATH)
    ps = metadata_df['playerID'].tolist()
    print(f'inherited {ps}')
    selected_players = {p: 1.0 for p in ps}
    forbidden_players = set(ps)

i = 0
while i < n:
    print(f"i={i}, {selected_players}")
    current_player = random.choices(list(selected_players.keys()), weights=list(selected_players.values()), k=1)[0]
    print(f"root player selected: {current_player}")
    selected_players[current_player] *= MULTIPLE_SELECTION_REDUCTION_FACTOR
    current_player_games_df = get_all_games(TABULATED_GAME_DIR, current_player, MONTHLY_ARCHIVE_DIR)
    next_player_games_df = current_player_games_df

    print('k-search')
    redo_outer_loop = False
    for k_i in range(k-1):
        next_player_name = find_next_opponent_k(next_player_games_df, forbidden_players, GAME_TYPES, MIN_GAME_COUNTS, GAME_COUNTS_DIR, MONTHLY_ARCHIVE_DIR)
        if next_player_name == 'NO PLAYER FOUND':
            redo_outer_loop = True
            break
        next_player_games_df = get_subset_games(TABULATED_GAME_DIR, next_player_name, MONTHLY_ARCHIVE_DIR)
        # if k_i == k-2:
        #     ## last player reached, populate the whole games_df
        #     next_player_games_df = get_all_games(TABULATED_GAME_DIR, next_player_name, MONTHLY_ARCHIVE_DIR)
        # else:
        #     ## only populate a subset games_df
        #     next_player_games_df = get_subset_games(TABULATED_GAME_DIR, next_player_name, MONTHLY_ARCHIVE_DIR)
    if redo_outer_loop:
        continue

    print('d-search')
    next_player_name = find_next_opponent_d(next_player_games_df, forbidden_players, GAME_TYPES, MIN_GAME_COUNTS, MIN_MONTHS, TABULATED_GAME_DIR, selected_players,
                                            USER_CATEGORY_DIR, GAME_COUNTS_DIR, MONTHLY_ARCHIVE_DIR)
    if next_player_name == 'NO PLAYER FOUND':
        print('restarted: NO PLAYER FOUND')
        continue
    add_newly_selected_player(selected_players, next_player_name, MULTIPLE_SELECTION_INCREMENT_FACTOR)
    forbidden_players.add(next_player_name)
    # only players who have been checked and selected are input into metadata
    next_player_parsed_game_counts_data = get_intermediate_data(GAME_COUNTS_DIR, next_player_name, user_game_counts_url, parse_game_counts_data)
    next_player_monthly_archive_data = get_intermediate_data(MONTHLY_ARCHIVE_DIR, next_player_name, user_monthly_archive_url, parse_monthly_archive_data)
    append_metadata(METADATA_FILEPATH, next_player_parsed_game_counts_data, next_player_monthly_archive_data, next_player_name)
    i += 1
