# URL of the API
url="https://api.chess.com/pub/player/jimmyjia/stats"

# Record the start time
start_time=$(date +%s)

# Run the API 100 times
for i in {1..500}; do
    response=$(curl -v https://api.chess.com/pub/player/jimmyjia/stats)
done

# Record the end time
end_time=$(date +%s)

# Calculate the total time taken
total_time=$((end_time - start_time))

echo "Total time taken for 10 API calls: ${total_time} seconds"
