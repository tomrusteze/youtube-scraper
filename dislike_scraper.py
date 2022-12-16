"""
By Tom Rust
GitHub : https://github.com/tomrusteze
"""

import pandas as pd
import requests, sys, time, csv

SLEEP = 1


def get_dislikes(id, title):
    request = requests.get(f"https://returnyoutubedislikeapi.com/votes?videoId={id}", timeout=5)
    try:
        dislikes = request.json()["dislikes"]
    except:
        dislikes = 0
    print("Got", dislikes ,"dislikes for", title)
    time.sleep(SLEEP)
    return dislikes


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} videos.csv")
        exit()

    FILE_NAME = sys.argv[1]
    
    df_video = pd.read_csv(FILE_NAME)
    df_video['dislikes'] = df_video.drop_duplicates(subset=['video_id']).apply(lambda row: get_dislikes(row['video_id'], row['title']), axis = 1)
    df_video.to_csv(f"{FILE_NAME}", encoding='utf-8', index=False, quotechar='"', quoting=csv.QUOTE_NONNUMERIC)    