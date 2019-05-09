# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class SocialMediaItem(scrapy.Item):
    # define the fields for your item here like:
    web = scrapy.Field()
    facebook = scrapy.Field()
    twitter = scrapy.Field()
    instagram = scrapy.Field()
    pass
