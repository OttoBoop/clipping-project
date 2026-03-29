        choices=[
            \"all\",
            \"rss\",
            \"google_news\",
            \"direct_scrape\",
            \"wordpress_api\",
            \"internal_search\",
            \"sitemap_daily\",
            \"vejario_archive\",
            \"camara_archive\",
        ],
    parser.add_argument(
        \"--query\",
        default=\"\",
        help=\"Optional custom query for google_news/direct_scrape/wordpress_api/internal_search/sitemap_daily\",
    )