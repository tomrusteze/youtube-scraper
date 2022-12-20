from flair.models import TextClassifier
from flair.data import Sentence

from pattern.en import parse
from pattern.en import pprint
from pattern.en import sentiment

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re
import os
import warnings
import nltk
import json
import csv
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from nltk.sentiment.vader import SentimentIntensityAnalyzer
warnings.filterwarnings("ignore")
pd.set_option('display.max_columns',None)

from sklearn import preprocessing
from sklearn import linear_model
from sklearn.metrics import mean_squared_error, r2_score

nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('vader_lexicon')
nltk.download('omw-1.4')

wnl = WordNetLemmatizer()

def tokenize_comment(sentence):
    return ' '.join([wnl.lemmatize(word) for word in sentence.split() if word not in set(stopwords.words('english'))])

def flair_prediction(x):
    sentence = Sentence(x)
    sia.predict(sentence)
    if "POSITIVE" in str(sentence):
        return sentence.score
    elif "NEGATIVE" in str(sentence):
        return -sentence.score
    else:
        return 0


if __name__ == '__main__':
    
    sentiment_library = "Pattern" #"NLTK" #Flair
    output_dir = "preprocessed"
    comments_1_file = 'output/UScomments_1_short.csv'
    videos_1_file = 'output/USvideos_1.csv'

    comments_1 = pd.read_csv(comments_1_file, error_bad_lines=False)
    videos_1 = pd.read_csv(videos_1_file, error_bad_lines=False)

    comments_1['comment_text_processed'] = comments_1['comment_text']
    comments_1['comment_text_processed'] = comments_1['comment_text_processed'].str.replace("[^a-zA-Z#]", " ")
    comments_1['comment_text_processed'] = comments_1['comment_text_processed'].apply(lambda x: ' '.join([w for w in x.split() if len(w)>3]))
    comments_1['comment_text_processed'] = comments_1['comment_text_processed'].apply(lambda x:x.lower())
    comments_1['comment_text_processed'] = comments_1['comment_text_processed'].apply(tokenize_comment)

    # Pattern
    print("Pattern analysis")
    comments_1['Sentiment Pattern'] = comments_1['comment_text'].apply(lambda x: sentiment(x)[0])

    # Flair
    print("Flair analysis")
    sia = TextClassifier.load('en-sentiment')
    comments_1['Sentiment Flair'] = comments_1["comment_text"].apply(flair_prediction)

    # NLTK
    print("NLTK analysis")
    sia_2 = SentimentIntensityAnalyzer()
    comments_1['Sentiment NLTK'] = comments_1['comment_text_processed'].apply(lambda x:sia_2.polarity_scores(x)['compound'])


    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    comments_1.to_csv(f"{output_dir}/comments_1_short_processed.csv", encoding='utf-8', index=False, quotechar='"', quoting=csv.QUOTE_NONNUMERIC)

    exit()
    #print("Old dataset videos shape:", videos_1.shape, "and comments:", comments_1.shape)
    
    # Perform Sentiment Analysis using the Pattern Library on all comments
    if sentiment_library == "Pattern":
        # Dataset 1
        comments_1['Sentiment Scores'] = comments_1['comment_text'].apply(lambda x: sentiment(x))
        comments_1['Sentiment Subjectivity'] = comments_1['Sentiment Scores'].apply(lambda x: x[1])
        comments_1['Sentiment Scores'] = comments_1['Sentiment Scores'].apply(lambda x: x[0])
 
    # NLTK Library
    if sentiment_library == "NLTK":
        comments_1.dropna(inplace=True)
        comments_1 = comments_1.reset_index().drop('index',axis=1)
        comments_1.likes = comments_1.likes.astype(int)
        comments_1.replies = comments_1.replies.astype(int)
        comments_1['comment_text_original'] = comments_1['comment_text']
        comments_1['comment_text'] = comments_1['comment_text'].str.replace("[^a-zA-Z#]", " ")
        comments_1['comment_text'] = comments_1['comment_text'].apply(lambda x: ' '.join([w for w in x.split() if len(w)>3]))
        comments_1['comment_text'] = comments_1['comment_text'].apply(lambda x:x.lower())


        wnl = WordNetLemmatizer()
        comments_1['comment_text'] = comments_1['comment_text'].apply(tokenize_comment)

        sia = SentimentIntensityAnalyzer()
        comments_1['Sentiment Scores'] = comments_1['comment_text'].apply(lambda x:sia.polarity_scores(x)['compound'])

    # Flair Library
    if sentiment_library == "Flair":
        sia = TextClassifier.load('en-sentiment')
        comments_1["Sentiment Scores"] = comments_1["comment_text"].apply(flair_prediction)

    comments_1['Sentiment'] = comments_1['Sentiment Scores'].apply(lambda s : 'Positive' if s > 0 else ('Neutral' if s == 0 else 'Negative'))
    print("Dataset 1: \n", comments_1.Sentiment.value_counts())

    # Calculate sentiment scores per video on dataset 1
    v_comments = {'nr_comments': [], 'nr_comments_neutral': [], 'nr_comments_positive': [], 'nr_comments_negative': [], 'sentiment': [], 'sentiment_positive': [], 'sentiment_negative': []}
    for v in videos_1.video_id:
        v_nr_comments = comments_1[comments_1.video_id == v].count()[0]
        v_nr_comments_neutral = comments_1[(comments_1.video_id == v) & (comments_1.Sentiment == 'Neutral')].count()[0]
        v_nr_comments_positive = comments_1[(comments_1.video_id == v) & (comments_1.Sentiment == 'Positive')].count()[0]
        v_nr_comments_negative = comments_1[(comments_1.video_id == v) & (comments_1.Sentiment == 'Negative')].count()[0]
        v_sentiment_positive = comments_1[(comments_1.video_id == v) & (comments_1.Sentiment == 'Positive')]['Sentiment Scores'].sum()
        v_sentiment_negative = comments_1[(comments_1.video_id == v) & (comments_1.Sentiment == 'Negative')]['Sentiment Scores'].sum()
        v_sentiment = comments_1[comments_1.video_id == v]['Sentiment Scores'].sum()
        v_comments['nr_comments'].append(v_nr_comments)
        v_comments['nr_comments_neutral'].append(v_nr_comments_neutral)
        v_comments['nr_comments_positive'].append(v_nr_comments_positive)
        v_comments['nr_comments_negative'].append(v_nr_comments_negative)
        v_comments['sentiment'].append(v_sentiment)
        v_comments['sentiment_positive'].append(v_sentiment_positive)
        v_comments['sentiment_negative'].append(v_sentiment_negative)

    videos_1['sentiment'] = v_comments['sentiment']
    videos_1['sentiment_positive'] = v_comments['sentiment_positive']
    videos_1['sentiment_negative'] = v_comments['sentiment_negative']

    videos_1['comment_retrieved'] = v_comments['nr_comments']
    videos_1['comment_neutral'] = v_comments['nr_comments_neutral']
    videos_1['comment_positive'] = v_comments['nr_comments_positive']
    videos_1['comment_negative'] = v_comments['nr_comments_negative']

    videos_1['sentiment_per_comment'] = videos_1['sentiment'] / videos_1['comment_retrieved']
    videos_1['positive_sentiment_per_comment'] = videos_1['sentiment_positive'] / videos_1['comment_positive']
    videos_1['negative_sentiment_per_comment'] = videos_1['sentiment_negative'] / videos_1['comment_negative']
    videos_1['sentiment_per_non_neutral_comment'] = videos_1['sentiment'] / (videos_1['comment_retrieved'] - videos_1['comment_neutral'])

    # Remove videos with less than 500 comments
    videos_1 = videos_1[videos_1.comment_retrieved > 500]

    # Remove videos with 0 dislikes (this never happens in practice, so it must be an error)
    videos_1 = videos_1[videos_1.dislikes > 0]
    print("New shape of old dataset:", videos_1.shape)

    print("Dataset 1 Sentiment scores:")
    print("Average sentiment on dataset per video", videos_1['sentiment'].sum()/videos_1.count()[0])
    print("Average sentiment on dataset per comment", videos_1['sentiment_per_comment'].sum()/videos_1.count()[0])
    print("Average non-neutral sentiment on dataset per video per comment", videos_1['sentiment_per_non_neutral_comment'].sum()/videos_1.count()[0])
    
    # Save to file
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    videos_1.to_csv(f"{output_dir}/videos_1_processed_{sentiment_library}.csv", encoding='utf-8', index=False, quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
    comments_1.to_csv(f"{output_dir}/comments_1_processed_{sentiment_library}.csv", encoding='utf-8', index=False, quotechar='"', quoting=csv.QUOTE_NONNUMERIC)