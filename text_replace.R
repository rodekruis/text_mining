library(data.table)
texts <- readRDS("data/texts1.rds")  # texts.rds
texts <- texts[text != ""]
texts <- texts[!str_detect(url, "/(category|tag)/")]

texts[, domain := get_domain_from_url(url = url)]

texts[, text1 := str_replace_all(text, "[\r\n\t]", " ") %>% 
        str_replace_all(" +", " ") %>%   # remove duplicated spaces
        str_replace_all("(^ | $)", "")]  # remove space at the beginning or the end

# times.mw
texts[domain == "times.mw",
      text1 := str_replace_all(text1, 
                               "(.*\\.) [A-Za-z ]* – who has written .*$", 
                               "\\1")]

texts[domain == "nyasatimes.com",
      text1 := str_replace_all(text1, 
                               "(\\(adsbygoogle = window\\.adsbygoogle \\|\\| \\[\\]\\)\\.push\\(\\{\\}\\);|Follow and Subscribe Nyasa TV.* $)", 
                               "")]

texts[domain == "mwnation.com",
      text1 := str_replace_all(text1, "\\(Visited .*$", "")]


texts[domain == "maravipost.com",
      text1 := str_replace_all(text1, "\\(adsbygoogle = window\\.adsbygoogle \\|\\| \\[\\]\\)\\.push\\(\\{\\}\\); Tweet *", "") %>%
        str_replace_all(": medianet_.*$", "")] 

texts[domain == "malawi24.com",
      text1 := str_replace_all(text1, "Share this: *Click to.*$", "")]

texts[domain == "malawivoice.com",
      text1 := str_replace_all(text1, " added by.*", "")]

fwrite(texts[, .(domain, url, text = text1)], "data/texts1.csv", sep = "\t")
