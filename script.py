from __future__ import print_function
import time
import json
import pickle
import os.path
from selenium import webdriver
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


with open('config.json') as config_file:
    config = json.load(config_file)


# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/contacts']

creds = None
# The file token.pickle stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'client_id.json', SCOPES)
        creds = flow.run_local_server()
    # Save the credentials for the next run
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)

service = build('people', 'v1', credentials=creds)

chromedriver = config.get('chromedriver_path', False)
force_all = config.get('force_all', False)
count_leads = config.get('count_leads', 1)

driver = webdriver.Chrome(chromedriver)
driver.get("https://web.whatsapp.com")
input('Aperte enter após escanear o QR Code...')


try:
    numbers = set()
    while True:
        a = driver.find_elements_by_class_name("_1wjpf")
        if force_all or any('+' in el.get_attribute('title') for el in a):  # temos gente nova pra adicionar
            for el in a:
                name = el.get_attribute('title')
                if len(name) > 0:
                    # el.click()
                    numbers.add(name)

            recent_list = driver.find_elements_by_xpath("//div[@class='_2wP_Y']")
            for recent in recent_list:
                driver.execute_script("arguments[0].scrollIntoView();", recent)

            time.sleep(0.1)
        else:
            print('Ninguém novo para adicionar')
            break
except Exception:
    pass


new_numbers = [number for number in numbers if '+' in number]
print('Quantidade de novos números:', len(new_numbers))


for i, number in enumerate(new_numbers[:]):
    service.people().createContact(parent='people/me', body={
        "names": [{
            "givenName": "LI 11 - {}".format(str(count_leads).zfill(5))
        }],
        "phoneNumbers": [{
            'value': number
        }]
    }).execute()
    count_leads += 1
    print('Inserido ({}): {}'.format(i, number))
    new_numbers.remove(number)
    if (i + 1) % 90 == 0:
        print('Escrevemos 90 usuários, vamos aguardar 1 min para escrever mais 90...')
        time.sleep(60)

# atualiza quantidade de leads
config['count_leads'] = count_leads
with open('config.json', 'w') as config_file:
    json.dump(config, config_file, indent=4)

print('Finalizado!')
