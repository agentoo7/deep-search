from duckpy import Client

client = Client()
results = client.search("Python Wikipedia")
# print(results)

# # In ra kết quả đầu tiên
# print(results[0]['title'])
# print(results[0]['url'])
# print(results[0]['description'])

for r in results:
    print(r)
