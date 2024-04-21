import csv
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import psycopg2
from psycopg2 import sql
import googlemaps
from datetime import datetime
import requests

gmaps = googlemaps.Client(key='AIzaSyD7xicoRah_jW46T0gOAhmISDVMua3QuSQ')


def connect_db():
    conn = psycopg2.connect(
        dbname="Hackathon",
        user="postgres",
        password="1234",
        host="localhost"
    )
    return conn

def insert_ad(data):
    conn = connect_db()
    try:
        with conn:
            with conn.cursor() as cur:
                query = """
                INSERT INTO ads (url, title, phone, address, latitude, longitude, description, use_instructions, schedule, image_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (url) DO NOTHING;
                """
                cur.execute(query, (
                    data['url'], data['title'], data['phone'], data['address'],
                    data['latitude'], data['longitude'], data['description'],
                    data['use_instructions'], data['schedule'], data['image_url']
                ))
    except Exception as e:
        print("Error inserting data: ", e)
    finally:
        conn.close()

sleep_interval = 3600

driver_path = '/opt/homebrew/Caskroom/chromedriver/123.0.6312.122/chromedriver-mac-arm64/chromedriver'

options = Options()
options.headless = True 

service = Service(executable_path=driver_path)
driver = webdriver.Chrome(service=service, options=options)
driver.get("https://astana.citypass.kz/ru/popular/")
WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.sights__item--btn-linck')))

main_window = driver.current_window_handle

visited_urls = set()

with open('crocos_data.csv', mode='a', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    if file.tell() == 0:
        writer.writerow(['URL', 'Мероприятие', 'Номер телефона', 'Адрес', 'Широта', 'Долгота', 'Описание', 'Как пользоваться', 'Расписание'])

try:
    while True:
        sights_items = driver.find_elements(By.CSS_SELECTOR, '.sights__item')
        for item in sights_items:
            image_element = item.find_element(By.CSS_SELECTOR, '.sights__item--img img')
            image_url = image_element.get_attribute('src') if image_element else None
            
            btn_link = item.find_element(By.CSS_SELECTOR, '.sights__item--btn-linck')
            href = btn_link.get_attribute('href') if btn_link else None

            if href and href not in visited_urls:
                visited_urls.add(href)
                driver.execute_script("window.open(arguments[0]);", href)
                WebDriverWait(driver, 15).until(EC.number_of_windows_to_be(2))
                new_window = [window for window in driver.window_handles if window != main_window][0]
                driver.switch_to.window(new_window)
            
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.object__title')))
            
            content = driver.page_source
            soup = BeautifulSoup(content, 'html.parser')
            
            name_data = soup.find('h1', class_='object__title')
            adres_data = soup.find('div', class_='object__info--adres')
            phone_data = soup.find('div', class_='object__info--email object__info--phone-repeater')

            if adres_data:
                if adres_data.svg and adres_data.svg.get_text(strip=True):
                    svg_text = adres_data.svg.get_text(strip=True)
                    address = adres_data.get_text(strip=True).replace(svg_text, '').strip()
                else:
                    address = adres_data.get_text(strip=True)
            else:
                address = 'Недоступно'
                    
            name = name_data.text.strip() if name_data else 'Недоступно'
            phone = phone_data.find('a', href=lambda x: x and x.startswith('tel:')).get_text(strip=True) if phone_data else 'Недоступно'

            first_p_description_data = soup.select_one('.object_content--desc p')
            if first_p_description_data and "Для прохода в Театр аниматрониксов" in first_p_description_data.get_text():
                first_p_description = soup.select('.object_content--desc p')[5].get_text(strip=True) if first_p_description_data else 'Недоступно'
            else:
                first_p_description = first_p_description_data.text.strip() if first_p_description_data else 'Недоступно'

            geocode_data = gmaps.geocode(address)
            latitude = geocode_data[0]['geometry']['location']['lat'] if geocode_data else 'Недоступно'
            longitude = geocode_data[0]['geometry']['location']['lng'] if geocode_data else 'Недоступно'
            

            timetable_div = soup.find('div', class_='object_content--right-list object_content--timetable')
            schedule = {}
            if timetable_div:
                days = timetable_div.find_all('li')
                for day in days:
                    day_name = day.find('div', class_='object_content-one').get_text(strip=True)
                    hours = day.find('div', class_='object_content-too').get_text(strip=True)
                    schedule[day_name] = hours
            else:
                'Недоступно'
                    
            section_title = soup.find('div', class_='sectipon__title--info').text.strip()
            description = soup.find('div', class_='how_desc').find_all('p')
            instructions = [desc.text.strip() for desc in description]
            steps = soup.find('ul', class_='blue-krug').find_all('li')
            step_list = [step.text.strip() for step in steps]


            with open('crocos_data.csv', mode='a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([href, name, phone, address, latitude, longitude, first_p_description, instructions, step_list,] + [f"{day}: {hours}" for day, hours in schedule.items()] if timetable_div else ['Недоступно'])
            
            data = {
                'url': href,
                'title': name,
                'phone': phone,
                'address': address,
                'latitude': latitude,  
                'longitude': longitude,  
                'description': first_p_description,
                'use_instructions': ' '.join(instructions),
                'schedule': ' '.join([f"{day}: {hours}" for day, hours in schedule.items()]) if timetable_div else 'Недоступно',
                'image_url': image_url
                }
            insert_ad(data)

            
            driver.close()
            driver.switch_to.window(main_window)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".sights__item--btn-linck")))
        
        next_page = driver.find_elements(By.CSS_SELECTOR, '.pag-next-page a.next_page')
        if next_page:
            next_page[0].click()
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.sights__item--btn-linck')))
        else:
            driver.get("https://astana.citypass.kz/ru/popular/")
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.sights__item--btn-linck')))
            break
        
finally:
    driver.quit()
    
time.sleep(sleep_interval)
