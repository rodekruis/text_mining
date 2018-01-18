library(tidyverse)
library(rvest)
library(stringr)
library(data.table)

source("functions.R")
source("config.R")

results_all <- readRDS("data/2018-01-17_results_all.rds")

html1 <- extract_html_from_url(results_all[1, url],  # "http://www.times.mw/drought-recovery-project-starts-this-month/"
                               sleep_sec_interval = c(1, 4))

text1 <- extract_article_text_from_html(html1,
                                        website = "times.mw",
                                        verbose = TRUE)

html2 <- extract_html_from_url(results_all[2200, url],
                               c(1, 2))
text2 <- extract_article_text_from_html(html2,
                                        website = "mwnation.com",
                                        verbose = TRUE)

