# txmm-project
This repository is created for the course Text and Multimedia Mining to easily scrape YouTube videos and comments.
## Usage
Create a file `api_key.txt` with your YouTube API key. You will need a valid API key for the YouTube Data API. It is free and the instructions for doing so are [here](https://developers.google.com/youtube/registering_an_application). It is slightly awkward to get a key, but if you follow the instructions you should be ok. \
Use the `country_code.txt` file to select the country that you want to download the most popular videos from. These are 2 letter country abbreviations according to ISO 3166-1.

### Easy usage
For easy usage: Run `scrape.sh` to scrape the 200 most popular videos with 100 comments on each video and their dislikes.

### Advanced usage
Run `python3 video_scraper.py --related_seed 50 --required_videos 1000` to scrape 1000 more videos based on the 50 most relevant videos from 50 videos. (Uses a lot of your API quota). \
With these videos, we can run `python3 comment_scraper.py output/<date>US_videos.csv 1000` to scrape 1000 comments on all the videos that we have just scraped. \
We can then run `python3 dislike_scraper.py output/<date>US_videos.csv` to scrape the dislikes using the Return YouTube Dislike API.

We now have 2 files in our `output` directory, on these we can perform some mining. See the notebook for more details.