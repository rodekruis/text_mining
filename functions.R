# helper function for extracting relevant items from list of values 
# (and handling missing data)
standardize_record <- function(value_list, 
                               fields = c("id", "name", "url", "snippet")) {
  record <- value_list[fields]                 # filter
  names(record) <- fields                      # in case some of them is missing
  record[sapply(record, is.null)] <- NA        # dtto
  return(record)
}

# urls from a Bing search for a specified query
get_all_urls <- function(query_string = "drought",
                         site_string = "times.mw",
                         api_key = API_KEY_1,
                         save_result = TRUE,
                         save_intermediate = TRUE,
                         results_limit = NULL) {
  # browser()
  
  API_URL <- "https://api.cognitive.microsoft.com/bing/v7.0/search?"
  FETCH_COUNT <- 50
  
  offset <- 0
  i <- 1
  articles_data <- list()
  
  repeat {
    response <- GET(url = paste0(API_URL,
                                 "q=", query_string,
                                 "+site%3A", site_string,
                                 "&count=", FETCH_COUNT,
                                 "&offset=", offset),
                    add_headers(`Ocp-Apim-Subscription-Key` = api_key))
    
    message(i, "\tstatus code: ", response$status_code)
    
    if (response$status_code == 200) {  # OK
      
      # extract main content object
      response_content <- content(response, 
                                  encoding = "json")
      
      # extract table of article records
      result_table <- rbindlist(
        lapply(response_content$webPages$value, 
               standardize_record)  # only select [id, name, url, snippet]
      )
      
      # get current result batch size & total amount of results
      matches_batch <- length(response_content$webPages$value)          # 46 (?)
      matches_total <- response_content$webPages$totalEstimatedMatches  # 1530
    }
    
    articles_data[[i]] <- list()
    
    articles_data[[i]]$response_content <- response_content
    articles_data[[i]]$result_table <- result_table
    articles_data[[i]]$matches_batch <- matches_batch
    
    i <- i + 1
    Sys.sleep(0.3)
    
    offset <- offset + min(FETCH_COUNT, matches_batch)  # min(50, 46) = 46
    
    response_content <- NA
    result_table <- NA
    matches_batch <- NA
    
    if (offset >= min(matches_total, results_limit)) break
  }
  
  all_results <- rbindlist(lapply(articles_data, function(x) x[["result_table"]]))
  
  # save to .rds
  filename <- paste(Sys.Date(),
                    gsub("\\W", "-", query_string),
                    gsub("\\W", "-", site_string),
                    sep = "_")
  if (save_intermediate) saveRDS(articles_data, 
                                 file = paste0("data/", 
                                               filename, 
                                               "_articles_data.rds"))
  if (save_result) saveRDS(all_results, 
                           file = paste0("data/", 
                                         filename, 
                                         "_all_results.rds"))
  
  return(all_results)
}


# https://www.w3schools.com/cssref/css_selectors.asp

extract_article_text_from_html <- function(html,
                                           website = c("undefined",
                                                       "times.mw", 
                                                       "nyasatimes.com",
                                                       "mwnation.com", 
                                                       "maravipost.com", 
                                                       "malawi24.com", 
                                                       "malawivoice.com"),
                                           css = NULL,
                                           verbose = FALSE) {
  website <- match.arg(website)
  
  if (website == "undefined" & is.null(css)) {
    stop("Specify css or select a website!")
  } else {
    css <- switch(website,
                  undefined = css,
                  `times.mw` = "div.entry-content", 
                  `nyasatimes.com` = "div#content article div.entry-content",
                  `mwnation.com` = "div#content article div.entry-content",  # JS 
                  `maravipost.com` = "div.content div.post-content p span", 
                  `malawi24.com` = "div.post-container div.post-content", 
                  `malawivoice.com` = "article div.entry-content"
    )
  }
  
  text <- try(
    html %>%
      html_nodes(css = css) %>% 
      html_text() %>%
      paste(collapse = "\n")
  )
  if (verbose) print(substr(text, 1, 50))
  text
}

# not used right now
extract_article_date_from_html <- function(html,
                                           website = c("undefined",
                                                       "times.mw", 
                                                       "nyasatimes.com",
                                                       "mwnation.com", 
                                                       "maravipost.com", 
                                                       "malawi24.com", 
                                                       "malawivoice.com"),
                                           css = NULL,
                                           verbose = FALSE) {
  website <- match.arg(website)
  
  if (website == "undefined" & is.null(css)) {
    stop("Specify css or select a website!")
  } else {
    css <- switch(website,
                  undefined = css,
                  `times.mw` = "div.mom-post-meta time", #datetime 
                  `nyasatimes.com` = "div#content article div.entry-meta",
                  `mwnation.com` = "div#content article span.entry-date time",  # datetime 
                  `maravipost.com` = "div.meta-holder", #text 
                  `malawi24.com` = "span.posted-on time", 
                  `malawivoice.com` = "p.postmeta time" #datetime
    )
  }
  
  text <- try(
    html %>%
      html_nodes(css = css) %>% 
      html_text() %>%
      paste(collapse = "\n")
  )
  if (verbose) print(substr(text, 1, 50))
  text
}

extract_html_from_url <- function(url,
                                  sleep_sec_interval) {
  con <- try(url_connection(url,
                            handle = new_handle(), 
                            sleep_sec_interval = sleep_sec_interval))
  on.exit(close(con))
  tryCatch(read_html(con),
           error = function(e) message("Missed url: ", url))
}

url_connection <- function(url, 
                           handle, 
                           user_agent_strings = getOption("user_agent_strings"),
                           sleep_sec_interval = getOption("sleep_sec_interval", c(1, 15))) {
  require("curl")
  if (is.null(user_agent_strings)) {
    user_agent_options <- c("Mozilla/5.0 (Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko")
  }
  # do nothing for a random amount of seconds (within interval)
  sleep_sec <- runif(1, sleep_sec_interval[1], sleep_sec_interval[2])
  message(round(sleep_sec, 2), "s sleep")
  Sys.sleep(sleep_sec)
  # pretend to be a random browser
  handle_setheaders(handle = handle, "User-Agent" = sample(user_agent_strings, 1))
  # return connection
  curl(url = url, open = "rb", handle = handle)
}

get_domain_from_url <- function(url) {
  str_replace(url, "https?://(www\\.)?([\\d\\w]*\\.(com|mw))/.*", "\\2")
}

clean_up_texts <- function(texts, drop_raw_text = TRUE) {
  
  texts[, text := raw_text]
  
  # copy raw text column
  if (drop_raw_text) texts[, raw_text := NULL]
  
  # filter out invalid rows
  texts <- texts[text != ""]
  texts <- texts[!str_detect(url, "/(category|tag)/")]
  
  # get short domain from url
  texts[, domain := get_domain_from_url(url = url)]
  
  texts[, text := str_replace_all(text, "[\r\n\t]", " ") %>% 
          str_replace_all(" +", " ") %>%   # remove duplicated spaces
          str_replace_all("(^ | $)", "")]  # remove space at the beginning or the end
  
  # clean up selectively for each domain
  texts[domain == "times.mw",
        text := str_replace_all(text, 
                                "(.*\\.) [A-Za-z ]* – who has written .*$", 
                                "\\1")]
  
  texts[domain == "nyasatimes.com",
        text := str_replace_all(text, 
                                "(\\(adsbygoogle = window\\.adsbygoogle \\|\\| \\[\\]\\)\\.push\\(\\{\\}\\);|Follow and Subscribe Nyasa TV.* $)", 
                                "")]
  
  texts[domain == "mwnation.com",
        text := str_replace_all(text, "\\(Visited .*$", "")]
  
  texts[domain == "maravipost.com",
        text := str_replace_all(text, "\\(adsbygoogle = window\\.adsbygoogle \\|\\| \\[\\]\\)\\.push\\(\\{\\}\\); Tweet *", "") %>%
          str_replace_all(": medianet_.*$", "")] 
  
  texts[domain == "malawi24.com",
        text := str_replace_all(text, "Share this: *Click to.*$", "")]
  
  texts[domain == "malawivoice.com",
        text := str_replace_all(text, " added by.*", "")]
  
  texts[]
}
