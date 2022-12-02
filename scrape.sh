#/bin/sh

COMMENT_LIMIT=1000

# Scrape the most popular videos at the moment
python3 video_scraper.py --output_dir data/scraper

#Scrape the comments belonging to these features
for file in data/scraper/*
do	
	echo "Running comment_scraper.py on $file"
	python3 comment_scraper.py $file $COMMENT_LIMIT
done


#python3 comment_scraper.py 