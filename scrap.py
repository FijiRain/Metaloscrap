from lxml import html
import requests

url = requests.get("https://www.metalorgie.com")
tree = html.fromstring(url.content)
xpath = //*[@id="content"]/div/div/div[2]/article/ul[2]/li[5]/div
print(tree)
