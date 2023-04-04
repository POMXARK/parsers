from datetime import date
import pandas as pd
from bs4 import BeautifulSoup as bs
import requests
from datetime import datetime
from pandas.tseries.offsets import BDay
from pprint import pprint

today = date.today()
count_days = 1
min_date = pd.to_datetime(today - BDay(count_days), format='%d%b%Y').date()
#print(f"Дата публикации извещения / внесения изменений от {min_date} до {today}")


class ParserHandler:

    def __init__(self):
        self.data = []
        self.unique_links = []

    def get_content(self):
        """Сохранить список ссылок на страницы сведений о закупках"""
        page = 1
        stop = 0
        while True:
            if stop == 1:
                break
            # level_0
            url_template = f"https://zakupki.rosatom.ru/Web.aspx?node=currentorders&ostate=F&page={page}"
            response = requests.get(url_template)
            page += 1
            soup = bs(response.text, "lxml")
            tbody = soup.find("tbody")

            # запись всех данных из строки в элемент словаря
            for idx, el_tr in enumerate(tbody.select('tr')):
                d = {
                    'Наименование закупки': '-',
                    'Цена': '-',
                    'Организатор закупки': '-',
                    'Дата окончания приема заявок / подведения итогов': '-',
                    'Наименование поставщика': '-',
                    'ИНН': '-',
                    'Телефон': '-',
                    'Факс': '-',
                    'Контактные лица': '-',
                }
                # исключить скрытые строки (even description, odd description)
                if idx % 2 == 0:
                    all_td = el_tr.find_all('td')
                    publication_date = (all_td[5].text.strip())

                    # ограничение по Дата публикации извещения / внесения изменений для каждой строки
                    if datetime.strptime(publication_date, '%d.%m.%Y').date() < min_date:
                        stop = 1
                        break

                    d['Наименование закупки'] = all_td[2].find('a').text.strip()
                    d['Цена'] = all_td[3].find('p').text.strip()
                    # print(all_td[3].find('p').text.strip())
                    d['Организатор закупки'] = all_td[4].text.strip()
                    d['Дата окончания приема заявок / подведения итогов'] = " ".join(all_td[6].text.strip().split())

                    # переход на вложенную страницу level_1
                    url_template = f"https://zakupki.rosatom.ru/{all_td[2].find('a')['href'][1:]}"
                    response = requests.get(url_template)
                    soup = bs(response.text, "lxml")

                    tab = soup.find(id='tab1')
                    provider = tab.find_all(class_='property-table')[2].find('table')
                    for el_tr in provider.select('tr'):
                        all_td = el_tr.find_all('td')
                        key = all_td[0].text.strip()
                        value = all_td[1].text.strip()

                        # запись данных
                        for _key in d.keys():
                            if key == _key:
                                d[_key] = value

                        # переход на вложенную страницу level_2
                        try:
                            link = all_td[1].find('a')['href'][1:]
                        except:
                            continue

                        if link is not None:
                            url_template = f"https://zakupki.rosatom.ru/{link}"
                            response = requests.get(url_template)
                            soup = bs(response.text, "lxml")
                            for tables in soup.find_all(class_='property-table'):
                                for el_tr in tables.find('table').find_all('tr'):
                                    all_td = el_tr.find_all('td')
                                    key = all_td[0].text.strip()
                                    value = all_td[1].text.strip()

                                    # запись данных
                                    for _key in d.keys():
                                        if key == _key:
                                            d[_key] = value

                    # запись строки таблицы
                    self.data.append(d)


# pprint(get_content())

parse = ParserHandler()
parse.get_content()

df = pd.DataFrame(parse.data)
df.to_excel(f'{min_date}_{str(date.today())}.xlsm', index=False)
# df.to_csv('output_' + str(date.today()) + '.csv', index=False)
