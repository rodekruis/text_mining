library(httr)
library(data.table)

api_url <- "https://api.cognitive.microsoft.com/bing/v7.0/search?"

response <- GET(url = paste0(api_url, 
                             "q=", query_string, 
                             "&count=", count, 
                             "&offset=", offset), 
               add_headers(`Ocp-Apim-Subscription-Key` = key1))

res <- content(response, encoding = 'json')

response$status_code  # 200

res$webPages$totalEstimatedMatches  # 1530

res_table <- rbindlist(res$webPages$value)