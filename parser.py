import json
import re
import csv
import requests
import time
import datetime
import multiprocessing
from bs4 import BeautifulSoup
from fake_useragent import UserAgent


class parser_machine:
    def __init__(self, city_code=84, API_KEY='11d3b9291d7b82c3be1640efb16eb525'):
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8, application/signed-exchange;v=b3;q=0.9',
            'UserAgent': UserAgent().random,
        }

        self.cookies = {
            'OP_SAMSON_CITY': f'{city_code}'
        }

        self.proxies = {
            'htpp': f'http://scraperapi:{API_KEY}@proxy-server.scraperapi.com:8001'
        }

        self.city = None
        self.cur_time = None

    def get_urls_of_xml(self, xml_url):
        # Получение ссылок на товары
        xml = requests.get(xml_url).text
        soup = BeautifulSoup(xml, 'lxml')

        links__arr = []
        for link in soup.findAll('loc'):
            link__str = link.getText('', True)
            if '/catalog/goods/' in link__str:
                links__arr.append(link__str)

        print('[+] References received')
        return links__arr

    def get_city_and_time(self, url):
        # Получение города и текущего времени
        response = requests.get(url=url, headers=self.headers, cookies=self.cookies, proxies=self.proxies)
        soup = BeautifulSoup(response.text, 'lxml')
        self.cur_time = datetime.datetime.now().strftime('%d_%m_%Y_%H_%M')
        self.city = soup.find('div', class_='dropdowncity HeaderPanelPlace__item').text.strip()

    def create_csv(self):
        # Создание csv-файла в соответсвии с указанным городом
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

    def collect_data(self, link):
        # Получение страницы товара
        self.headers['UserAgent'] = UserAgent().random
        response = requests.get(url=link, headers=self.headers, cookies=self.cookies, proxies=self.proxies)
        soup = BeautifulSoup(response.text, 'lxml')
        self.get_item_info(soup, response)

    def get_item_info(self, soup, response):
        # Наименование товара
        title = soup.find('h1', class_='Product__name js-itemPropToRemove js-detailProductName').text.strip()

        # Брэнд
        brand = json.loads(soup.find('div', class_='itemInfoDetails group').attrs['data-ga-obj'])['brand']

        # Категории по уровням
        levels = soup.find('ul', class_='breadcrums').find_all('li')
        level__1 = levels[-3].text.strip()
        level__2 = levels[-2].text.strip()
        level__3 = levels[-1].text.strip()

        # Артикул
        article = int(re.findall('\d+', soup.find('span', class_='code js-productDetailCode').text)[0])

        # Текущая цена и цена без скидки
        try:
            current__price = soup.find('div', class_='itemInfoDetails group').find('div', class_='Product__price js-itemPropToRemove')['content']
            no__discount__price__block = soup.find('div', class_='itemInfoDetails group').find('div', class_='Product__price Product__price--initial')
            price__count = ''.join(re.findall('\d+', no__discount__price__block.find('span', class_='Price__count').text))
            price__penny = no__discount__price__block.find('span', class_='Price__penny').text
            no__discount__price = f'{price__count}.{price__penny}'
        except Exception:
            try:
                current__price = soup.find('div', class_='itemInfoDetails group').find('div', class_='Product__price js-itemPropToRemove')['content']
                no__discount__price = None
            except Exception:
                current__price = None
                no__discount__price = None

        # Статус, количество на складе
        try:
            avail = soup.find('div', class_='ProductState ProductState--red').find(text=re.compile('Временно отсутствует|Недоступен')).text
            if 'Временно отсутствует' in avail:
                availability = 'нет в наличии'
                quantity = 0
            else:
                availability = 'недоступен к заказу'
                quantity = None
        except AttributeError:
            try:
                avail = soup.find('table', class_='AvailabilityList AvailabilityList--dotted').find(text=re.compile('Наличие')).text
                quantity = int(re.findall('\d+', soup.find('tr', class_='AvailabilityItem').text)[0])
                availability = 'в наличии'
            except AttributeError:
                try:
                    avail = soup.find('div', class_='Availability__aux').find(text=re.compile('Под заказ')).text
                    quantity = int(re.findall('\d+', soup.find('div', class_='Availability__hint').text)[0])
                    availability = 'под заказ'
                except AttributeError:
                    availability = None
                    quantity = None

        # Сроки доставки
        try:
            delivery__time = soup.find('div', class_="itemInfoDetails group").find(text=re.compile('Удаленный склад')).text
        except AttributeError:
            try:
                delivery__time = soup.find('div', class_="Availability__aux").find(text=re.compile('Срок поставки'))
            except AttributeError:
                delivery__time = None

        # Количество товара: минимальная партия, в упаковке
        order__quantity = soup.find('div', class_='itemInfoDetails group').find_all('div', class_='ProductState ProductState--gray')
        if len(order__quantity) != 0:
            min__batch, in__package = [re.findall('\d+', val.text) for val in order__quantity]
            min__batch = int(min__batch[0])
            in__package = int(in__package[0])
        else:
            min__batch, in__package = None, None

        # Характеристики товара
        try:
            specifications__block = soup.find('ul', class_='infoFeatures').find_all('li')[1:]
            specifications = '\n'.join([' '.join(s.text.split()) for s in specifications__block])
        except AttributeError:
            specifications = None

        # Ссылка на товар
        link__product = response.url

        # Добавление информации о товаре в csv-файл
        with open(f'{self.city}_{self.cur_time}.csv', 'a', newline="") as file:
            writer = csv.writer(file)

            writer.writerow(
                [
                    title,
                    brand,
                    level__1,
                    level__2,
                    level__3,
                    article,
                    current__price,
                    no__discount__price,
                    availability,
                    quantity,
                    in__package,
                    min__batch,
                    specifications,
                    delivery__time,
                    link__product,
                ]
            )

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


if __name__ == '__main__':
    # Создание объекта
    # city_code: код города, согласно сайту, (по умолчанию - Москва)
    # API_KEY: ключ, для получения Proxy с сайта https://www.scraperapi.com/
    obj = parser_machine(city_code=84, API_KEY='11d3b9291d7b82c3be1640efb16eb525')
    obj.run()
