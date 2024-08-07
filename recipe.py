import requests
from bs4 import BeautifulSoup
import csv

materials = ["乾パン", "レトルトカレー", "さば缶", "ツナ缶", "パスタ", "クラッカー", "グラノーラ"]

recipes = []
base_url = 'https://recipe.rakuten.co.jp'

for material in materials:
    response = requests.get(base_url + '/search/' + material)
    soup = BeautifulSoup(response.content, 'html.parser')
    elements = soup.find_all('a', class_='recipe_ranking__link')
    for j in elements:
        title = j.find("span", class_="recipe_ranking__recipe_title omit_2line").text.strip()
        image = j.find("img")['src']
        recipe_link = base_url + j['href']
        recipes.append({
            'title': title,
            'image_url': image,
            'parent_category': material,
            'link': recipe_link
        })

# 写入到CSV文件
csv_file = 'recipes.csv'
csv_columns = ['title', 'image_url', 'parent_category', 'link']

with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
    writer.writeheader()
    for recipe in recipes:
        writer.writerow(recipe)

print(f"Successul data save  {csv_file}")