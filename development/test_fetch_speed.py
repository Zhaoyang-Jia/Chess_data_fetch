
## testing parallelization
# import concurrent.futures
# import subprocess
# import time
#
# # URL of the API
# url = 'https://api.chess.com/pub/player/jimmyjia/stats'
# urls = [url for _ in range(1000)]
#
#
# def fetch_data(input_url):
#     curl_command = ['curl', '-v', input_url]
#     result = subprocess.run(curl_command, capture_output=True, text=True)
#     print(result.stdout)
#     if result.returncode == 0:
#         return result.stdout  # or handle the content as needed
#     else:
#         print(result.returncode)
#         return -1
#
#
# start_time = time.time()
# with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
#     results = list(executor.map(fetch_data, urls))
#
# end_time = time.time()
# total_time = end_time - start_time
# print(f"Total time taken for 100 API calls: {total_time:.2f} seconds")
#
# print(results)


## working code: using subprocess
# import subprocess
#
# # Define the curl command
# curl_command = ['curl', '-v', 'https://api.chess.com/pub/player/jimmyjia/stats']
#
# for _ in range(100):
#     result = subprocess.run(curl_command, capture_output=True, text=True)
#
#     ## Print the output
#     # print("Return Code:", result.returncode)
#     print("Standard Output:\n", result.stdout)
#     if result.returncode != 0:
#         print("Standard Error:\n", result.stderr)
#     print()