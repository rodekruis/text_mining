library(httr)
library(data.table)

source("config.R")  # load API_KEY_1, API_KEY_2

response <- readRDS("data/response1.rds")

############

get_all_urls <- function(query_string = "drought",
                         site_string = "times.mw") {
  
  API_URL <- "https://api.cognitive.microsoft.com/bing/v7.0/search?"
  FETCH_COUNT <- 50
  
  offset <- 0
  i <- 1
  
  articles_data <- list()
  
  repeat {
    
    
    response <- response
      # GET(url = paste0(API_URL, 
      #                  "q=", query_string, 
      #                  "+site%3A", site_string,
      #                  "&count=", FETCH_COUNT, 
      #                  "&offset=", offset), 
      #     add_headers(`Ocp-Apim-Subscription-Key` = API_KEY_1))
    
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
    
    offset <- offset + min(FETCH_COUNT, matches_batch)  # min(50, 46) = 46
    if (offset >= matches_total) break
    
    print(i)
    
    articles_data[[i]] <- list()
    
    articles_data[[i]]$response_content <- response_content
    articles_data[[i]]$result_table <- result_table
    articles_data[[i]]$matches_batch <- matches_batch
    
    response_content <- NA
    result_table <- NA
    matches_batch <- NA
    
    i <- i + 1
  }
  
}


standardize_record <- function(value_list) {
  fields <- c("id", "name", "url", "snippet")  # we only need these columns
  record <- value_list[fields]                 # filter
  names(record) <- fields                      # in case some of them is missing
  record[sapply(record, is.null)] <- NA        # dttp
  return(record)
}





###########
query_string <- "drought"
site_string <- "times.mw"
count <- 100
offset <- 0

response <- GET(url = paste0(api_url, 
                             "q=", query_string, 
                             "+site%3A", site_string,
                             "&count=", count, 
                             "&offset=", offset), 
                add_headers(`Ocp-Apim-Subscription-Key` = API_KEY_1))

res <- content(response, encoding = 'json')

response$status_code  # 200

res$webPages$totalEstimatedMatches  # 1530

res_table <- rbindlist(res$webPages$value)