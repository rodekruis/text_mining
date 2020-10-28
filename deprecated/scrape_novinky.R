library(tidyverse)
library(rvest)
library(stringr)

novinky_make_listing_url <- function(query = "uprchlíci",
                                     exact_phrase = 0,
                                     section = -1,
                                     exclude = "",
                                     date_from = "1.9.2016",
                                     date_to = "",
                                     page = 1) {
  paste0("https://www.novinky.cz/hledej?w=",
         gsub(" ", "+", query),
         "&isPhrase=", 
         exact_phrase,
         "&section=",
         section,
         "&excludeWords=",
         exclude,
         "&dateFrom=",
         date_from,
         "&dateTo=",
         date_to,
         "&page=",
         page)
}

novinky_get_links_from_listing_url <- function(url) {
  url %>%
    url_connection(handle = new_handle()) %>%
    read_html() %>%
    html_nodes("div.item div.info a") %>% 
    html_attr("href")
}

novinky_get_last_listing_page <- function(first_url) {
  max_from_page <- first_url %>%
    url_connection(handle = new_handle()) %>%
    read_html() %>% 
    html_nodes("div#msgLine strong") %>% 
    html_text() %>% 
    str_replace_all("\\D", "") %>% 
    as.numeric() %>% 
    max() %>%
    (function (x) ceiling(x / 10))
  # pages with page number > 100 return an error (bug?)
  min(max_from_page, 100)
}

novinky_get_all_links <- function(query = "uprchlíci",
                                  exact_phrase = 0,
                                  section = -1,
                                  exclude = "",
                                  date_from = "1.9.2016",
                                  date_to = "",
                                  sleep_secs = 0) {
  last_page <- novinky_get_last_listing_page(
    novinky_make_listing_url(query = query,
                             exact_phrase = exact_phrase,
                             section = section,
                             exclude = exclude,
                             date_from = date_from,
                             date_to = date_to,
                             page = 1)
  )
  all_urls <- unlist(lapply(1:last_page, 
                            function(page) {
                              Sys.sleep(sleep_secs)
                              novinky_get_links_from_listing_url(
                                novinky_make_listing_url(query = query,
                                                         exact_phrase = exact_phrase,
                                                         section = section,
                                                         exclude = exclude,
                                                         date_from = date_from,
                                                         date_to = date_to,
                                                         page = page))
                            }
  ))
  unique(all_urls)
}

