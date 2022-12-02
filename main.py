import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re
import os
import warnings
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from nltk.sentiment.vader import SentimentIntensityAnalyzer
warnings.filterwarnings("ignore")

#nltk.download('stopwords')
#nltk.download('wordnet')
nltk.download('vader_lexicon')

if __name__ == '__main__':
    pd.set_option('display.max_columns',None)
    # Load data
    US_comments = pd.read_csv('data/kaggle/UScomments.csv', error_bad_lines=False)
    US_videos = pd.read_csv('data/kaggle/USvideos.csv', error_bad_lines=False)

    # Clean comment data
    US_comments.dropna(inplace=True)
    US_comments.drop(41587, inplace=True)
    US_comments = US_comments.reset_index().drop('index',axis=1)
    US_comments.likes = US_comments.likes.astype(int)
    US_comments.replies = US_comments.replies.astype(int)
    US_comments['comment_text'] = US_comments['comment_text'].str.replace("[^a-zA-Z#]", " ")
    US_comments['comment_text'] = US_comments['comment_text'].apply(lambda x: ' '.join([w for w in x.split() if len(w)>3]))
    US_comments['comment_text'] = US_comments['comment_text'].apply(lambda x:x.lower())

    tokenized_comment = US_comments['comment_text'].apply(lambda x: x.split())
    wnl = WordNetLemmatizer()
    tokenized_comment.apply(lambda x: [wnl.lemmatize(i) for i in x if i not in set(stopwords.words('english'))])
    for i in range(len(tokenized_comment)):
        tokenized_comment[i] = ' '.join(tokenized_comment[i])
    US_comments['comment_text'] = tokenized_comment

    sia = SentimentIntensityAnalyzer()
    US_comments['Sentiment Scores'] = US_comments['comment_text'].apply(lambda x:sia.polarity_scores(x)['compound'])
    US_comments['Sentiment'] = US_comments['Sentiment Scores'].apply(lambda s : 'Positive' if s > 0 else ('Neutral' if s == 0 else 'Negative'))
    print(US_comments.Sentiment.value_counts())
