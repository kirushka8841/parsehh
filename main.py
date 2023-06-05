import requests
from fake_headers import Headers 
import bs4
import lxml
from pprint import pprint
import re
import tqdm


key_words = ('django', 'flask')
url = 'https://spb.hh.ru/search/vacancy?text=python&area=1&area=2'

def get_headers():
    headers = Headers(browser='firefox', os='win')
    headers_data = headers.generate()
    return headers_data
	
def get_html(url, headers_data):
    hh_page_html = requests.get(url, headers=headers_data).text
    return hh_page_html

def get_vacancy_list(hh_page_html):
    hh_page_soup = bs4.BeautifulSoup(hh_page_html, 'lxml')
    vacancy_list = hh_page_soup.find_all(class_="vacancy-serp-item__layout")
    return vacancy_list

def get_information(vacancy_list, list_info, key_words):
    for vacancy in vacancy_list:
        description = vacancy.find("div", class_="g-user-content")

        if description is None:
            description = ""
        else:
            description = description.text

        address = vacancy.find("div", class_="vacancy-serp-item-company").\
            find("div", class_="vacancy-serp-item__info").\
            find(attrs={'class': 'bloko-text', 'data-qa': 'vacancy-serp__vacancy-address'}).text
        city = address.split(',')[0]
        title = vacancy.find(class_="serp-item__title").text
        link = vacancy.find(class_="serp-item__title")["href"]
        vacancy_tag_div = vacancy.find(class_="vacancy-serp-item-body__main-info").find("div", class_="")
        vacancy_tag_span = vacancy_tag_div.find('span', class_="bloko-header-section-3")
        employer = vacancy.find("div", class_="vacancy-serp-item-company").\
                find("div", class_="bloko-v-spacing-container bloko-v-spacing-container_base-2").\
                find("a").text
        if vacancy_tag_span is not None:
            salary = format_salary(vacancy_tag_span.text)
        else:
            salary = "Зарплата не указана"
        if any(key_word in title.lower() or key_word in description.lower() for key_word in key_words):
            about_vacancy = {
                "Должность": title,
                "Ссылка": link,
                "Зарплата": salary,
                "Компания": employer,
                "Город": city
                }
            list_info.append(about_vacancy)
    return list_info

def format_salary(salary_string):
    match = re.findall(r'\d[\d\s]*\d|\d+', salary_string)
    if match:
        digits = [int(m.replace('\u202f', '')) for m in match]
        currency = re.sub(r'\d', '', salary_string).replace('\u202f', '').strip()
        if len(digits) == 1:
            return f"{digits[0]} {currency}"
        elif len(digits) == 2:
            return f"{digits[0]}-{digits[1]} {currency}"
        else:
            return "Зарплата не указана"
    return "Зарплата не указана"

def pages_find(url):
    html = get_html(url=url)
    bs = bs4.BeautifulSoup(html, features='html5lib')
    num_pages = bs.find(class_="pager")
    list_span = []
    for span in num_pages.find_all("span"):
        title = span.find("span")
        if title is not None and title.text.isdigit():
            list_span.append(int(title.text))
    return max(list_span)

def pages(url, *key_words, num_pages=None):
    vacancies = []
    headers_data = get_headers()
    if num_pages is not None:
        num_pages = pages_find(url=url)       
        for page in tqdm(range(num_pages), desc='Поиск по страницам ...'):
            url_page = url + f'&page={page}'
            html = get_html(url=url_page, headers_data=headers_data)
            vacancies_list = get_vacancy_list(hh_page_html=html)
            vacancies = get_information(vacancies_list, *key_words)
    return vacancies


if __name__ == '__main__':
    vacancies = pages(url, *key_words)
    pprint(vacancies)