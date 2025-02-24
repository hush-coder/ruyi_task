import requests
issue_url = "https://api.github.com/repos/ruyisdk/packages-index/issues/28"
response = requests.get(issue_url)
print("Closed" if response.json()["state"] == "closed" else "Open")
