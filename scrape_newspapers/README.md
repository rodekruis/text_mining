three python scripts to scrap news articles and extract impact data

1) scrape_articles <br />
get articles from all newspapers of a given country <br />
output: pandas DataFrame of articles, in csv <br />
row format: ['title', 'publish_date', 'text', 'url']

2) inspect_articles_tag_topical <br />
analyze the output of scrap_articles and decide if each article is relevant or not <br />
add a corresponding boolean variable <br />
input: pandas DataFrame of articles, in csv <br />
output: pandas DataFrame of articles, in csv <br />
TBI: automatize the process with a classification algorithm, too few data so far <br />

3) get_impact_data <br />
analyze relevant articles and extract impact data <br />
input: pandas DataFrame of articles, in csv + gazetteer of locations, in csv + keywords, in txt <br />
output: pandas DataFrame of impact data, in csv <br />
row format: [index=['location', 'date'], columns=['damage_livelihood', 'damage_general',
                                                    'people_affected', 'people_dead',
                                                    'houses_affected', 'livelihood_affected',
                                                    'infrastructures_affected',
                                                    'infrastructures_mentioned',
                                                    'sentence(s)', 'article_title']]
<br />
author: Jacopo Margutti, 2019
