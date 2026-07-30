import requests
from bs4 import BeautifulSoup
key = 'junior python'
page = '1'
url = f'https://djinni.co/jobs/?all_keywords={key}&search_type=basic-search&page={page}'
BASE_URL = 'https://djinni.co'



response = requests.get(
    url,
    headers={
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/138.0.0.0 Safari/537.36"
        )
    }
)

soup = BeautifulSoup(response.text,"html.parser")


def create_vacancie_url(card):
    link_element = card.find('a', class_='job_item__header-link')
    if link_element and 'href' in link_element.attrs:
        return BASE_URL + f"{link_element['href']}"
    return None

cards = soup.select("div.job-item")


vacancie_url = create_vacancie_url(cards[0])
# print(vacancie_url)
response_vacancie = requests.get(
    vacancie_url,
    headers={
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/138.0.0.0 Safari/537.36"
        )
    }
)
vacancie_soup = BeautifulSoup(response_vacancie.text,"html.parser")
card = vacancie_soup.select('.container.job-post-page')
# print(card)
        


