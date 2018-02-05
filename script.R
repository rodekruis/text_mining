library(tidyverse)
library(rvest)
library(stringr)
library(data.table)
library(httr)

source("functions.R")
source("config.R")

### (1) get article urls from Bing search API --------

# prepare lists for drough and flood articles
results_flood   <- list()
results_drought <- list()

for (domain in c("times.mw", "nyasatimes.com", "mwnation.com",
                 "maravipost.com", "malawi24.com", "malawivoice.com")) {
  results_flood[[domain]]   <- get_all_urls("flood", domain)
  results_drought[[domain]] <- get_all_urls("drought", domain)
}

# merge to records to one data.table
results_flood_all <- rbindlist(results_flood)
results_drought_all <- rbindlist(results_drought)

# filter out some invalid urls
results_flood_all <- results_flood_all[!str_detect(url, "/(category|tag)/")]
results_drought_all <- results_drought_all[!str_detect(url, "/(category|tag)/")]

# save
saveRDS(results_flood_all, paste0("data/", Sys.Date(), "_results_flood.rds"))
saveRDS(results_drought_all, paste0("data/", Sys.Date(), "_results_flood.rds"))


### (2) fetch article pages from url list ------------

urls_flood <- results_flood_all[, unique(url)]
urls_drought <- results_drought_all[, unique(url)]

htmls_flood <- list()
for (url in urls_flood) {
  htmls_flood[[url]] <- extract_html_from_url(url,
                                              sleep_sec_interval = c(1, 4))
}
saveRDS(htmls_flood, "data/htmls_flood.rds")

htmls_drought <- list()
for (url in urls_drought) {
  htmls_drought[[url]] <- extract_html_from_url(url,
                                                sleep_sec_interval = c(1, 4))
}
saveRDS(htmls_drought, "data/htmls_drought.rds")


### (3) extract article text from html ---------------

# prepare table for texts
texts <- data.table(type = c(rep("flood", length(htmls_flood)),
                             rep("drought", length(htmls_drought))),
                    url = c(names(htmls_flood), names(htmls_drought)))
texts[, raw_text := character()]
texts[, id := .I]
missed <- c()

# loop through all collected URL and try to get the article text
for (URL in texts$url) {
  cat("\r", texts[url == URL, id], "/", texts[, max(id)])
  domain <- get_domain_from_url(URL)
  texts[url == URL, text := tryCatch(
    extract_article_text_from_html(htmls[[URL]],
                                   website = domain,
                                   verbose = FALSE),
    error = function(e) {
      missed <- c(missed, URL)
      message("Missed url: ", URL)
    }
  )]
}

# save
saveRDS(texts, "data/texts_raw.rds")


### (4) clean up texts -------------------------------

texts <- clean_up_texts(texts)

saveRDS(texts, "data/texts_clean.rds")
fwrite(texts, "data/texts.csv", sep = "/t")


