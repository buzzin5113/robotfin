"""
Расчет привлекательности акций

1. Прогнозный рост
    Стоимость 2 балла
    Прогнозный рост акций
    Значения от 0 до 50%
    Стоимость от 0 до 2
    Расчет: ((Sreal-Sprog)/(Sreal/100))*0.0.2
            if < 0 = 0
            if > 2 = 2
2. Дивиденты
    Стоимость 0.5 балла
    Дивиденты годовые
    Значения от 2 до 10
    Стоимость от 0 до 0.5
    Расчет: (DIV-2)*(0.5/8)
3. P/E
    Стоимость 1 балл.
    Отношение прибыли к стоимости компании.
    Значения - от 20 до 5
    Стоимость - от 0 до 1
    Расчет: 1 - (P/E-5*(1/15))
            if > 1 = 1
            if < 0 = 0
4. Forward P/E
    Стоимость 0.5 балла.
    Прогнозное отношение прибыли к стоимости компании.
    Значения - от 20 до 5
    Стоимость - от 0 до 0.5
    Расчет: 0.5 - (P/E-5*(1/30))
            if > 0.5 = 0.5
            if < 0 = 0
5. MinMax
    Стоимость 1 балл
    Текущая позиция относительно изменения цены за год
    Расчет: 1 -  (vMax - VMin / ((((vMax - vMin)/2) - vPrice))

"""

import urllib3
from lxml import html
import requests
from time import sleep
import json
import argparse
from random import randint
import re


def parse_finance_page(ticker):
    """
    Grab financial data from NASDAQ page

    Args:
      ticker (str): Stock symbol

    Returns:
      dict: Scraped data
    """
    key_stock_dict = {}
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-GB,en;q=0.9,en-US;q=0.8,ml;q=0.7",
        "Connection": "keep-alive",
        "Host": "www.nasdaq.com",
        "Referer": "http://www.nasdaq.com",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.119 Safari/537.36"
    }

    # Retrying for failed request
    for retries in range(5):
        try:
            url = "http://www.nasdaq.com/symbol/%s" % (ticker)
            response = requests.get(url, headers=headers, verify=False)

            if response.status_code != 200:
                raise ValueError("Invalid Response Received From Webserver")

            #print("Parsing %s" % (url))
            # Adding random delay
            # sleep(randint(1, 3))
            parser = html.fromstring(response.text)
            xpath_head = "//div[@id='qwidget_pageheader']//h1//text()"
            xpath_key_stock_table = '//div[@class="row overview-results relativeP"]//div[contains(@class,"table-table")]/div'
            #xpath_open_price = '//span[@class = "last-sale"]/span'
            #xpath_open_date = '//b[contains(text(),"Open Date:")]/following-sibling::span/text()'
            #xpath_close_price = '//b[contains(text(),"Close Price:")]/following-sibling::span/text()'
            #xpath_close_date = '//b[contains(text(),"Close Date:")]/following-sibling::span/text()'
            xpath_key = './/div[@class="table-cell"]/b/text()'
            xpath_value = './/div[@class="table-cell"]/text()'
            xpath_last_sale = './/span[@class="last-sale"]/text()'

            raw_name = parser.xpath(xpath_head)
            key_stock_table = parser.xpath(xpath_key_stock_table)
            last_sale = parser.xpath(xpath_last_sale)

            company_name = raw_name[0].replace("Common Stock Quote & Summary Data", "").strip() if raw_name else ''
            #open_price = raw_open_price[0].strip() if raw_open_price else None
            #open_date = raw_open_date[0].strip() if raw_open_date else None
            #close_price = raw_close_price[0].strip() if raw_close_price else None
            #close_date = raw_close_date[0].strip() if raw_close_date else None

            # Grabbing ans cleaning keystock data
            for i in key_stock_table:
                key = i.xpath(xpath_key)
                value = i.xpath(xpath_value)
                key = ''.join(key).strip()
                value = ' '.join(''.join(value).split())
                key_stock_dict[key] = value

            nasdaq_data = {

                "company_name": company_name,
                "ticker": ticker,
                "url": url,
                "last_sale": last_sale,
                "key_stock_data": key_stock_dict
            }
            return nasdaq_data

        except Exception as e:
            print("Failed to process the request, Exception:%s" % (e))


if __name__ == "__main__":

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    #argparser = argparse.ArgumentParser()
    #argparser.add_argument('ticker', help='Company stock symbol')
    #args = argparser.parse_args()

    with open('out.csv', 'a+') as fileout:
        out = 'vTicker' + ';' + 'vName' + ';' + 'vPrice' + ';' + 'vTarget' + ';' + 'vPE' + ';' + 'vFPE' \
              + 'vYield' + ';' + 'vMax' + ';' + 'vMin' + ';' + 'vK1' + ';' + 'vK2' \
              + ';' + 'vK2' + ';' + 'vK3' + ';' + 'vK4' + ';' + 'vK5' + ';' + 'vSum' + '\n'
        fileout.write(out)

    with open('stoks.csv', 'r') as file:
        for line in file:

            line = re.sub(r"[^A-Za-z]+", '', line)
#            print(line)
            ticker = line
#            print("Fetching data for %s" % (ticker))
            scraped_data = parse_finance_page(ticker)
            #print("Writing scraped data to output file")
            #print (scraped_data)

            vName = scraped_data['company_name']
            vTicker = scraped_data['ticker']
            vPrice = float(re.sub("[^\d\.]", "", scraped_data['last_sale'][0]))
            try:
                vTarget = float(scraped_data['key_stock_data']['1 Year Target'])
            except:
                vTarget = vPrice
            try:
                vPE = float(scraped_data['key_stock_data']['P/E Ratio'])
            except:
                vPE = 30
            try:
                vFPE = float(scraped_data['key_stock_data']['Forward P/E (1y)'])
            except:
                vFPE = vPE
            try:
                vYield = float(re.sub("[^\d\.]", "", scraped_data['key_stock_data']['Current Yield']))
            except:
                vYield = 0
            vMaxMin = scraped_data['key_stock_data']['52 Week High / Low']
            lMaxMin = vMaxMin.split("/")
            try:
                vMax = float(re.sub("[^\d\.]", "", lMaxMin[0]))
            except:
                vMax = 0
            try:
                vMin = float(re.sub("[^\d\.]", "", lMaxMin[1]))
            except:
                vMin = 0

#            print("vName   :" + vName)
#            print("vTicker :" + vTicker)
#            print("vPrice  :" + str(vPrice))
#            print("vTarget :" + str(vTarget))
#            print("vPE     :" + str(vPE))
#            print("vFPE    :" + str(vFPE))
#            print("vYield  :" + str(vYield))
#            print("vMax    :" + str(vMax))
#            print("vMin    :" + str(vMin))
#            print("-------------------")

            vK1 = ((vTarget - vPrice)/(vPrice/100))*0.02
            if vK1 > 2:
                vK1 = 2
            if vK1 < 0:
                vK1 = 0
            vK2 = (vYield-2)*(0.5/8)
            if vK2 > 0.5:
                vK2 = 0.5
            if vK2 < 0:
                vK2 = 0
            vK3 = 1 - (vPE - 5 * (1 / 15))
            if vK3 > 1:
                vK3 = 1
            if vK3 < 0:
                vK3 = 0
            vK4 = 0.5 - (vFPE-5*(1/30))
            if vK4 > 0.5:
                vK4 = 0.5
            if vK4 < 0:
                vK4 = 0

            v1 = vPrice - (vMin + (vMax-vMin) * 0.5)
            if v1 < 0:
                v1 = v1 * -1
            v2 = (vMax-vMin)*0.5*0.01
            vK5 = 1 - ((v1/v2)*0.01)

            vSum = vK1 + vK2 + vK3 + vK4 + vK5

#            print("K1:     :", vK1)
#            print("K2:     :", vK2)
#            print("K3:     :", vK3)
#            print("K4:     :", vK4)
#            print("K5:     :", vK5)
#            print("v1  :", v1)
#            print("v2  :", v2)
#            print("Summ    :", vSum)

            with open('out.csv', 'a+') as fileout:
                out = vTicker + ';' + vName + ';' + str(vPrice) + ';' + str(vTarget) + ';' + str(vPE) + ';' + str(vFPE)\
                      + str(vYield) + ';' + str(vMax) + ';' + str(vMin) + ';' + str(vK1) + ';' + str(vK2) \
                      + ';' + str(vK2) + ';' + str(vK3) + ';' + str(vK4) + ';' + str(vK5) + ';' + str(vSum) + '\n'
                print(out)
                fileout.write(out)