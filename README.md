# Chess.com Independent Player Data Scraper

## Table of contents:
1. Introduction
2. Requirement
3. Algorithm
4. Filtering
5. Workflow


## Introduction
This software utilizes Chess.com's public API to 
collect a set of player's ID and lifetime game data. With a simple graph algorithm,
the software archives an efficient collection, while maintaining randomness and a reasonable
independence among the player set for the output set of players.

## Requirement
Needs to be run on a machine with UNIX-based shell, as the software runs `curl` as a python subprocess for API interaction

## Algorithm
The major bottleneck of the operation is in the API request. Chess.com does not allow parallel requests, and
sequential request each takes about 0.1 sec. Therefore, all approaches will need to minimize the number of API requests.

For each API request made, the parsed data is saved for future identical request, so future request will read from the 
intermediate data folder instead.

The algorithm takes input `StartPlayer` and constants `k` and `d`, alongside many filtering parameters.
The output is a list of "independent" players, alongside with each one of their full game history.

The algorithm to search for the next "independent player" is a recursive statement. 
In each iteration, a random root player is selected from the set of already selected 
players `S`. This random selection is weighted, and a player's chance increases each time they are not being selected (\*=1.1),
and the chance decreases each time they are selected (\*= 0.25). This design is chosen over the fully-linear search as
a full linear search is more likely to spiral into a certain player base.

The search for the next player is done via two subroutines `k-search` and `d-search`. 

`k-search` is a fast approach intended to quickly gain distance from the current player, for a total of `k-1` players.
In each iteration, a random active month is read, and a random player (with minimum filtering) is selected to be the next
player. Each jump takes exactly 4 API calls. 

`d-search` is a comprehensive approach intended to make sure the player selected is at least `d`-distances away from
any other players in `S`. (i.e. `d`=1 means the selected player has never played any game with anyone in `S`; `d`=2 means 
none of the player played with the selected player has played any game with anyone in `S`; and etc.) The player is first
checked via a more extensive filter. Then, all active months of the player is read-in, 
all opponents' IDs are checked against players in `S` (`d`=1) For `d` > 1,
this is repeated recursively, for all the opponents this player played.

Note, the `k-search` does not guarantee the found player is `k`-distance away, as the found player can have other games,
with shorter (or even 0-distance) from the current root player.
Together, `k-search` and `d-search` guarantees the player found is at least `d`-distance away, with the hope of being
`k`-distance away. 

In terms of runtime, `k-search` scales linearly, and arguably, `k`=5 is sufficient. On the other hand, `d-search` scales exponentially,
in two dimensions, as it takes longer to recursively find all players, and it is increasingly easier to find out the 
found player is actually within the distance threshold and get failed. In practice, a `d-search` takes about 
(#MonthsActive + 5)^d + (#UniqueOpponents)^(d-1) API calls. 
With most players having more than 10 active months and more than 1000 unique opponents, even `d`=2 would take too long.

## Filtering
- `TimeClass`: time-class of interest (rapid, blitz, bullet, daily), allows multi-choices
- `ActiveMonths`: months with >= 1 game
- `GameCounts`: {`TimeClass`: MinCount}
- `IsStreamer`: whether the player is identified as a streamer by Chess.com

`k-search`: player played with games included in `TimeClass` with the current player, with more than 2 active months 
(this is a fixed number, required for subsequent `k-search` to work appropriately, and at least `GameCounts` of games in each time-class.

`d-search`: player played with games included in `TimeClass` with the current player, with more than `ActiveMonths` active months, at least
`GameCounts` of games in each time-class, not `IsStreamer`, and at least `d`-distances away from others in `S`.

## Workflow

Note, most parameters are set within each file, and not passed via args.

Run the software with one 1 initial player:

`python main.py`

Run the software with the current populated players in metadata, to add-on to the previous list:

`python main.py --resume`

Filter players, so that the game folder only contains players in the metadata (verified selection):

`python filter_games_data.py`
