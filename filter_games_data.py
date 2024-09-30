import os
import pandas as pd


METADATA_DIR = 'data/players_metadata.csv'
GAMES_DIR = 'data/games_csv/'


metadata = pd.read_csv(METADATA_DIR)
selected_players = [p.lower() for p in metadata['playerID'].tolist()]

for game_file in os.listdir(GAMES_DIR):
    file_player = game_file.split('.')[0]
    if file_player.lower() not in selected_players:
        os.remove(f"{GAMES_DIR}/{game_file}")
        print(f"removed {game_file}")
