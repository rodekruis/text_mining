library(tidyverse)
library(rvest)
library(stringr)
library(data.table)

source("functions.R")
source("config.R")

results_all <- readRDS("data/2018-01-17_results_all.rds")

# ---------------
example_html <- extract_html_from_url("http://www.times.mw/drought-recovery-project-starts-this-month/",
                                      sleep_sec_interval = c(1, 4))

example_text <- extract_article_text_from_html(example_html,
                                               website = "times.mw",
                                               verbose = TRUE)
# ---------------

urls <- results_all[, unique(url)]

htmls <- list()
for (url in urls[2008:length(urls)]) {
  htmls[[url]] <- extract_html_fromURL(url,
                                        sleep_sec_interval = c(1, 4))
}
saveRDS(htmls, "data/htmls1.rds")

texts <- data.table(url = names(htmls), text = character(length(htmls)))
texts[, id := .I]
missed <- c()

for (URL in texts$url) {
  cat("\r", texts[url == URL, id])
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

saveRDS(texts, "data/texts.rds")
fwrite(texts, "data/texts.csv")

