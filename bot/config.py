import pytz

class BotConfig:
    # Paths
    GIF_DIR = 'gifs'
    URMOM_GIF = f"{GIF_DIR}/ur-mom.gif"
    ALOT_GIF = f"{GIF_DIR}/alot.gif"
    
    # Response triggers
    ALOT_EXCEPTIONS = ['zealot', 'zealots', 'zealotry']
    
    # Feature toggles
    USE_REACTIONS = True
    USE_GIF_RESPONSES = True
    
    # API endpoints
    OMDB_API_URL = "http://www.omdbapi.com/"
    NHL_API_BASE = "https://api-web.nhle.com/v1"
    NHL_STATS_API = "https://api.nhle.com/stats/rest/en"
    
    # Panthers team ID and abbreviation
    PANTHERS_TEAM_ID = 13
    PANTHERS_TEAM_ABBREV = "FLA"
    
    # Timezone for reminders
    TIMEZONE = pytz.timezone('US/Eastern')
    
    # Reminder storage
    REMINDER_CHECK_INTERVAL = 10  # seconds
    
    # Panthers player quotes
    PANTHERS_QUOTES = [
        "\"We're just taking it one game at a time.\" - Aleksander Barkov",
        "\"The fans here are incredible. We feed off their energy.\" - Matthew Tkachuk",
        "\"This team has something special. We believe in each other.\" - Aaron Ekblad",
        "\"Florida is a hockey state now, and we're proud to represent it.\" - Sam Reinhart",
        "\"We play for each other and for this city.\" - Carter Verhaeghe",
        "\"The culture here is different. We're all pulling in the same direction.\" - Gustav Forsling",
        "\"Every shift matters. Every game matters.\" - Brandon Montour",
        "\"We want to bring a Cup to South Florida.\" - Sergei Bobrovsky",
        "\"The chemistry on this team is unreal.\" - Sam Bennett",
        "\"We're not done yet. We want more.\" - Paul Maurice (Head Coach)"
    ]

# Team name aliases for comparison
TEAM_ALIASES = {
    'panthers': 13, 'florida': 13, 'fla': 13,
    'oilers': 22, 'edmonton': 22, 'edm': 22,
    'jets': 52, 'winnipeg': 52, 'wpg': 52,
    'capitals': 15, 'washington': 15, 'wsh': 15, 'caps': 15,
    'knights': 54, 'vegas': 54, 'vgk': 54, 'golden knights': 54,
    'leafs': 10, 'toronto': 10, 'tor': 10, 'maple leafs': 10,
    'stars': 25, 'dallas': 25, 'dal': 25,
    'kings': 26, 'los angeles': 26, 'lak': 26, 'la': 26,
    'avalanche': 21, 'colorado': 21, 'col': 21, 'avs': 21,
    'lightning': 14, 'tampa bay': 14, 'tbl': 14, 'tampa': 14, 'bolts': 14,
    'hurricanes': 12, 'carolina': 12, 'car': 12, 'canes': 12,
    'wild': 30, 'minnesota': 30, 'min': 30,
    'senators': 9, 'ottawa': 9, 'ott': 9, 'sens': 9,
    'blues': 19, 'st louis': 19, 'stl': 19, 'st. louis': 19,
    'flames': 20, 'calgary': 20, 'cgy': 20,
    'canadiens': 8, 'montreal': 8, 'mtl': 8, 'habs': 8,
    'devils': 1, 'new jersey': 1, 'njd': 1,
    'canucks': 23, 'vancouver': 23, 'van': 23, 'nucks': 23,
    'blue jackets': 29, 'columbus': 29, 'cbj': 29, 'jackets': 29,
    'utah': 59, 'utah hockey club': 59, 'uth': 59,
    'red wings': 17, 'detroit': 17, 'det': 17, 'wings': 17,
    'rangers': 3, 'new york rangers': 3, 'nyr': 3,
    'islanders': 2, 'new york islanders': 2, 'nyi': 2, 'isles': 2,
    'penguins': 5, 'pittsburgh': 5, 'pit': 5, 'pens': 5,
    'ducks': 24, 'anaheim': 24, 'ana': 24,
    'sabres': 7, 'buffalo': 7, 'buf': 7,
    'bruins': 6, 'boston': 6, 'bos': 6,
    'flyers': 4, 'philadelphia': 4, 'phi': 4,
    'kraken': 55, 'seattle': 55, 'sea': 55,
    'predators': 18, 'nashville': 18, 'nsh': 18, 'preds': 18,
    'blackhawks': 16, 'chicago': 16, 'chi': 16, 'hawks': 16,
    'sharks': 28, 'san jose': 28, 'sjs': 28
}