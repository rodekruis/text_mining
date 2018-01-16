library(tidyverse)
library(rvest)
library(stringr)

seznam_get_links_from_listing_url <- function(url) {
  url %>%
    url_connection(handle = new_handle()) %>%
    read_html() %>%
    html_nodes("div.Result-contentContainer a.Result-url-link") %>%
    html_attr("href")
}

seznam_get_all_urls <- function(query = "uprchlíci",
                                site = "parlamentnilisty.cz",
                                domain = c("search", "clanky"),
                                approx_n_results = NULL,
                                sleep_secs = 0,
                                verbose = FALSE) {
  # browser()
  domain <- match.arg(domain)
  basic_url <- paste0("https://",
                      domain,
                      ".seznam.cz/?q=site%3A",
                      site,
                      "+",
                      query,
                      "&count=20&from=")
  all_urls <- c()
  from <- 0
  repeat {
    page_urls <- seznam_get_links_from_listing_url(paste0(basic_url, from))
    if (all(page_urls %in% tail(all_urls, 20)) || 
        (!is.null(approx_n_results) && 
         from > approx_n_results)) break
    all_urls <- c(all_urls, page_urls)
    if (verbose) {
      message(from)
      print(page_urls)
    }
    Sys.sleep(sleep_secs)
    from <- from + 20
  }
  unique(all_urls)
}
