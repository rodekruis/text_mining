library(httr)
library(data.table)

source("config.R")     # load API_KEY_1, API_KEY_2
source("functions.R")  # load standardize_record()

# response <- readRDS("data/response1.rds")


# helper function for extracting relevant items from list of values 
# (and handling missing data)
standardize_record <- function(value_list, 
                               fields = c("id", "name", "url", "snippet")) {
  record <- value_list[fields]                 # filter
  names(record) <- fields                      # in case some of them is missing
  record[sapply(record, is.null)] <- NA        # dtto
  return(record)
}


############

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

results_flood <- list()
for (domain in c("times.mw", "nyasatimes.com", "mwnation.com",
                 "maravipost.com", "malawi24.com", "malawivoice.com")) {
  results_flood[[domain]] <- get_all_urls("flood", domain)
}
results_flood_all <- rbindlist(results_flood)
results_flood_all <- results_flood_all[!str_detect(url, "/(category|tag)/")]
saveRDS(results_flood_all, paste0("data/", Sys.Date(), "_results_flood.rds"))

####

results <- list()
results[["times.mw"]]        <- get_all_urls("drought", "times.mw")
results[["nyasatimes.com"]]  <- get_all_urls("drought", "nyasatimes.com")
results[["mwnation.com"]]    <- get_all_urls("drought", "mwnation.com")
results[["maravipost.com"]]  <- get_all_urls("drought", "maravipost.com")
results[["malawi24.com"]]    <- get_all_urls("drought", "malawi24.com")
results[["malawivoice.com"]] <- get_all_urls("drought", "malawivoice.com")

results_all <- rbindlist(results)
saveRDS(results_all, paste0("data/", Sys.Date(), "_results_all.rds"))
        