class Urls:
    # urls contain search terms: named location, price <300k and condo/house
    big_island_scrape = ("https://www.zillow.com/island-of-hawaii-hilo-hi/?searchQueryState=%7B%22pagination%22%3A%7B"
                         "%7D%2C%22isMapVisible%22%3Atrue%2C%22mapBounds%22%3A%7B%22west%22%3A-157.04063398828126%2C"
                         "%22east%22%3A-153.82713301171876%2C%22south%22%3A18.537330703267006%2C%22north%22%3A20"
                         ".638341655139012%7D%2C%22usersSearchTerm%22%3A%22Island%20of%20Hawaii%2C%20HI%22%2C"
                         "%22regionSelection%22%3A%5B%7B%22regionId%22%3A784002%2C%22regionType%22%3A31%7D%5D%2C"
                         "%22filterState%22%3A%7B%22sort%22%3A%7B%22value%22%3A%22globalrelevanceex%22%7D%2C%22ah%22"
                         "%3A%7B%22value%22%3Atrue%7D%2C%22price%22%3A%7B%22max%22%3A300000%7D%2C%22mp%22%3A%7B%22max"
                         "%22%3A1542%7D%2C%22tow%22%3A%7B%22value%22%3Afalse%7D%2C%22mf%22%3A%7B%22value%22%3Afalse"
                         "%7D%2C%22land%22%3A%7B%22value%22%3Afalse%7D%2C%22apa%22%3A%7B%22value%22%3Afalse%7D%2C"
                         "%22manu%22%3A%7B%22value%22%3Afalse%7D%7D%2C%22isListVisible%22%3Atrue%2C%22mapZoom%22%3A9"
                         "%7D")
    maui_scrape = (
        "https://www.zillow.com/maui-county-hi/?searchQueryState=%7B%22pagination%22%3A%7B%7D%2C%22isMapVisible%22"
        "%3Atrue%2C%22mapBounds%22%3A%7B%22west%22%3A-157.4500422441406%2C%22east%22%3A-155.84329175585935%2C"
        "%22south%22%3A20.345325891144544%2C%22north%22%3A21.387284027917385%7D%2C%22usersSearchTerm%22%3A%22Maui"
        "%20County%2C%20HI%22%2C%22regionSelection%22%3A%5B%7B%22regionId%22%3A250%2C%22regionType%22%3A4%7D%5D%2C"
        "%22filterState%22%3A%7B%22sort%22%3A%7B%22value%22%3A%22globalrelevanceex%22%7D%2C%22price%22%3A%7B%22min"
        "%22%3A0%2C%22max%22%3A300000%7D%2C%22mp%22%3A%7B%22min%22%3A0%2C%22max%22%3A1556%7D%2C%22tow%22%3A%7B"
        "%22value%22%3Afalse%7D%2C%22mf%22%3A%7B%22value%22%3Afalse%7D%2C%22land%22%3A%7B%22value%22%3Afalse%7D%2C"
        "%22ah%22%3A%7B%22value%22%3Atrue%7D%2C%22apa%22%3A%7B%22value%22%3Afalse%7D%2C%22manu%22%3A%7B%22value%22"
        "%3Afalse%7D%7D%2C%22isListVisible%22%3Atrue%7D")

    kauai_scrape = (
        "https://www.zillow.com/kauai-county-hi/?searchQueryState=%7B%22isMapVisible%22%3Atrue%2C%22mapBounds%22"
        "%3A%7B%22north%22%3A22.46205510651506%2C%22south%22%3A21.427758392993628%2C%22east%22%3A-159"
        ".1179757558594%2C%22west%22%3A-160.72472624414064%7D%2C%22usersSearchTerm%22%3A%22Maui%2C%20HI%22%2C"
        "%22filterState%22%3A%7B%22sort%22%3A%7B%22value%22%3A%22globalrelevanceex%22%7D%2C%22tow%22%3A%7B%22value"
        "%22%3Afalse%7D%2C%22mf%22%3A%7B%22value%22%3Afalse%7D%2C%22land%22%3A%7B%22value%22%3Afalse%7D%2C%22ah%22"
        "%3A%7B%22value%22%3Atrue%7D%2C%22apa%22%3A%7B%22value%22%3Afalse%7D%2C%22manu%22%3A%7B%22value%22%3Afalse"
        "%7D%2C%22price%22%3A%7B%22max%22%3A300000%7D%2C%22mp%22%3A%7B%22max%22%3A1558%7D%7D%2C%22isListVisible%22"
        "%3Atrue%2C%22regionSelection%22%3A%5B%7B%22regionId%22%3A578%2C%22regionType%22%3A4%7D%5D%2C%22pagination"
        "%22%3A%7B%7D%7D")
