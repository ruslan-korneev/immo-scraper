from datetime import datetime
from typing import Optional, Union

from bs4 import BeautifulSoup


def parse_locals(value: BeautifulSoup) -> Union[int, str]:
    value = value.find(
        'span', class_="im-mainFeatures__value"
    ).text.strip().replace('+', '')
    try:
        return int(value)
    except ValueError:
        return value


def parse_date_of_sale(value: BeautifulSoup) -> Optional[str]:
    try:
        date_of_sale = value.find(
            'span', class_="im-mainFeatures__value").text.strip()
        return str(datetime.strptime(date_of_sale, '%d/%m/%Y'))
    except AttributeError:
        return


def parse_surface(value: BeautifulSoup):
    quantity, unit = value.find(
        'span', class_="im-mainFeatures__value").text.strip().split()
    return {"quantity": float(quantity), "unit": unit}


def parse_bathrooms(value: BeautifulSoup) -> Union[int, str]:
    value = value.find(
        'span', class_="im-mainFeatures__value"
    ).text.strip().replace('+', '')
    try:
        return int(value)
    except ValueError:
        return value


def parse_plan(value: BeautifulSoup) -> str:
    return value.find('span', class_="im-mainFeatures__value").text.strip()


GET_PARAMETR_PARSER = {
    "locals": parse_locals,
    "date_of_sale": parse_date_of_sale,
    "surface": parse_surface,
    "bathrooms": parse_bathrooms,
    "plan": parse_plan,
}


def translate_label(label: str) -> str:
    """ translate italian-labels to english """
    LABELS = {
        "locali": "locals",
        "data vendita": "date_of_sale",
        "superficie": "surface",
        "bagni": "bathrooms",
        "piano": "plan",
    }
    return LABELS[label]


def parse_product(soup: BeautifulSoup, url: str) -> dict:
    """ parse product-data from web-page """
    # looking for title, description, seller data
    title = soup.find('span', class_="im-titleBlock__title").text.strip()
    description = soup.find(
        'div', class_="im-description__text js-readAllText"
    ).text.strip()
    try:
        seller_name = soup.find(
            'div', class_='im-lead__supervisor').find('p').text
        seller_phone = soup.find('div', class_='im-lead__supervisor').find(
            'a', class_="im-lead__phone").find_next('a').get('href')
        seller = {"name": seller_name, "phone": seller_phone}
    except AttributeError:
        seller = None

    # get price if exists
    price_box = soup.find('div', class_="im-mainFeatures__title").text.strip()
    price_box = price_box.replace('da', '').strip()
    try:
        currency = price_box.split()[0]
        price = float(price_box.split()[1].replace('.', '').replace(',', '.'))
    except ValueError:
        currency = None
        price = price_box

    # looking for photos
    photos = []
    try:
        photo_numbers = int(soup.find(
            'a', id="foto-tab"
        ).text.strip().split()[0])
        for photo_number in range(1, photo_numbers+1):
            photos.append(f"{url}#foto{photo_number}")
    except ValueError:
        photos.append(f"{url}#foto1")
    except AttributeError:
        pass

    # save results to `result`
    result = {
        "title": title,
        "description": description,
        "url": url,
        "seller": seller,
        "price": {"quantity": price, "currency": currency},
        "photos": photos,
        "parametrs": {}
    }

    # looking for other parametrs
    ul: list[BeautifulSoup] = soup.find(
        'div', class_="im-mainFeatures__title").find_all_next(
            'li', class_="nd-list__item")
    for li in ul:
        if '© 2022 Immobiliare.it' in li.text.strip():
            break
        try:
            label = translate_label(li.find(
                'span', class_='im-mainFeatures__label'
            ).text.strip())
            parametr = {label: GET_PARAMETR_PARSER[label](li)}
        except (KeyError, AttributeError):
            continue
        result["parametrs"].update(parametr)

    return result
