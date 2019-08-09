# -*- coding: utf-8 -*-
import scrapy
from scrapy import Spider, Request
# from selenium import webdriver
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.common.action_chains import ActionChains
import re
import pandas as pd
import numpy
import json
import math
import time
import requests


class SephoraSpidySpider(scrapy.Spider):
    name = 'sephora_spidy'
    allowed_urls = ["https://www.sephora.com", "https://api.bazaarvoice.com"]
    start_urls = ["https://www.sephora.com/brands-list"]

    def parse(self, response):
		#time.sleep(0.5)
		#this scrapes all of the brands
		#links = response.xpath('//a[@class="u-hoverRed u-db u-p1"]//@href').extract()
		#links = [x + "?products=all" for x in links]
		
		#brand_links = ["/fenty-beauty-rihanna", "/kiehls", "/lancome", "/estee-lauder", "/the-ordinary",
		#"/shiseido", "/sk-ii", "/clinique", "/benefit-cosmetics", "dr-jart", "/chanel", "/nars",
		#"/laneige", "/urban-decay", "/bobbi-brown"]
		#brand_links = response.css('a.css-d84rnc::attr(href)').extract()
		#brand_links = [x.replace('/brand', '') for x in brand_links]
		#self.df.to_csv('results.csv', encoding='utf-8')
		#df = pd.DataFrame(columns=['Product Name', 'Product UID', 'Brand Name', 'Review'])
        brand_links = ["/refa"]
        brand_links = [x + "?products=all" for x in brand_links]

		#this scrapes only the brands inside brand_links
        links = ["https://www.sephora.com" + link for link in brand_links]
        for url in links:
			#time.sleep(0.5)
            yield Request(url, callback=self.parse_product)
		# print('PRINTING DF')
		# print(self.df)
		# print('')
    def parse_product(self, response):
		
        product_urls = response.css('a.css-ix8km1::attr(href)').extract()
        product_names = response.css('a.css-ix8km1::attr(aria-label)').extract()
        product_uid = response.css('a.css-ix8km1::attr(data-uid)').extract()
        p_brand_names = response.css('span.css-ktoumz::text').extract()
		#product_dict = {'Product URLS': product_urls, 'Product Names': product_names, 'Product UID': product_uid}
		#product_urls = response.css('a.css-ix8km1::attr(href)').extract()
		# dictionary = response.xpath('//script[@id="searchResult"]/text()').extract()
		# dictionary = re.findall('"products":\[(.*?)\]', dictionary[0])[0]

		# product_urls = re.findall('"product_url":"(.*?)",', dictionary)
		# product_names = re.findall('"display_name":"(.*?)",', dictionary)
		# product_ids = re.findall('"id":"(.*?)",', dictionary)
		# ratings = re.findall('"rating":(.*?),', dictionary)
		# brand_names = re.findall('"brand_name":"(.*?)",', dictionary)
		##list_prices = re.findall('"list_price":(.*?),', dictionary)

        individual_products_urls = ["https://www.sephora.com" + link for link in product_urls]

        # print('')
        # print('TOTAL PRODUCTS')
        # print(len(individual_products_urls))
        # print('')
        # if len(product_urls)!=len(ratings)!=len(brand_names):
        # 	print('Number of products do not match with ratings')

        product_df = pd.DataFrame({'individual_products_urls': individual_products_urls,
        'product_names': product_names,'product_uid': product_uid, 'p_brand_names': p_brand_names})

        # print (product_df.head())
        # print (list(product_df.index))

        for n in list(product_df.index):
            product = product_df.loc[n, 'product_names']
            p_uid = product_df.loc[n, 'product_uid']
            brand_name = product_df.loc[n, 'p_brand_names']

            print ('individual' + product_df.loc[n,'individual_products_urls'])

            # yield SplashRequest(product_df[n, 'individual_product_urls'], callback=self.parse_detail, meta={product})
        
            yield Request(product_df.loc[n,'individual_products_urls'], callback=self.parse_detail, 
            meta={'product': product, 'p_uid':p_uid, 'brand_name':brand_name},)
            
    def request_reviews(self, api_url, offset):
        print(api_url)
        return requests.get(api_url.format(offset))

    def parse_detail(self, response):
        #time.sleep(0.5)
        product = response.meta['product']
        p_uid = response.meta['p_uid'].split(' ')[0]
        brand_name = response.meta['brand_name']

        
        review_link = 'https://api.bazaarvoice.com/data/reviews.json?apiversion=5.4&passkey=rwbw526r2e7spptqd2qzbkp7&Filter=ProductId:{}'.format(p_uid) + '&Include=Products&Stats=Reviews&Limit=100'
        
        yield Request(review_link, callback=self.parse_reviews, 
            meta={'product': product, 'p_uid':p_uid, 'brand_name':brand_name},)

    def parse_reviews(self, response):
        print(response.meta)
        print('RESPONSE HEADERS')
        print(response.headers)
        print('')
        product = response.meta['product']
        p_uid = response.meta['p_uid'].split(' ')[0]
        brand_name = response.meta['brand_name']
        limit = 100
        offset = 0

        review_link = response.url + '&Offset={}'.format(offset)
        all_reviews = []
        #review_link = self.request_reviews(review_link, offset=offset)
        info = requests.get(review_link).json()

        theList = info['Includes']['Products']
        all_upcs = []
        for product in theList: 
            all_upcs += theList[product]['UPCs']

        totalNum = info['TotalResults']
        while offset < totalNum:
            all_reviews += info['Results']
            offset += limit
            review_link.format(offset)
            #review_link = self.request_reviews(review_link, offset=offset)
            #print(response.headers['X-Bazaarvoice-QPM-Current'])
            info = requests.get(review_link).json()
            time.sleep(1)
        dictionary_data = []
        for review in all_reviews:
            print('review')
            dictionary_info = {'product': product,'p_uid': p_uid, 'brand_name': brand_name, 'UPCs': all_upcs,
            'Reviews': review}
            dictionary_data.append(dictionary_info)
        with open('reviews.json', 'a') as fout:
            print('json')
            json.dump(dictionary_data, fout)
        # p_num_reviews = response.xpath('//span[@class="css-mzsag6"]/text()').extract()
        # print('')
        # print('TYPE REVIEWS')
        # print(len(p_num_reviews))
        # print('')
        # p_num_reviews = p_num_reviews[0]
        # p_num_reviews = p_num_reviews.replace('s', '')
        # p_num_reviews = p_num_reviews.replace(' review', '')
        # p_num_reviews = int(p_num_reviews)



    # def parse_reviews(self, response):
    # 	dictionary_data = []
        
    # 	product = response.meta['product']
    # 	p_uid = response.meta['p_uid']
    # 	brand_name = response.meta['brand_name']
    # 	p_num_reviews = response.meta['p_num_reviews']
    # 	data = json.loads(response.text)
    # 	reviews = data['Results']

    # 	for review in reviews:
    # 		item = SephoraItem()
    # 		item['product'] = product
    # 		item['p_id'] = p_uid
    # 		item['brand_name'] = brand_name
    # 		item['p_num_reviews'] = p_num_reviews
            
    # 		try:
    # 			r_review = review['ReviewText']
    # 		except:
    # 			r_review = None
    # 		dictionary_info = {'Product Name': product,'Product UID': p_uid, 'Brand Name': brand_name, 
    #         'Reviews': r_review}
    # 		dictionary_data.append(dictionary_info)
            
    # 		yield item
    # 	with open('reviews.json', 'a') as fout:
    # 		    json.dump(dictionary_data , fout)



        # driver = webdriver.Chrome()
        # driver.get(response.url)
        
        # button = driver.find_element_by_class_name('css-zea1jq')
        # ActionChains(driver).move_to_element(button).send_keys(Keys.ESCAPE).perform()

        # #body = driver.find_element_by_tag_name('html').get_attribute('innerHTML')
        # driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2.5);")
        # time.sleep(1)
        # more_reviews_flag = True
        # while(more_reviews_flag):
        # 	try:
        # 		read_more_reviews = driver.find_element_by_class_name('css-1phfyoj')
        # 		read_more_reviews.click()
        # 		driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 3);")
        # 	except:
        # 		print('in except')
        # 		more_reviews_flag = False

        # reviews = driver.find_elements_by_class_name('css-1p4f59m')
        # read_mes = driver.find_elements_by_class_name('css-xq9yyh')
        
        # try:
        # 	driver.execute_script("document.getElementById('divToky').style.display = 'none';")
        # except:
        # 	pass

        # for i in range(0, len(read_mes)):
        # 	read_mes[i].click()
        # for i in range(0, len(reviews)):
        # 	print(reviews[i].get_attribute('innerHTML'))
        # 	print("")

        # print('LEN OF REVIEWS')
        # print(len(reviews))


        # dictionary_data = []
        # for i in range(0, len(reviews)):
        # 	dictionary_info = {'Product Name': product,'Product UID': p_uid, 'Brand Name': brand_name, 
        # 	'Reviews': reviews[i].get_attribute('innerHTML')}
        # 	dictionary_data.append(dictionary_info)
        # with open('reviews.json', 'a') as fout:
        # 	json.dump(dictionary_data , fout)
            #df = pd.DataFrame.from_dict(dictionary_info.items())
            #self.df.append([product, p_uid, brand_name, reviews[i].get_attribute('innerHTML')])
            # df['Product Name'] = product
            # df['Product UID'] = p_uid
            # df['Brand Name'] = brand_name
            # df['Review'] = reviews[i].get_attribute('innerHTML')
            # df = pd.DataFrame(dictionary_info.items())

            # print('DATA FRAME ITEMS')
            # print(self.df)
            # with open('reviews.csv', 'a') as outfile:
            # 	for key in dictionary_info.keys():
            # 		outfile.write("%s,%s\n"%(key,dictionary_info[key]))
            # with open('reviews.txt', 'w') as outfile:
            # 	json.dump(dictionary_info, outfile)
            
            # print('DICTIONARY')
            # print(dictionary_info)
            # print('')
            # df = df.append(dictionary_info, ignore_index=True)
            # print('DATA FRAME')
            # print(df)
            # print('')
        # 	# print("")
        
        # print('')
        # print('PRODUCT parse detail')
        # print(product)
        # print(p_uid)
        # print(brand_name)
        # print('')

        # driver.quit()
        
        # product_df = pd.DataFrame()
        # print('PRODUCT DF')
        # print(product_df)
        # print('')
        # product_df.to_csv('results.csv', index=False, encoding='utf-8')
        
        
    #	p_category = response.xpath('//a[@class="css-u2mtre"]/text()').extract_first()

    # 	try:
    # 		p_price = response.xpath('//div[@class="css-18suhml"]/text()').extract()
    # 		p_price = p_price[0]
    # 	except:
    # 		p_price = None

    # 	p_num_reviews = response.xpath('//span[@class="css-1dz7b4e"]/text()').extract()
    # 	p_num_reviews = p_num_reviews[0]
    # 	p_num_reviews = p_num_reviews.replace('s', '')
    # 	p_num_reviews = p_num_reviews.replace(' review', '')
    # 	p_num_reviews = int(p_num_reviews)

    # 	print ('Number of reviews: {}'.format(p_num_reviews))

    # 	#create code here that creates a list of urls for calling the reviews
    # 	#you will use p_num_reviews, use the "{}".format technique

    # 	#max_n = math.ceil(p_num_reviews/30)
    # 	#low_range = [x*30 for x in list(range(0,max_n))]
    # 	#up_range = [x*30 for x in list(range(1,max_n+1))]

        # links3 = ['https://api.bazaarvoice.com/data/reviews.json?Filter=ProductId%3A' +
        # 	p_uid + '&Sort=Helpfulness%3Adesc&Limit=' + 
        # 	'{}&Offset={}&Include=Products%2CComments&'.format(min(len(reviews), int(100)), 0) +
        # 	'Stats=Reviews&passkey=rwbw526r2e7spptqd2qzbkp7&apiversion=5.4']
        # print('CREATE LINKS3')
        # for url in links3:
        # 	#time.sleep(0.5)
        # 	print('in for loop for links3')
        # 	yield Request(url, callback=self.parse_reviews,
        # 		meta={'product': product, 'p_uid':p_uid, 'brand_name':brand_name,
        # 		'p_num_reviews':len(reviews)})

    # def parse_reviews(self, response):
    # 	#time.sleep(0.5)
    # 	print('parse_reviews')
        # product = response.meta['product']
        # p_uid = response.meta['p_uid']
    # 	# p_star = response.meta['p_star']
    # 	brand_name = response.meta['brand_name']
    # 	# p_price = response.meta['p_price']
    # 	# p_category = response.meta['p_category']
    # 	p_num_reviews = response.meta['p_num_reviews']
        
    # 	data = json.loads(response.text)
    # 	print('RESPONSES.TEXT')
    # 	print(response.text)
    # 	print('')

    # # 	print('REVIEWS DATA')
        
    # # 	#check keys
    # # 	#data.keys()
    # 	reviews = data['Results'] #this is a list
    # 	print(reviews)

    # 	print('')

    #     dictionary_data = []

    #     for review in reviews:
    #         item = SephoraItem()
    #         item['product'] = product
    #         item['p_id'] = p_uid
    #         item['brand_name'] = brand_name
    #         item['p_num_reviews'] = p_num_reviews
            
    #         try:
    # 			r_review = review['ReviewText']
    # 		except:
    # 			r_review = None

    #         dictionary_info = {'Product Name': product,'Product UID': p_uid, 'Brand Name': brand_name, 
    #         'Reviews': r_review}
    #         dictionary_data.append(dictionary_info)
    # 	    with open('reviews.json', 'a') as fout:
    # 		    json.dump(dictionary_data , fout)
    # 		yield item
    # 	print ('='*50)
    # 	print ('TOTAL NUMBER OF REVIEWS: {}'.format(int(p_num_reviews)))
    # 	print ('NUMBER OF REVIEWS TO BE PULLED: {}'.format(len(reviews)))
    # 	print ('ACTUAL NUMBER PULLED {}'.format(n_count))
    # 	print ('TOTAL NUMBER PULLED {}'.format(n_count_tot))
    # 	print ('='*50)







    # # 	#each element inside reviews is a dictionary
    # # 	#tmp[0].keys() will give the keys of the dictionaries inside reviews

    # # 	#create code here which arranges the data from the json dictionary into a dataframe

    # # 	n_count = 0
    # # 	global n_count_tot
    #     # for review in reviews:
    #     #     item=SephoraItem()
    # # 		try:
    # # 			reviewer = review['UserNickname']
    # # 		except:
    # # 			reviewer = None
    # # 		try:
    # # 			r_star = review['Rating']
    # # 		except:
    # # 			r_star = None

    # # 		try:
    # # 			r_eyecolor = review['ContextDataValues']['eyeColor']['Value']
    # # 		except:
    # # 			r_eyecolor = None

    # # 		try:
    # # 			r_haircolor = review['ContextDataValues']['hairColor']['Value']
    # # 		except:
    # # 			r_haircolor = None

    # # 		try:
    # # 			r_skintone = review['ContextDataValues']['skinTone']['Value']
    # # 		except:
    # # 			r_skintone = None

    # # 		try:
    # # 			r_skintype = review['ContextDataValues']['skinType']['Value']
    # # 		except:
    # # 			r_skintype = None
    # # 		try:
    # # 			r_skinconcerns = review['ContextDataValues']['skinConcerns']['Value']
    # # 		except:
    # # 			r_skinconcerns = None

    # # 		try:
    # # 			r_review = review['ReviewText']
    # # 		except:
    # # 			r_review = None

    # # 		#need to create an error handler for empty data for reviews

    # # 		print ('BRAND: {} PRODUCT: {}'.format(brand_name, product))
    # # 		print ('ID: {}'.format(reviewer))
    # # 		print ('='*50)


            
    #         # item['product'] = product

    # 		# item['p_uid'] = p_uid
    # 		# #item['p_star'] = p_star
    # 		# item['brand_name'] = brand_name
    # 		# #item['p_price'] = p_price
    # 		# #item['p_category'] = p_category
    # 		# item['p_num_reviews'] = p_num_reviews 

    # # 		#all of these needs to be taken from the reviews list/dictionary

    # # 		item['reviewer'] = reviewer
    # # 		item['r_star'] = r_star
    # # 		item['r_eyecolor'] = r_eyecolor
    # # 		item['r_haircolor'] = r_haircolor
    # # 		item['r_skintone'] = r_skintone
    # # 		item['r_skintype'] = r_skintype
    # # 		item['r_skinconcerns'] = r_skinconcerns
    # # 		item['r_review'] = r_review

    # # 		#time.sleep(0.025)
    # # 		n_count += 1
    # #		n_count_tot += 1



