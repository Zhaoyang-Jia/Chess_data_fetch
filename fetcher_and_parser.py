import os
import subprocess
import json
import time
import re
import pandas as pd
import random
import ast


############################## URLs ###################################

def user_game_counts_url(username):
    return f"https://www.chess.com/callback/member/stats/{username.lower()}"


def user_category_url(username):
    return f"https://www.chess.com/callback/user/popup/{username.lower()}"


def user_monthly_archive_url(username):
    return f"https://api.chess.com/pub/player/{username.lower()}/games/archives"


############################## Fetchers ###################################

class RequestFailedException(Exception):
    pass


def fetch(url):
    """
    given a fetch freezes, will retry after a small delay until fetched successfully
    :param url:
    :return:
    """

    def fetch_data():
        # try to mimic user-agent header for API bypass
        # user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
        curl_command = f'curl -v {url}'
        print(curl_command)
        result = subprocess.run(curl_command, capture_output=True, text=True, shell=True)
        if result.returncode != 0:
            raise RequestFailedException(f"Fetch Error ({url}): {result.stderr}")
        json_output = json.loads(result.stdout)
        if 'message' in json_output and json_output['message'].startswith('Invalid values'):
            raise RequestFailedException(f"Fetch Error-invalid values ({url}): {json_output},  command: {' '.join(curl_command)}")
        return json_output

    retries = 0
    while True:
        try:
            data = fetch_data()
            break  # Exit the loop if request is successful
        except Exception as e:
            if retries == 0:
                print("##########################SSSSSS###########################")  # mark issue started
            print(f"retries: {retries}; code: {e}")
        retries += 1
        time.sleep(random.uniform(0.5, 1.5))  # a random interval in-between each retry
    if retries != 0:
        print("##########################TTTTTT###########################")  # mark issue resolved
    return data


def fetch_monthly_archives(parsed_monthly_archive_data, n_months=-1):
    """
    fetch all/subset of monthly archives
    :param parsed_monthly_archive_data:
    :param n_months: -1 for all months, other int = number of months to be taken
    :return:
    """
    urls = parsed_monthly_archive_data['archiveUrls']
    if n_months != -1:
        urls = random.sample(urls, n_months)
    return {url.split('games/')[-1]: fetch(url) for url in urls}


############################## Parsers/Filters ###################################

def parse_category_data(category_data):
    return {'isStreamer': category_data['isStreamer']}


def parse_monthly_archive_data(monthly_archive_data):
    archive_urls = monthly_archive_data['archives']
    return {'monthsPlayed': len(archive_urls),
            'archiveUrls': archive_urls}


def parse_game_counts_data(game_counts_data):
    allowed_types = ['rapid', 'bullet', 'blitz', 'daily']
    output = {}
    for info in game_counts_data['stats']:
        game_type = info['key']
        if game_type not in allowed_types:
            continue
        game_counts = info['gameCount']
        other_info = info['stats']
        current_rating = other_info['rating']
        highest_rating = other_info['highest_rating']
        avg_opponent_rating = other_info['avg_opponent_rating']
        output[game_type] = {'gameCounts': game_counts,
                             'currentRating': current_rating,
                             'highestRating': highest_rating,
                             'avgOpponentRating': avg_opponent_rating}
    return output


def parse_games(all_games_data, player_name):
    """
    :param all_games_data: output of `fetch_monthly_archives`
    :param player_name: name of the protagonist, used for identifying side and opponent
    :return: df of all games
    """
    output = []
    for month, info in all_games_data.items():
        games = info['games']
        for game in games:
            if game['time_class'] not in ['rapid', 'blitz', 'bullet', 'daily']:
                continue
            ## find which side the player is on
            if game['white']['username'].lower() == player_name.lower():
                player_side = 'white'
                opponent_side = 'black'
            else:
                player_side = 'black'
                opponent_side = 'white'
            ## parsing other status
            player_data = game[player_side]
            opponent_data = game[opponent_side]
            if player_data['result'] == 'win':
                win = True
                end_method = opponent_data['result']
            else:
                win = False
                end_method = player_data['result']
            player_rating = player_data['rating']
            opponent_rating = opponent_data['rating']
            opponent_name = opponent_data['username']
            date_pattern = r'\[Date \"(\d+)\.(\d+)\.(\d+)\"\]'
            if 'pgn' not in game:
                year, month, day = -1, -1, -1
            else:
                re_match = re.search(date_pattern, game['pgn'])
                if re_match is None:
                    year, month, day = -1, -1, -1
                else:
                    year, month, day = re_match.groups()
            opening = game['eco'].split('openings/')[-1].replace("\"", '')
            output.append({'year': int(year),
                           'month': int(month),
                           'day': int(day),
                           'rated': game['rated'],
                           'timeClass': game['time_class'],
                           'playerSide': player_side,
                           'win': win,
                           'endMethod': end_method,
                           'opening': opening,
                           'playerRating': player_rating,
                           'opponentRating': opponent_rating,
                           'opponentName': opponent_name})
    column_orders = ['year', 'month', 'day', 'rated', 'timeClass', 'playerSide', 'win', 'endMethod', 'opening', 'playerRating', 'opponentRating',
                     'opponentName']
    df = pd.DataFrame(output, columns=column_orders)
    return df


def player_metadata(parsed_monthly_archieve_data, parsed_game_counts_data):
    return {}


############################## I/O ###################################

def get_all_games(games_csv_dir, player_id, monthly_archive_dir):
    ## use stored data if there is one
    games_csvs = [file.split('.')[0] for file in os.listdir(games_csv_dir)]
    for csv in games_csvs:
        if player_id.lower() == csv.lower():
            return pd.read_csv(f"{games_csv_dir}/{csv}.csv")

    ## fetch data otherwise
    parsed_monthly_archive_data = get_intermediate_data(monthly_archive_dir, player_id, user_monthly_archive_url, parse_monthly_archive_data)
    all_games_df = parse_games(fetch_monthly_archives(parsed_monthly_archive_data), player_id)

    ## store data for future use
    all_games_df.to_csv(f"{games_csv_dir}/{player_id}.csv", index=False)
    return all_games_df


def get_subset_games(games_csv_dir, player_id, monthly_archive_dir, n_months=2):
    ## use stored fullset games_df if there is one
    games_csvs = [file.split('.')[0] for file in os.listdir(games_csv_dir)]
    for csv in games_csvs:
        if player_id.lower() == csv.lower():
            return pd.read_csv(f"{games_csv_dir}/{csv}.csv")

    ## fetch and store subset data otherwise
    parsed_monthly_archive_data = get_intermediate_data(monthly_archive_dir, player_id, user_monthly_archive_url, parse_monthly_archive_data)
    subset_games_df = parse_games(fetch_monthly_archives(parsed_monthly_archive_data, n_months=n_months), player_id)

    return subset_games_df


def get_intermediate_data(parsed_game_counts_data_dir, player_id, url_func, parser_func):
    ## use stored data
    csvs = [file.split('.')[0] for file in os.listdir(parsed_game_counts_data_dir)]
    for csv in csvs:
        if player_id.lower() == csv.lower():
            with open(f"{parsed_game_counts_data_dir}/{csv}.csv") as fp_read:
                data = fp_read.readline()
            return ast.literal_eval(data)

    ## fetch and store data otherwise
    parsed_data = parser_func(fetch(url_func(player_id)))
    with open(f"{parsed_game_counts_data_dir}/{player_id}.csv", 'w') as fp_write:
        fp_write.write(str(parsed_data))
    return parsed_data


def initialize_metadata(filepath):
    with open(filepath, 'w') as fp_write:
        fp_write.write('playerID,monthsActive,rapidCounts,bulletCounts,blitzCounts,dailyCounts,rapidELO,bulletELO,blitzELO,dailyELO\n')


def append_metadata(filepath, parsed_game_count_data, parsed_monthly_archive_data, player_id):
    rapidCounts, bulletCounts, blitzCounts, dailyCounts, rapidELO, bulletELO, blitzELO, dailyELO = 0, 0, 0, 0, -1, -1, -1, -1
    if 'rapid' in parsed_game_count_data:
        rapidCounts = parsed_game_count_data['rapid']['gameCounts']
        rapidELO = parsed_game_count_data['rapid']['currentRating']
    if 'bullet' in parsed_game_count_data:
        bulletCounts = parsed_game_count_data['bullet']['gameCounts']
        bulletELO = parsed_game_count_data['bullet']['currentRating']
    if 'blitz' in parsed_game_count_data:
        blitzCounts = parsed_game_count_data['blitz']['gameCounts']
        blitzELO = parsed_game_count_data['blitz']['currentRating']
    if 'daily' in parsed_game_count_data:
        dailyCounts = parsed_game_count_data['daily']['gameCounts']
        dailyELO = parsed_game_count_data['daily']['currentRating']
    with open(filepath, 'a') as fp_write:
        fp_write.write(f"{player_id},"
                       f"{parsed_monthly_archive_data['monthsPlayed']},"
                       f"{rapidCounts},"
                       f"{bulletCounts},"
                       f"{blitzCounts},"
                       f"{dailyCounts},"
                       f"{rapidELO},"
                       f"{bulletELO},"
                       f"{blitzELO},"
                       f"{dailyELO}"
                       f"\n")

## runtime benchmark
# start_time = time.time()
# x = parse_monthly_archieve_data(fetch(user_monthly_archive_url('jimmyjia')))
# y = fetch_monthly_archives(x)
# end_time1 = time.time()
# print(f"Total time taken for API calls: {end_time1 - start_time:.2f} seconds")
# games = parse_games(y, 'jimmyjia')
# end_time2 = time.time()
# print(f"Total time taken for parsing: {end_time2 - end_time1:.2f} seconds")
# store_data(y, 'test_output/games.txt')
# end_time3 = time.time()
# print(f"Total time taken for storage: {end_time3 - end_time2:.2f} seconds")

# x = fetch(user_game_counts_url('jimmyjia'))
