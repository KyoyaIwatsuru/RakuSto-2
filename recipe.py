import requests
from bs4 import BeautifulSoup
import re
import csv

base_url = 'https://recipe.rakuten.co.jp'

# 获取所有分类的URL
category_url = f'{base_url}/category/'
response = requests.get(category_url)
soup = BeautifulSoup(response.content, 'html.parser')

categories = soup.find_all('li', class_='category_top-list__item')
category_list = []

for category in categories:
    name = category.find('span').text.strip()
    link = base_url + category.find('a', class_='category_top-list__link')['href']
    name = re.sub(r'\(.*?\)', '', name).strip()
    category_list.append({'name': name, 'url': link})

# 提取上一级分类名称
def extract_parent_category(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    category_name = soup.find('title').text.split('-')[0].strip()
    return category_name

# 获取每个分类下的食谱详情
def fetch_recipe_details(url, parent_category):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    recipes = []
    recipe_items = soup.select('ol.recipe_ranking__list li.recipe_ranking__item')
    
    for item in recipe_items:
        recipe_link = base_url + item.find('a', class_='recipe_ranking__link')['href']
        recipe_title = item.find('span', class_='recipe_ranking__recipe_title').text.strip()
        recipe_image = item.find('img')['src']
        recipes.append({
            'title': recipe_title,
            'image_url': recipe_image,
            'parent_category': parent_category,
            'link': recipe_link
        })
    
    return recipes

# 遍历每个分类URL并提取食谱信息
all_recipes = []

for category in category_list:
    parent_category = extract_parent_category(category['url'])
    recipes = fetch_recipe_details(category['url'], parent_category)
    all_recipes.extend(recipes)

# 写入到CSV文件
csv_file = 'recipes.csv'
csv_columns = ['title', 'image_url', 'parent_category', 'link']

with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
    writer.writeheader()
    for recipe in all_recipes:
        writer.writerow(recipe)

print(f"数据已成功写入 {csv_file}")