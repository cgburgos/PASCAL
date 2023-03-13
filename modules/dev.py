import os
import json

print("////////////////////////////////")
print("////////////////////////////////")

with open("modules/api/ChatGPTtemplates.json", "r") as jsonFile:
    ChatGPTtemplates = json.load(jsonFile)

print(list(ChatGPTtemplates.keys()))