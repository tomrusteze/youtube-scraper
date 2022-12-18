"""
By Tom Rust
GitHub : https://github.com/tomrusteze

The script is based on https://github.com/sleepyeePanda/Trending-YouTube-Scraper
"""

import pandas as pd
import requests, sys, time, os, argparse, csv
# List of simple to collect features
snippet_features = ["title",
                    "publishedAt",
                    "channelTitle",
                    "categoryId"]

snippet_features_names = ["title",
                          "channel_title",
                          "category_id"]

PUBLISHED_AFTER = "2021-12-14T00:00:00Z"

# Any characters to exclude, generally these are things that become problematic in CSV files
unsafe_characters = ['\n', '"']

# Used to identify columns, currently hardcoded order
header = ["video_id"] + snippet_features_names + ["tags", "views", "likes", "dislikes",
                                            "comment_total", "thumbnail_link", "date"]


def setup(api_path, code_path):
    with open(api_path, 'r') as file:
        api_key = file.readline()

    with open(code_path) as file:
        country_codes = [x.rstrip() for x in file]

    return api_key, country_codes


def prepare_feature(feature):
    # Removes any character from the unsafe characters list and surrounds the whole item in quotes
    for ch in unsafe_characters:
        feature = str(feature).replace(ch, "")
    return f'"{feature}"'


def api_request_list(id_list, country_code):
    # Builds the URL and requests the JSON from it
    ids = ",".join(id_list)
    request_url = f"https://www.googleapis.com/youtube/v3/videos?part=id,statistics,snippet&id={ids}&regionCode={country_code}&key={api_key}"
    request = requests.get(request_url)
    if request.status_code == 429:
        print("Temp-Banned due to excess requests, please wait and continue later")
        sys.exit()
    return request.json()


def api_request(page_token, country_code):
    # Builds the URL and requests the JSON from it
    request_url = f"https://www.googleapis.com/youtube/v3/videos?part=id,statistics,snippet{page_token}chart=mostPopular&regionCode={country_code}&maxResults=50&key={api_key}"
    request = requests.get(request_url)
    if request.status_code == 429:
        print("Temp-Banned due to excess requests, please wait and continue later")
        sys.exit()
    return request.json()


def get_tags(tags_list):
    # Takes a list of tags, prepares each tag and joins them into a string by the pipe character
    return "|".join(tags_list)


def get_videos(items):
    lines = []
    for video in items:
        comments_disabled = False
        ratings_disabled = False

        # We can assume something is wrong with the video if it has no statistics, often this means it has been deleted
        # so we can just skip it
        if "statistics" not in video:
            continue

        # A full explanation of all of these features can be found on the GitHub page for this project
        video_id = video['id']

        # Snippet and statistics are sub-dicts of video, containing the most useful info
        snippet = video['snippet']
        statistics = video['statistics']

        # This list contains all of the features in snippet that are 1 deep and require no special processing
        #features = [prepare_feature(snippet.get(feature, "")) for feature in snippet_features]

        # The following are special case features which require unique processing, or are not within the snippet dict
        #description = snippet.get("description", "")
        thumbnail_link = snippet.get("thumbnails", dict()).get("default", dict()).get("url", "")
        #trending_date = time.strftime("%y.%d.%m")
        tags = get_tags(snippet.get("tags", ["[none]"]))
        view_count = statistics.get("viewCount", 0)

        # This may be unclear, essentially the way the API works is that if a video has comments or ratings disabled
        # then it has no feature for it, thus if they don't exist in the statistics dict we know they are disabled
        if 'likeCount' in statistics:
            likes = statistics['likeCount']
        else:
            likes = 0

        if 'dislikeCount' in statistics:
            dislikes = statistics['dislikeCount']
        else:
            dislikes = 0

        if 'commentCount' in statistics:
            comment_count = statistics['commentCount']
        else:
            comment_count = 0

        # Compiles all of the various bits of info into one consistently formatted line
        #line = [video_id] + features + [prepare_feature(x) for x in [tags, view_count, likes, dislikes,
        #                                                                       comment_count, thumbnail_link]] + [date]
        #lines.append(",".join(line))
        yield {'video_id': video_id,
        	   'title': snippet.get("title", ""),
               'channel_title': snippet.get("channelTitle", ""),
               'category_id': snippet.get("categoryId", ""),
               'tags': tags,
               'views': int(view_count),
               'likes': int(likes),
               'dislikes': int(dislikes),
               'comment_total': int(comment_count),
               'thumbnail_link': thumbnail_link,
               'date': snippet.get("publishedAt", "")}


def get_pages(country_code, next_page_token="&"):
    df_video = pd.DataFrame()

    # Because the API uses page tokens (which are literally just the same function of numbers everywhere) it is much
    # more inconvenient to iterate over pages, but that is what is done here.
    while next_page_token is not None:
        # A page of data i.e. a list of videos and all needed data
        video_data_page = api_request(next_page_token, country_code)
        
        if video_data_page.get('error'):
            print(video_data_page['error'])

        # Get the next page token and build a string which can be injected into the request with it, unless it's None,
        # then let the whole thing be None so that the loop ends after this cycle
        next_page_token = video_data_page.get("nextPageToken", None)
        
        next_page_token = f"&pageToken={next_page_token}&" if next_page_token is not None else next_page_token

        # Get all of the items as a list and let get_videos return the needed features
        items = video_data_page.get('items', [])
        
        for video in get_videos(items):
            df_video = df_video.append(video, ignore_index=True)

    return df_video


def get_relevant_ids(id):
    request_url = f"https://www.googleapis.com/youtube/v3/search?part=id&maxResults=50&publishedAfter={PUBLISHED_AFTER}&relatedToVideoId={id}&type=video&key={api_key}"
    request = requests.get(request_url)
    if request.status_code == 429:
        print("Temp-Banned due to excess requests, please wait and continue later")
        sys.exit()
    
    request = request.json()

    if request.get('error'):
            print(request['error'])
    items = request.get('items', [])
    
    result = []
    for item in items:
        result.append(item['id']['videoId'])
    return result

def divide_chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


def gather_more_videos(data, country_code):
    ids = data.video_id.to_list()
    relevant_ids = set()
    for id in ids[:RELATED_SEED]:
        relevant_ids.update(get_relevant_ids(id))
        time.sleep(0.1)

    relevant_ids = list(relevant_ids - set(ids))[:REQUIRED_VIDEOS]
    print(f"Found {len(relevant_ids)} more relevant videos")
    
    # Split the large set up into sublists of length 50
    for relevant_ids_subset in divide_chunks(relevant_ids, 50):
        video_data_page = api_request_list(relevant_ids_subset, country_code)
        time.sleep(0.1)
        
        if video_data_page.get('error'):
            print(video_data_page['error'])
        # Get all of the items as a list and let get_videos return the needed features
        items = video_data_page.get('items', [])
        
        for video in get_videos(items):
            data = data.append(video, ignore_index=True)
    
    return data.drop_duplicates(subset=['video_id'])

def write_to_file(country_code, country_data):

    print(f"Writing {country_code} data to file,", len(country_data), "videos found")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    country_data.to_csv(f"{output_dir}/{time.strftime('%y.%d.%m')}_{country_code}_videos.csv", encoding='utf-8', index=False, quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
    

def get_data():
    for country_code in country_codes:
        country_data = get_pages(country_code)
        country_data = gather_more_videos(country_data, country_code)
        write_to_file(country_code, country_data)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--key_path', help='Path to the file containing the api key, by default will use api_key.txt in the same directory', default='api_key.txt')
    parser.add_argument('--country_code_path', help='Path to the file containing the list of country codes to scrape, by default will use country_codes.txt in the same directory', default='country_codes.txt')
    parser.add_argument('--output_dir', help='Path to save the outputted files in', default='output/')
    parser.add_argument('--related_seed', help='Number of videos that we parse for extra videos, by default will use 0', default=0)
    parser.add_argument('--required_videos', help='Number of videos that we try to find allong with the top 200, default is 0', default=0)

    args = parser.parse_args()
    RELATED_SEED = int(args.related_seed)
    REQUIRED_VIDEOS = int(args.required_videos)
    output_dir = args.output_dir
    api_key, country_codes = setup(args.key_path, args.country_code_path)

    get_data()
