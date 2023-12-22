import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from flask import Flask, request, render_template

app = Flask(__name__, static_url_path='/static')                                                         # Create an instance of flask


client = MongoClient("localhost", 27017)                                                                 # Database connectivity
database = client['Books']                                                                               # Create a new database
collection = database['reviews']                                                                         # Create a new collection in the database
def process(page_url):
    html = requests.get(page_url)                                                                        # Gets the HTML of the page
    soup = BeautifulSoup(html.text, 'html.parser')                                                       # Parses the html element
    try:
        book_image = soup.find('img', class_='workCoverImage')['src']                                    # Gets the URL of the book cover
    except:
        book_image = "https://t4.ftcdn.net/jpg/01/20/73/360_F_120736914_mvc0UMUrgebZ11izrwPjF6HsHdsXnr8P.jpg"
    book_name = soup.find('div', class_='headsummary')                                                    # Gets the name and author of the book
    bk = book_name.text.split("by")
    book_name = bk[0]
    book_author = bk[1]
    names = soup.find_all('div', class_='commentFooter')                                                  # Gets the name of the reviewer
    data = {}
    temp = []
    for name in names:
        temp.append(name.text)
    data["Names"] = temp
    data['Book Name'] = book_name
    temp = []
    pos = 0
    neg = 0
    neu = 0
    count = 0
    reviews = soup.find_all('div', class_="commentText brslop")            

    for review in reviews:
        temp.append(review.text)
        count += 1
        analyzer = SentimentIntensityAnalyzer()
        sentiment_scores = analyzer.polarity_scores(review.text)                                           # Sentimente Analyzer 
        pos += sentiment_scores['pos']
        neg += sentiment_scores['neg']
        neu += sentiment_scores['neu']
    ht = {}
    data["Reviews"] = temp
    # Calculate Percentage
    ht['positive'] = (round(pos/count, 4))*100
    ht['negative'] = (round(neg/count, 4))*100
    ht['neutral'] = (round(neu/count, 4))*100
    ht['image'] = book_image
    ht['book_name'] = book_name
    ht['book_author'] = book_author
    database.collection.insert_one(data)
    return ht


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/main', methods=['GET'])
def main():
    url = request.args.get('url')                                                                           # Get URL from Web Server
    ht = {}
    try:
        ht = process(url)
        return render_template('book.html', positive=ht['positive'], negative=ht['negative'], neutral=ht['neutral'],
                               url=ht['image'], name=ht['book_name'], author=ht['book_author'])
    except:
        return render_template('index.html', msg = "Sorry book reviews not found!")


if __name__ == '__main__':
    app.run()
