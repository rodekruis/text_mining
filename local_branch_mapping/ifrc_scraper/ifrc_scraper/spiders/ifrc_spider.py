# Import scrapy
import scrapy
import re
import pandas as pd

# Import the CrawlerProcess: for running the spider
from scrapy.crawler import CrawlerProcess

def safe_execute(default, function, group_number):
    try:
        return function.group(group_number)
    except:
        return default

# Create the Spider class
class ifrc_spider(scrapy.Spider):
    
    name = "ifrc_spider"
    
    regions = ['africa', 'americas', 'asia-pacific', 'europe-and-central-asia', 'middle-east-and-north-africa']
    start_urls = []
    for region in regions:
        start_urls.append('https://media.ifrc.org/ifrc/where-we-work/' + region + '/')
        
    # First parsing method
    def parse(self, response):
        # get list of countries
        ns_dict = {key: value for (key, value) in 
                   zip(response.css('.media-heading > a ::text').extract(),
                       response.css('.media-heading > a ::attr(href)').extract())
                   }
        if ns_dict == {}:
            ns_dict = {key: value for (key, value) in 
                       zip(response.css('.et_pb_text_inner > p > a ::text').extract(),
                           response.css('.et_pb_text_inner > p > a ::attr(href)').extract())
                       }
            region = re.sub('/', '', re.sub('https://media.ifrc.org/ifrc/where-we-work/', '', response.url))
            bad_names = [name_ns for name_ns, url in ns_dict.items() if region not in url]
            for bad_name in bad_names:
                del ns_dict[bad_name]
        
        for name_ns, url in ns_dict.items():
            yield response.follow(url = url,
                                  callback = self.parse_nation,
                                  meta={'name_ns': name_ns})

    # Second parsing method
    def parse_nation(self, response):
        contact_info = ', '.join(response.css('.cw_content2colsgroup ::text').extract())
        type_contact = 1
        if contact_info == '':
            type_contact = 2
            contact_info = response.css('.ns-detail ::text').extract()
        
        if type_contact == 1:
            address = safe_execute('', re.search('Address:(?s)(.*)(Postal Address:|Contact Information:)', contact_info, re.IGNORECASE), 1)
            postal_address = safe_execute('', re.search('Postal Address:(?s)(.*)Contact Information:', contact_info, re.IGNORECASE), 1)
            tel = safe_execute('', re.search('(?<=Tel:)[0-9,\s,\/,\(,\),\+,\-]+', contact_info, re.IGNORECASE), 0)
            fax = safe_execute('', re.search('(?<=Fax:)[0-9,\s,\/,\(,\),\+,\-]+', contact_info, re.IGNORECASE), 0)
            telegram = safe_execute('', re.search('(?<=Telegram:)([a-z,A-Z,À-ÿ,0-9,\s,\/,\(,\),\']+)(Email:)', contact_info, re.IGNORECASE), 1)
            email = safe_execute('', re.search('(?<=Email: , )[.,@,a-z,A-Z,À-ÿ,0-9,\/,\(,\),-]+', contact_info, re.IGNORECASE), 0)
            web = safe_execute('', re.search('(?<=Web: , )(http:\/\/|https:\/\/)[.,a-z,A-Z,0-9,\-]+', contact_info, re.IGNORECASE), 0)
            tw = safe_execute('', re.search('(?<=Twitter: , )(http:\/\/|https:\/\/)[.,a-z,A-Z,0-9,\-,\/]+', contact_info, re.IGNORECASE), 0)
            fb = safe_execute('', re.search('(?<=Facebook: , )(http:\/\/|https:\/\/)[.,a-z,A-Z,0-9,\-,\/]+', contact_info, re.IGNORECASE), 0)
            if fb == '':
                fb = safe_execute('', re.search('(?<=Facebook: , )[.,a-z,A-Z,0-9,\-,\/,\s,À-ÿ]+', contact_info, re.IGNORECASE), 0)
                # TO DO: IF ONLY TEXT, SEARCH ON FB AND SCRAPE URL
            
        if type_contact == 2:
            try:
                address = contact_info[contact_info.index('Address') + 1]
            except:
                address = ''
            postal_address = ''
            tel = ', '.join([re.sub('Tel: ', '', x) for x in contact_info if 'Tel: ' in x])
            fax = ', '.join([re.sub('Fax: ', '', x) for x in contact_info if 'Fax: ' in x])
            telegram = ''
            try:
                email = contact_info[contact_info.index('Email: ') + 1]
                contact_info_web = response.css('.ns-icon ::attr(href)').extract()
                web, tw, fb = contact_info_web[0], contact_info_web[1], contact_info_web[2]
            except:
                email, web, tw, fb = '', '', '', ''
        yield {
                'name': response.meta['name_ns'],
                'address': address,
                'postal_address': postal_address,
                'tel': tel,
                'fax': fax,
                'telegram': telegram,
                'email': email,
                'web': web,
                'twitter': tw,
                'facebook': fb
            }
