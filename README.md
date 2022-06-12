# <a name="general"></a>Тестовое задание на сбор данных
## Описание
**Цель:** Спарсить все товары и описанную ниже информацию для каждого товара с магазина Офисмаг 

**Сайт:** [`https://www.officemag.ru/`](https://www.officemag.ru/)

**Локация:** Москва

**Объем данных:** Все товары, представленные на сайте

**Информация о товаре:**
+	Наименование товара
+	Бренд
+	Категория 1 уровня
+	Категория 2 уровня
+	Категория 3 уровня
+	Артикул
+	Текущая цена
+	Цена без скидки (если есть скидка, если нет - пустое поле)
+	Статус товара (в наличии, под заказ, нет в наличии)
+	Количество
+	Количество в упаковке
+	Минимальная партия товара
+	Характеристики товара (вес, объем и т.п)
+	Сроки поставок
+	Ссылка на товар
___
## Результаты
Собранные данные представлены в zip-файле [`Москва_12_06_2022_08_13.zip`](https://github.com/AlexMtnkv/scraping/blob/main/Москва_12_06_2022_08_13.zip)

Состояние терминала:

![image](https://user-images.githubusercontent.com/90116073/173212387-2a18f418-036c-4240-86f7-73577da7d7d5.png)
___
## Аномалии
По ссылкам представленным ниже не удалось получить характеристики товаров, даже при отдельном рассмотрении:
+ [`https://www.officemag.ru/catalog/goods/982206`](https://www.officemag.ru/catalog/goods/982206)
+ [`https://www.officemag.ru/catalog/goods/982205`](https://www.officemag.ru/catalog/goods/982205)
+ [`https://www.officemag.ru/catalog/goods/980604`](https://www.officemag.ru/catalog/goods/980604)
+ [`https://www.officemag.ru/catalog/goods/980605`](https://www.officemag.ru/catalog/goods/980605)
+ [`https://www.officemag.ru/catalog/goods/980606`](https://www.officemag.ru/catalog/goods/980606)
+ [`https://www.officemag.ru/catalog/goods/982208`](https://www.officemag.ru/catalog/goods/982208)
+ [`https://www.officemag.ru/catalog/goods/982207`](https://www.officemag.ru/catalog/goods/982207)
+ [`https://www.officemag.ru/catalog/goods/980607`](https://www.officemag.ru/catalog/goods/980607)
+ [`https://www.officemag.ru/catalog/goods/980608`](https://www.officemag.ru/catalog/goods/980608)
+ [`https://www.officemag.ru/catalog/goods/980609`](https://www.officemag.ru/catalog/goods/980609)
___
## Использованные технологии
+ В качестве парсера взят [`BeautifulSoup`](https://beautiful-soup-4.readthedocs.io/en/latest/)
+ Для многопоточности [`multiprocessing`](https://pydocs2cn.readthedocs.io/projects/pydocs2cn/en/latest/library/multiprocessing.html)
+ Прокси с сайта [`ScraperAPI`](https://www.scraperapi.com/)

В файле [`req.txt`](https://github.com/AlexMtnkv/scraping/blob/main/req.txt) содержаться полный список библиотек и технологий, используемых в данном проекте.
___
## Описание кода
Создание объекта класса `parser_machine`, где в качестве входных данных: `city_code` - код города, согласно параметру cookies сайта `OP_SAMSON_CITY`, по умолчанию - Москва (84); `API_KEY` - ключ из личного кабинета, для получения Proxy с сайта [`ScraperAPI`](https://www.scraperapi.com/).
```python
if __name__ == '__main__':
    obj = parser_machine(city_code=84, API_KEY='11d3b9291d7b82c3be1640efb16eb525')
    obj.run()
```
Иницилизация объекта класса
```python
def __init__(self, city_code=84, API_KEY='11d3b9291d7b82c3be1640efb16eb525'):
	# Шапка браузера
	self.headers = {
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8, application/signed-exchange;v=b3;q=0.9',
		'UserAgent': UserAgent().random,
	}
	
	# Cookies
	self.cookies = {
		'OP_SAMSON_CITY': f'{city_code}'
	}
	
	# Proxy-server
	self.proxies = {
		'htpp': f'http://scraperapi:{API_KEY}@proxy-server.scraperapi.com:8001'
	}
	
	# Город и текущее время
	self.city = None
	self.cur_time = None
```
Получение ссылок на товары, создание CSV-файла, получение DataSeta с помощью многопоточности и вывод общего времени выполнения программы
```python
def run(self):
	start_time = time.time()

	# Получение ссылок на товары с помощью sitemap
	links_data_arr = self.get_urls_of_xml("https://www.officemag.ru/sitemap/sitemap_1.xml")

	# Создание csv-файла
	self.get_city_and_time('https://www.officemag.ru/')
	self.create_csv()

	# Генерирование DataSet используя многопоточность
	print('Please wait...')
	with multiprocessing.Pool(multiprocessing.cpu_count()) as p:
		p.map(self.collect_data, links_data_arr)

	end_time = time.time()
	process_time = time.strftime("%H:%M:%S", time.gmtime(end_time - start_time))
	print(f'Successfully!\nProcess time: {process_time}')
```
Получение ссылок, используя `sitemap`. Товары имеют отличительную особенность в url - `/catalog/goods/`
```python
def get_urls_of_xml(self, xml_url):
	xml = requests.get(xml_url).text
	soup = BeautifulSoup(xml, 'lxml')

	links__arr = []
	for link in soup.findAll('loc'):
		link__str = link.getText('', True)
		if '/catalog/goods/' in link__str:
			links__arr.append(link__str)

	print('[+] References received')
	return links__arr
```
Получение названия города и текущего времени
```python
def get_city_and_time(self, url):
	response = requests.get(url=url, headers=self.headers, cookies=self.cookies, proxies=self.proxies)
	soup = BeautifulSoup(response.text, 'lxml')
	self.cur_time = datetime.datetime.now().strftime('%d_%m_%Y_%H_%M')
	self.city = soup.find('div', class_='dropdowncity HeaderPanelPlace__item').text.strip()
```
Создание CSV-файла в соответсвии с указанным городом и временем
```python
def create_csv(self):
	with open(f'{self.city}_{self.cur_time}.csv', 'w', newline="") as file:
		writer = csv.writer(file)

		writer.writerow(
			[
				'Наименование товара',
				'Бренд',
				'Категория 1 уровня',
				'Категория 2 уровня',
				'Категория 3 уровня',
				'Артикул',
				'Текущая цена',
				'Цена без скидки',
				'Статус товара',
				'Количество на складе',
				'Количество в упаковке',
				'Минимальная партия товара',
				'Характеристики товара',
				'Сроки поставки',
				'Ссылка на товар',
			]
		)

	print('[+] CSV-file created')
```
Получение страницы товара
```python
def collect_data(self, link):
	response = requests.get(url=link, headers=self.headers, cookies=self.cookies, proxies=self.proxies)
	soup = BeautifulSoup(response.text, 'lxml')
	self.get_item_info(soup, response)
```
В функции `get_item_info` реализовано получение необходимой информации о товаре и её последующее добавление в CSV-файл.

**Полный код в файле**: [`parcer.py`](https://github.com/AlexMtnkv/scraping/blob/main/parser.py)

[:arrow_up:Наверх](#general)
