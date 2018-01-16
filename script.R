library(tidyverse)
library(rvest)
library(stringr)
library(tokenizers)



#########################
xxx <- read_html("https://www.nyasatimes.com/uladi-claims-joyce-banda-sets-political-dynasty-pp/")
xxx %>% html_nodes("article div.entry-content") %>% html_text() %>% cat()

url1 <- "http://www.times.mw/bad-sobo-on-market/"
url1 %>% read_html() %>% html_nodes("div.entry-content") %>% html_text()

#########################

source("config.R")
source("functions.R")

text_pattern <- "drought"


# get urls
novinky_urls <- novinky_get_all_links(query = "uprchlíci",
                                      exact_phrase = 0,
                                      section = -1,
                                      exclude = "",
                                      date_from = "1.9.2016",
                                      date_to = "",
                                      sleep_secs = 5)

# get named character vectors
novinky_bodies <- sapply(novinky_urls, 
                         function(url) extract_text_from_url(url = url,
                                                             website = "novinky",
                                                             sleep_secs = 5))

