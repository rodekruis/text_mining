
# helper function for extracting relevant items from list of values 
# (and handling missing data)
standardize_record <- function(value_list, 
                               fields = c("id", "name", "url", "snippet")) {
  record <- value_list[fields]                 # filter
  names(record) <- fields                      # in case some of them is missing
  record[sapply(record, is.null)] <- NA        # dtto
  return(record)
}


# https://www.w3schools.com/cssref/css_selectors.asp

extract_text_from_url <- function(url,
                                  website = c("undefined",
                                              "times.mw", 
                                              "nyasatimes.com",
                                              "mwnation.com", 
                                              "maravipost.com", 
                                              "malawi24.com", 
                                              "malawivoice.com"),
                                  css = NULL,
                                  verbose = FALSE,
                                  sleep_secs = 1) {
  website <- match.arg(website)
  
  if (website == "undefined" & is.null(css)) {
    stop("Specify css or select a website!")
  } else {
    css <- switch(website,
                  undefined = css,
                  `times.mw` = "div.entry-content", 
                  `nyasatimes.com` = "article div.entry-content",
                  `mwnation.com` = "", 
                  `maravipost.com` = "", 
                  `malawi24.com` = "", 
                  `malawivoice.com` = ""
                  )
  }
  
  text <- try(
    url %>%
      url_connection(handle = new_handle()) %>%
      read_html() %>%
      html_nodes(css = css) %>% 
      html_text() %>%
      paste(collapse = "\n")
  )
  if (verbose) print(substr(text, 1, 50))
  Sys.sleep(sleep_secs)
  text
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
  Sys.sleep(runif(1, sleep_sec_interval[1], sleep_sec_interval[2]))
  # pretend to be a random browser
  handle_setheaders(handle = handle, "User-Agent" = sample(user_agent_strings, 1))
  # return connection
  curl(url = url, open = "rb", handle = handle)
}
