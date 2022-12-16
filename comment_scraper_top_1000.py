"""
By Tom Rust
GitHub : https://github.com/tomrusteze

The script is based on https://github.com/egbertbouman/youtube-comment-downloader and https://github.com/ahmedshahriar/youtube-comment-scraper

By default, the script will download most recent 100 comments
You can change the default filter (line 33 onwards)
Variables :
COMMENT_LIMIT : How many comments you want to download 
SORT_BY_POPULAR : filter comments by popularity (0 for True , 1 for false)
SORT_BY_RECENT : filter comments by recently posted (0 for True , 1 for false)
"""

import pandas as pd
import json
import os
import sys
import re
import time
import csv
import requests

from video_scraper import prepare_feature

# pandas dataframe display configuration
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

YOUTUBE_COMMENTS_AJAX_URL = 'https://www.youtube.com/comment_service_ajax'

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'

# set parameters
# filter comments by popularity or recent, 0:False, 1:True
SORT_BY_POPULAR = 0
# default recent
SORT_BY_RECENT = 0
# set comment limit
COMMENT_LIMIT = 100

YT_CFG_RE = r'ytcfg\.set\s*\(\s*({.+?})\s*\)\s*;'
YT_INITIAL_DATA_RE = r'(?:window\s*\[\s*["\']ytInitialData["\']\s*\]|ytInitialData)\s*=\s*({.+?})\s*;\s*(?:var\s+meta|</script|\n)'


def regex_search(text, pattern, group=1, default=None):
    match = re.search(pattern, text)
    return match.group(group) if match else default


def ajax_request(session, endpoint, ytcfg, retries=5, sleep=20):
    url = 'https://www.youtube.com' + endpoint['commandMetadata']['webCommandMetadata']['apiUrl']

    data = {'context': ytcfg['INNERTUBE_CONTEXT'],
            'continuation': endpoint['continuationCommand']['token']}

    for _ in range(retries):
        response = session.post(url, params={'key': ytcfg['INNERTUBE_API_KEY']}, json=data)
        if response.status_code == 200:
            return response.json()
        if response.status_code in [403, 413]:
            return {}
        else:
            print(response.status_code)
            time.sleep(sleep)


def clean_number(number):
    return int(str(number).replace("K","000").replace(',',''))
    

def download_comments(YOUTUBE_VIDEO_URL, video_id, sort_by=SORT_BY_RECENT, language=None, sleep=0.1):
    session = requests.Session()
    session.headers['User-Agent'] = USER_AGENT
    session.cookies.set('CONSENT', 'YES+cb', domain='.youtube.com')
    
    response = session.get(YOUTUBE_VIDEO_URL)

    if 'uxe=' in response.request.url:
        session.cookies.set('CONSENT', 'YES+cb', domain='.youtube.com')
        response = session.get(YOUTUBE_VIDEO_URL)

    html = response.text
    ytcfg = json.loads(regex_search(html, YT_CFG_RE, default=''))
    if not ytcfg:
        return  # Unable to extract configuration
    if language:
        ytcfg['INNERTUBE_CONTEXT']['client']['hl'] = language

    data = json.loads(regex_search(html, YT_INITIAL_DATA_RE, default=''))
    section = next(search_dict(data, 'itemSectionRenderer'), None)
    renderer = next(search_dict(section, 'continuationItemRenderer'), None) if section else None
    if not renderer:
        # Comments disabled?
        return

    needs_sorting = sort_by != SORT_BY_POPULAR
    continuations = [renderer['continuationEndpoint']]
    while continuations:
        continuation = continuations.pop()
        response = ajax_request(session, continuation, ytcfg)

        if not response:
            break

        error = next(search_dict(response, 'externalErrorMessage'), None)
        if error:
            raise RuntimeError('Error returned from server: ' + error)

        actions = list(search_dict(response, 'reloadContinuationItemsCommand')) + \
                    list(search_dict(response, 'appendContinuationItemsAction'))
        for action in actions:
            for item in action.get('continuationItems', []):
                if action['targetId'] in ['comments-section', 'engagement-panel-comments-section']:
                    # Process continuations for comments and replies.
                    continuations[:0] = [ep for ep in search_dict(item, 'continuationEndpoint')]
                if action['targetId'].startswith('comment-replies-item') and 'continuationItemRenderer' in item:
                    # Process the 'Show more replies' button
                    continuations.append(next(search_dict(item, 'buttonRenderer'))['command'])

        for comment in reversed(list(search_dict(response, 'commentRenderer'))):
            yield {#'cid': comment['commentId'],
                   'video_id': video_id,
                   'comment_text': ''.join([c['text'] for c in comment['contentText'].get('runs', [])]),
                   'likes': clean_number(comment.get('voteCount', {}).get('simpleText', '0')),
                   'replies': clean_number(comment.get('replyCount', 0)),
                   }

        time.sleep(sleep)


def search_dict(partial, search_key):
    stack = [partial]
    while stack:
        current_item = stack.pop()
        if isinstance(current_item, dict):
            for key, value in current_item.items():
                if key == search_key:
                    yield value
                else:
                    stack.append(value)
        elif isinstance(current_item, list):
            for value in current_item:
                stack.append(value)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} videos.csv LIMIT")
        exit()
    
    VIDEO_FILE = sys.argv[1]
    COMMENT_LIMIT = int(sys.argv[2])

    FILE_NAME = VIDEO_FILE.replace("video", "comment")
    if(FILE_NAME == VIDEO_FILE):
        FILE_NAME = "comments.csv"

    df_video_list = pd.read_csv(VIDEO_FILE, error_bad_lines=False)
    df_video_list = df_video_list.drop_duplicates(subset=['video_id']).sort_values(by=['views'], ascending=False).head(1000)
    
    video_data = list(zip(df_video_list["video_id"], df_video_list["title"]))

    if os.path.exists(FILE_NAME):
        os.remove(FILE_NAME)

    for video_id, video_title in video_data:
        try:
            df_comment = pd.DataFrame()
            youtube_url = "https://www.youtube.com/watch?v=" + video_id

            print('Downloading Youtube comments for video:', video_title)
            count = 0
            start_time = time.time()

            for comment in download_comments(youtube_url, video_id):
                df_comment = df_comment.append(comment, ignore_index=True)
                count += 1
                if COMMENT_LIMIT and count >= COMMENT_LIMIT:
                    break
            
            if not os.path.isfile(FILE_NAME):
                df_comment.to_csv(FILE_NAME, encoding='utf-8', index=False, quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
            else:  # else it exists so append without writing the header
                df_comment.to_csv(FILE_NAME, mode='a', encoding='utf-8', index=False, header=False,quotechar='"', quoting=csv.QUOTE_NONNUMERIC)

            print('[{:.2f} seconds] Done! \n'.format(time.time() - start_time))

        except Exception as e:
            print('Error:', str(e))
            sys.exit(1)

    # Print the new dataframe that corresponds to the comments
    df_video_list.to_csv(f"{VIDEO_FILE}_new.csv", encoding='utf-8', index=False, quotechar='"', quoting=csv.QUOTE_NONNUMERIC)