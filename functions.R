

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
                  `maravipost.com` = "div.content div.post-content", 
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

extract_html_from_url <- function(url,
                                  sleep_sec_interval) {
  con <- try(url_connection(url,
                     handle = new_handle(), 
                     sleep_sec_interval = sleep_sec_interval))
  on.exit(close(con))
  read_html(con)
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
