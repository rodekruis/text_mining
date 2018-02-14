# merge texts
texts_drought <- readRDS("data/texts1.rds")
texts_drought[, type := "drought"]
texts_flood <- readRDS("data/texts21.rds")
texts_flood[, type := "flood"]

texts_both <- rbindlist(list(texts_drought, texts_flood))

# merge text metadata
articles_drought <- readRDS("data/2018-01-17_results_all.rds")
articles_flood <- readRDS("data/2018-02-03_results_flood.rds")
articles_both <- rbindlist(list(articles_drought, articles_flood))

# combine together
merged <- articles_both[, .(url, name, snippet)][texts_both, on = "url"]
merged[, text := text1]
merged[, text1 := NULL]
merged[, id := NULL]
setcolorder(merged, c("type", "domain", "url", "name", "snippet", "text"))

# saveRDS(merged, "data/merged2018-02-05.rds")
# write.csv(merged, "data/merged2018-02-05.txt", sep = "/t")

merged <- readRDS("data/merged2018-02-05.rds")
merged <- unique(merged)

# add indicator of presence of a keyword indication effect 
# (taken from geographical-related-keywords.txt -- from original article)
merged[, effect_keyword := str_detect(text, "(affected|hit|situation|cut off|displaced|destroyed|submerged|collapsed)")]

write.csv(merged, "data/merged2018-02-14.txt", sep = "/t")
