from fetcher_and_parser import *

import random


def find_next_opponent_k(subset_games_df, forbidden_players, type_filter, game_count_filter, game_counts_dir, monthly_archive_dir):
    """
    first filter against all opponents using the criteria, then randomly select a remaining player not in the forbidden list
    :param monthly_archive_dir:
    :param game_counts_dir:
    :param game_count_filter: {game type: minimum count}
    :param forbidden_players: players not to be selected as output
    :param subset_games_df: a fraction of all the games from this player
    :param type_filter: [game type]
    :return: player name
    """
    filtered_df = subset_games_df[subset_games_df['timeClass'].isin(type_filter)]
    players = filtered_df['opponentName'].unique().tolist()
    if not players:
        return "NO PLAYER FOUND"
    tries = 0
    while True:
        tries += 1
        if tries == 20:
            return "NO PLAYER FOUND"
        selected_player = random.choice(players)
        if selected_player in forbidden_players:
            forbidden_players.add(selected_player)
            continue
        parsed_selected_player_game_count_data = get_intermediate_data(game_counts_dir, selected_player, user_game_counts_url, parse_game_counts_data)
        counts_passed = True
        for game_type, min_count in game_count_filter.items():
            if game_type not in parsed_selected_player_game_count_data or parsed_selected_player_game_count_data[game_type]['gameCounts'] < min_count:
                counts_passed = False
                break
        if not counts_passed:
            continue
        parsed_monthly_archive_data = get_intermediate_data(monthly_archive_dir, selected_player, user_monthly_archive_url, parse_monthly_archive_data)
        if parsed_monthly_archive_data['monthsPlayed'] < 2:
            # this is needed for more efficient downstream k-extension
            forbidden_players.add(selected_player)
            continue
        break
    return selected_player


def find_next_opponent_d(games_df, forbidden_players, type_filter, game_count_filter, active_month_filter, csv_dir, already_selected_players,
                         player_category_dir, game_counts_dir, monthly_archive_dir):
    filtered_df = games_df[games_df['timeClass'].isin(type_filter)]
    players = filtered_df['opponentName'].unique().tolist()
    if not players:
        return "NO PLAYER FOUND"
    tries = 0
    while True:
        tries += 1
        if tries == 20:
            return "NO PLAYER FOUND"
        selected_player = random.choice(players)
        if selected_player in forbidden_players:
            forbidden_players.add(selected_player)
            continue
        ## filter: this player is not a streamer
        parsed_category_data = get_intermediate_data(player_category_dir, selected_player, user_category_url, parse_category_data)
        if parsed_category_data['isStreamer']:
            forbidden_players.add(selected_player)
            continue
        ## filter: this player has enough active months
        parsed_monthly_archive_data = get_intermediate_data(monthly_archive_dir, selected_player, user_monthly_archive_url, parse_monthly_archive_data)
        if parsed_monthly_archive_data['monthsPlayed'] < active_month_filter:
            forbidden_players.add(selected_player)
            continue
        ## filter: this player played enough games
        parsed_selected_player_game_count_data = get_intermediate_data(game_counts_dir, selected_player, user_game_counts_url, parse_game_counts_data)
        counts_passed = True
        for game_type, min_count in game_count_filter.items():
            if parsed_selected_player_game_count_data[game_type]['gameCounts'] < min_count:
                counts_passed = False
        if not counts_passed:
            continue
        ## filter: this player is not a neighbor of previously selected players
        selected_player_games_df = get_all_games(csv_dir, selected_player, monthly_archive_dir)
        if not player_not_in_immediate_neighborhood(selected_player_games_df, already_selected_players):
            continue
        break
    return selected_player


def player_not_in_immediate_neighborhood(games_df, current_players):
    """
    check if the df's player is within the d=1 immediate neighborhood with any other current players
    :param games_df:
    :param current_players: dict of players already selected {playerName: randomizerWeight}
    :return:
    """
    current_player_names = list(current_players.keys())
    players_in_neighborhood = games_df['opponentName'].tolist()
    intersection = set(players_in_neighborhood).intersection(current_player_names)
    if intersection:
        return False
    return True


def add_newly_selected_player(selected_players, new_player_name, increment_factor):
    for key, val in selected_players.items():
        selected_players[key] *= increment_factor
    selected_players[new_player_name] = 1.0



