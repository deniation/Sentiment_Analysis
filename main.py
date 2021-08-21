from flask import Flask, jsonify
from bs4 import BeautifulSoup
from flask_restful import Api, Resource
from flask_cors import CORS
from nltk import word_tokenize
from nltk.corpus import stopwords
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import requests
import string
import pandas as pd

app = Flask(__name__)
CORS(app)
api = Api(app)

amazon_url = 'https://www.jumia.co.ke/womens-skirts/'
reviews_url = 'https://www.jumia.co.ke/catalog/productratingsreviews/sku/'
headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"}

response = requests.get(amazon_url, headers=headers)

soup = BeautifulSoup(response.content, 'lxml')

items = soup.find_all('article', {'class': 'prd _fb col c-prd'})

all_product_data = {}
content_list = []

product_sentiment = ''


def sentiment_analyse(sentiment_text):
    score = SentimentIntensityAnalyzer().polarity_scores(sentiment_text)
    neg = score['neg']
    pos = score['pos']
    if neg > pos:
        sentiment = 'Negative Sentiment'
    elif neg < pos:
        sentiment = 'Positive Sentiment'
    else:
        sentiment = 'Neutral Sentiment'
    return sentiment

def Merge(dict_one, dict_two):
    result = {**dict_one, **dict_two}
    return result

for item_list in items:
    product_data = {}
    ids = item_list.a

    pid = ids['data-id']
    uli = item_list.find('a', href=True)

    res = requests.get('https://www.jumia.co.ke' + uli['href'], headers=headers)
    res_soup = BeautifulSoup(res.content, 'lxml')
    if not res_soup.find('p', {'class': '-fs16 -ptl -m'}):
        image = item_list.find('img', {'class': 'img'})
        product_image = image['data-src']

        product_data['product_id'] = pid
        product_data['product_image'] = product_image
        product_data['product_name'] = item_list.find('h3', {'class': 'name'}).text.strip()
        product_data['product_price'] = item_list.find('div', {'class': 'prc'}).text.strip()

        review_req = requests.get('https://www.jumia.co.ke/catalog/productratingsreviews/sku/' + pid + '/',
                                  headers=headers)
        review_soup = BeautifulSoup(review_req.content, 'lxml')

        reviews = review_soup.find_all('article', {'class': '-pvs -hr _bet'})

        for review in reviews:
            review_text = review.find('p', {'class': '-pvs'}).text.strip()
            lowercase_reviews = review_text.lower()
            cleaned_reviews = lowercase_reviews.translate(str.maketrans('', '', string.punctuation))
            # tokenized_reviews = cleaned_reviews.split()
            tokenized_reviews = word_tokenize(cleaned_reviews, "english")
            final_words = []
            for word in tokenized_reviews:
                if word not in stopwords.words('english'):
                    final_words.append(word)

            product_sentiment = sentiment_analyse(cleaned_reviews)

        product_data['sentiment'] = product_sentiment
        content_list.append(product_data)

        # print('https://www.jumia.co.ke' + uli['href'])

class SentimentAnalysis(Resource):
    def get(self):
        # print(product_data)
        return content_list


api.add_resource(SentimentAnalysis, "/sentiment")

if __name__ == '__main__':
    app.run(debug=True)
