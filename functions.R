standardize_record <- function(value_list) {
  fields <- c("id", "name", "url", "snippet")  # we only need these columns
  record <- value_list[fields]                 # filter
  names(record) <- fields                      # in case some of them is missing
  record[sapply(record, is.null)] <- NA        # dttp
  return(record)
}


# https://www.w3schools.com/cssref/css_selectors.asp

extract_text_from_url <- function(url,
                                  website = c("undefined",
                                              "aktualne", "blesk", "ct24",
                                              "denik", "echo24", "euro",
                                              "idnes", "ihned", "lidovky",
                                              "metro", "nova", "novinky",
                                              "parlamentnilisty", "tyden"),
                                  css = NULL,
                                  verbose = FALSE,
                                  sleep_secs = 1) {
  website <- match.arg(website)
  
  if (website == "undefined" & is.null(css)) {
    stop("Specify css or select a website!")
  } else {
    css <- switch(website,
                  undefined = css,
                  aktualne = "div.clanek-telo p",
                  blesk = "div.content p",
                  ct24 = "div.textcontent p",
                  denik = "div.dv4-clanek-text p",
                  echo24 = "div.article-detail__content p",
                  euro = "div.body p",
                  idnes = "div.text#art-text div.bbtext p",
                  ihned = "div.article-body p",
                  lidovky = "div.text div.bbtext p",
                  metro = "div.text div.bbtext p",
                  nova = "div.article_wrap p",
                  novinky = "div.articleBody p",
                  parlamentnilisty = "section.article-content p",
                  tyden = "div#lightbox-search p"
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

<<<<<<< HEAD
||||||| 6cbdb36... fix extract_phrases_from_bodies
extract_phrases_from_bodies <- function(bodies, browser = FALSE) {
  if (browser) browser()
  # get table of article urls and sentences containing migrant-related words
  filtered_sentences <- bodies %>% 
    tokenize_sentences() %>%
    named_sentences_to_df() %>%
    filter(str_detect(sentence, text_pattern)) %>%
    transform(art_id = group_indices(., article)) %>%
    group_by(art_id) %>%
    mutate(sen_id = seq_along(sentence)) %>%
    ungroup() %>%
    mutate(comp_id = paste0(art_id, "-", sen_id))
  print(filtered_sentences)
  
  # get table of words and their functions, by article
  analyzed_sentences <- rdr_pos(tagger, 
                                x = filtered_sentences$sentence,
                                doc_id = filtered_sentences$comp_id) %>%
    as_data_frame() 
  print(analyzed_sentences)
  
  interesting_sentences <- analyzed_sentences %>% 
    group_by(doc_id) %>%
    # only filter sentences that contain a matching word as a noun AND a verb
    filter(sum((str_detect(token, text_pattern) & 
                  pos == "NOUN") | 
                 pos %in% c("VERB", "AUX")) > 1) %>% 
    arrange(doc_id)
  print(interesting_sentences)
  
  # look at noun-verb combinations
  noun_verb_combinations <- interesting_sentences %>% 
    filter((str_detect(token, text_pattern) & pos == "NOUN") | pos %in% c("VERB", "AUX")) %>% 
    mutate(nouns = sum(pos == "NOUN"),
           noun_order = ifelse(pos == "NOUN",
                               cumsum(pos == "NOUN"),
                               0)) %>%
    arrange(doc_id)
  print(noun_verb_combinations)
  
  # process sentences with multiple interesting words
  noun_verb_processed <- noun_verb_combinations %>% 
    # replicate groups with n > 2 nouns n times
    .[rep(x = 1:nrow(.), times = .$nouns), ] %>%
    group_by(doc_id, token_id) %>%
    # create a new id for replicated groups 
    mutate(copy_id = seq_along(token_id)) %>%
    # and make sure there's only one noun in each group
    filter(pos != "NOUN" | noun_order == copy_id)
  print(noun_verb_processed)
  
  # select nouns and verbs per group
  noun_verb_selected <- noun_verb_processed %>% 
    group_by(doc_id, copy_id) %>%
    mutate(noun_position = sum(token_id * (pos == "NOUN")),
           dist_from_noun = abs(token_id - noun_position),
           closest_verb = dist_from_noun == min(dist_from_noun[pos != "NOUN"])) %>%
    filter(closest_verb == TRUE | pos == "NOUN")
  print(noun_verb_selected)
  
  # construct phrases
  extracted_phrases <- noun_verb_selected %>%
    summarize(phrase = paste(token[pos == "NOUN"], 
                             # n() - 1 makes sure we always have the second
                             # verb in case there are two with the same distance
                             token[pos %in% c("VERB", "AUX")][n() - 1])) %>%
    select(-copy_id)
  extracted_phrases
}

=======
extract_phrases_from_bodies <- function(bodies) {
  # get table of article urls and sentences containing migrant-related words
  filtered_sentences <- bodies %>% 
    tokenize_sentences() %>%
    named_sentences_to_df() %>%
    filter(str_detect(sentence, text_pattern)) %>%
    transform(art_id = group_indices(., article)) %>%
    group_by(art_id) %>%
    mutate(sen_id = seq_along(sentence)) %>%
    ungroup() %>%
    mutate(comp_id = paste0(art_id, "-", sen_id))
  print(filtered_sentences)
  
  # get table of words and their functions, by article
  analyzed_sentences <- rdr_pos(tagger, 
                                x = filtered_sentences$sentence,
                                doc_id = filtered_sentences$comp_id) %>%
    as_data_frame() 
  print(analyzed_sentences)
  
  interesting_sentences <- analyzed_sentences %>% 
    group_by(doc_id) %>%
    # only filter sentences that contain a matching word as a noun AND a verb
    filter(sum((str_detect(token, text_pattern) & 
                  pos == "NOUN") | 
                 pos %in% c("VERB", "AUX")) > 1) %>% 
    arrange(doc_id)
  print(interesting_sentences)
  
  # look at noun-verb combinations
  noun_verb_combinations <- interesting_sentences %>% 
    filter((str_detect(token, text_pattern) & pos == "NOUN") | pos %in% c("VERB", "AUX")) %>% 
    mutate(nouns = sum(pos == "NOUN"),
           noun_order = ifelse(pos == "NOUN",
                               cumsum(pos == "NOUN"),
                               0)) %>%
    arrange(doc_id)
  print(noun_verb_combinations)
  
  # process sentences with multiple interesting words
  noun_verb_processed <- noun_verb_combinations %>% 
    # replicate groups with n > 2 nouns n times
    .[rep(x = 1:nrow(.), times = .$nouns), ] %>%
    group_by(doc_id, token_id) %>%
    # create a new id for replicated groups 
    mutate(copy_id = ifelse(nouns > 1,
                            seq_along(token_id),
                            -1L)) %>%
    # and make sure there's only one noun in each group
    filter(noun_order != copy_id) 
  print(noun_verb_processed)
  
  # select nouns and verbs per group
  noun_verb_selected <- noun_verb_processed %>% 
    group_by(doc_id, copy_id) %>%
    mutate(noun_position = sum(token_id * (pos == "NOUN")),
           dist_from_noun = abs(token_id - noun_position),
           closest_verb = dist_from_noun == min(dist_from_noun[pos != "NOUN"])) %>%
    filter(closest_verb == TRUE | pos == "NOUN")
  print(noun_verb_selected)
  
  # construct phrases
  extracted_phrases <- noun_verb_selected %>%
    summarize(phrase = paste(token[pos == "NOUN"], 
                             # n() - 1 makes sure we always have the second
                             # verb in case there are two with the same distance
                             token[pos %in% c("VERB", "AUX")][n() - 1])) %>%
    select(-copy_id)
  extracted_phrases
}

>>>>>>> parent of 6cbdb36... fix extract_phrases_from_bodies
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
