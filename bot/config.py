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
    
    # Random emotes covering Discworld, horror, and occult themes
    RANDOM_EMOTES = [
        # Discworld-inspired emotes
        "adjusts a slightly bent wizard hat",
        "mutters about the importance of proper footnotes",
        "checks if anyone is watching, then discretely counts on fingers",
        "peers suspiciously at a small piece of cheese",
        "straightens up and tries to look dignified",
        "fumbles with a worn leather-bound book",
        "glances around nervously for any sign of the Auditors",
        "adjusts robes that seem to have a mind of their own",
        "looks thoughtfully at the sky, as if expecting it to fall",
        "checks pockets for spare change and finds only lint",
        "mutters something about the reliability of gargoyles",
        "peers over invisible reading glasses",
        "tries to look wise while clearly having no idea what is happening",
        "adjusts a pointy hat that keeps sliding sideways",
        "looks around for a conveniently placed orangutan",
        "checks the time on a watch that runs backwards",
        "mutters about the difficulty of maintaining a proper beard",
        "shuffles through a deck of cards that seem to shuffle themselves",
        "glances nervously at shadows that move independently",
        "adjusts spectacles and peers at something extremely small",
        "looks for a turtle to stand on",
        "checks if reality is still properly attached",
        "mutters about the unreliability of magic",
        "peers into a crystal ball that shows only static",
        "adjusts a collar that seems uncomfortably tight",
        "looks around for Death, just in case",
        "checks if the Luggage is following at a safe distance",
        "mutters about the proper way to fold space",
        "glances at a timepiece that measures L-space",
        "adjusts robes and tries to look mysterious",
        "peers at a small imp that may or may not be there",
        "checks if anyone noticed the small magical accident",
        "looks thoughtfully at a banana, as if it holds cosmic secrets",
        "adjusts a badge that reads Wizzard (misspelled)",
        "mutters about the difficulty of herding cats... or students",
        
        # Horror/slasher-inspired emotes
        "glances nervously over shoulder",
        "checks if all the doors are locked",
        "peers suspiciously into dark corners",
        "adjusts a hockey mask slightly",
        "sharpens something metallic with deliberate care",
        "looks out the window at the suspiciously quiet street",
        "checks the basement door... it is still locked, right?",
        "glances at the old mirror, half-expecting something else to look back",
        "listens intently to creaking sounds from upstairs",
        "checks the phone line... still dead",
        "peers at old photographs that seem to move when not looking directly",
        "adjusts a chainsaw chain with mechanical precision",
        "looks under the bed, just to be sure",
        "checks if the car will actually start this time",
        "glances at the old camp sign, weathered and ominous",
        "peers into the fog that should not be there",
        "checks the calendar... Friday the 13th again",
        "looks at a kitchen knife with professional interest",
        "glances at the old Ouija board in the corner",
        "checks if the power is still on",
        "peers at shadows that seem too long for the light source",
        "looks at a machete with nostalgic fondness",
        "checks if anyone else heard that scream",
        "glances at the old abandoned summer camp across the lake",
        "adjusts a freddy sweater with pride",
        "looks at the old VHS collection with satisfaction",
        "peers into a well that is definitely deeper than it should be",
        "checks the time... 3 AM, naturally",
        "glances at a music box that plays by itself",
        "looks at the old corn maze with professional appreciation",
        "peers at a clown doll that definitely was not there before",
        "checks if the babysitter remembered to lock all the windows",
        "glances at the old psychiatric hospital on the hill",
        "looks at a ouija board pointer that moved on its own",
        "peers into a bathroom mirror, counting reflections",
        
        # Occult/Crowley-inspired emotes
        "traces a pentagram in the air with deliberate precision",
        "adjusts a ceremonial robe with occult symbols",
        "peers into a scrying bowl filled with dark water",
        "mutters an incantation in ancient Enochian",
        "checks the lunar calendar for the next significant date",
        "adjusts candles in a precise magical arrangement",
        "peers at tarot cards that seem to glow faintly",
        "traces sigils on a dusty grimoire",
        "checks the alignment of ceremonial daggers",
        "mutters about the difficulty of proper ritual timing",
        "adjusts a thelemic ankh pendant",
        "peers into a crystal that reflects impossible colors",
        "checks if the ritual circle is properly sealed",
        "adjusts robes bearing the Tree of Life",
        "mutters about the reliability of astral projection",
        "peers at a mandala that seems to shift and breathe",
        "checks ancient texts for proper invocation syntax",
        "adjusts a ceremonial crown with occult significance",
        "traces the paths of the Qabalah in the air",
        "peers into a mirror that shows more than reflections",
        "mutters about the complexity of gematria calculations",
        "adjusts ritual implements with ceremonial precision",
        "checks if the incense is producing the correct colored smoke",
        "peers at hieroglyphic inscriptions that seem to move",
        "traces the seal of Solomon with practiced movements",
        "adjusts a ritual crown bearing the Eye of Horus",
        "mutters about the proper pronunciation of divine names",
        "peers into a cauldron of bubbling, luminescent liquid",
        "checks astronomical charts for planetary influences",
        "adjusts a ceremonial sword with esoteric engravings",
        "traces magical formulae in ancient alphabets",
        "peers at a compass that points to magnetic and spiritual north",
        "mutters about the challenges of maintaining magical equilibrium",
        "adjusts a ritual mask bearing symbols of transformation",
        "checks if the ethereal energies are properly balanced",
        
        # General mystical/quirky emotes
        "adjusts reality slightly to the left",
        "peers at something that probably should not exist",
        "checks if the laws of physics are still working",
        "mutters about the unreliability of dimensional boundaries",
        "glances at a clock that shows thirteen o clock",
        "adjusts a monocle that reveals hidden truths",
        "peers at footprints that lead in impossible directions",
        "checks if the universe is still expanding at the correct rate",
        "mutters about the difficulty of maintaining proper cosmic balance",
        "adjusts a hat that exists in more dimensions than strictly necessary",
        "looks at a map of places that probably do not exist",
        "checks a compass that points to somewhere else",
        "peers at a book whose pages turn themselves",
        "mutters about the complexity of interdimensional filing systems",
        "adjusts spectacles that show things as they really are",
        "glances at shadows that fall upward",
        "checks if gravity is still working as advertised",
        "peers at a photograph that shows the future",
        "mutters about the unreliability of cause and effect",
        "adjusts a watch that measures emotional time"
    ]
    
    # Taylor Swift quotes for !wisdom command
    TAYLOR_SWIFT_QUOTES = [
        "\"No matter what happens in life, be good to people. Being good to people is a great legacy to leave behind.\" - Taylor Swift",
        "\"Just be yourself, there is no one better.\" - Taylor Swift",
        "\"I've learned that you can't predict what's going to happen next.\" - Taylor Swift",
        "\"Fearless is not the absence of fear. Fearless is living in spite of those things that scare you to death.\" - Taylor Swift",
        "\"People haven't always been there for me, but music always has.\" - Taylor Swift",
        "\"I think the tiniest little thing can change the course of your day, which can change the course of your year, which can change who you are.\" - Taylor Swift",
        "\"If you're horrible to me, I'm going to write a song about it, and you won't like it. That's how I operate.\" - Taylor Swift",
        "\"The lesson I've learned the most often in life is that you're always going to know more in the future than you know now.\" - Taylor Swift",
        "\"I've found that growing up can mean a lot of things. For me, it doesn't mean I should become somebody completely new and stop loving the things I used to love.\" - Taylor Swift",
        "\"I think there is a friendly way to be strong and a strong way to be friendly.\" - Taylor Swift",
        "\"Life isn't how to survive the storm, it's about how to dance in the rain.\" - Taylor Swift",
        "\"In a world where anyone can say anything that they want about you at any time, the only thing you can really do is just live your life.\" - Taylor Swift",
        "\"I never want to change so much that people can't recognize me.\" - Taylor Swift",
        "\"Giving up doesn't always mean you're weak. Sometimes you're just strong enough to let go.\" - Taylor Swift",
        "\"I think the best thing about songwriting is that you don't have to be in a certain mood to write a certain kind of song.\" - Taylor Swift",
        "\"I think that no matter what you do in life, you should try to be a nice person.\" - Taylor Swift",
        "\"Anytime someone tells me that I can't do something, I want to do it more.\" - Taylor Swift",
        "\"I've always felt music is the only way to give an instantaneous moment the feel of slow motion.\" - Taylor Swift",
        "\"We don't need to share the same opinions as others, but we need to be respectful.\" - Taylor Swift",
        "\"I'm intimidated by the fear of being average.\" - Taylor Swift",
        "\"The way I see it, you have to earn things. If you want something, you work for it.\" - Taylor Swift",
        "\"I'd rather be at home and eat ice cream than go out and get wasted.\" - Taylor Swift",
        "\"I've wanted one thing for me my whole life, and I'm not going to be that girl who wants one thing her whole life then gets it and complains.\" - Taylor Swift",
        "\"If somebody hurts you, it's okay to cry a river, just remember to build a bridge and get over it.\" - Taylor Swift",
        "\"Unique and different is the next generation of beautiful.\" - Taylor Swift",
        "\"I'm not the girl who always has a boyfriend. I'm the girl who rarely has a boyfriend.\" - Taylor Swift",
        "\"I think who you are in school really sticks with you. I don't ever feel like the cool kid at the party, ever.\" - Taylor Swift",
        "\"I suffer from girlnextdooritis where the weights of beauty are just too heavy for a girl to carry.\" - Taylor Swift",
        "\"Silence speaks so much louder than screaming tantrums. Never give anyone an excuse to say that you're crazy.\" - Taylor Swift",
        "\"I love making new friends and I respect people for a lot of different reasons.\" - Taylor Swift",
        "\"You have people come into your life shockingly and surprisingly. You have losses that you never thought you'd experience.\" - Taylor Swift",
        "\"I don't think you should ever stop being a dreamer.\" - Taylor Swift",
        "\"There are two ways to live: you can live as if nothing is a miracle; you can live as if everything is a miracle. I choose the latter.\" - Taylor Swift",
        "\"I've always strived to be successful, not famous.\" - Taylor Swift",
        "\"Real life is a funny thing, you know. In real life, saying the right thing at the right moment is beyond crucial.\" - Taylor Swift",
        "\"To me, fearless is not the absence of fear. It's not being completely unafraid. Fearless is having fears but jumping anyway.\" - Taylor Swift",
        "\"I think the worst part of getting older is the realization that all your problems are your own.\" - Taylor Swift",
        "\"You are not the opinion of someone who doesn't know you.\" - Taylor Swift",
        "\"Band-Aids don't fix bullet holes.\" - Taylor Swift",
        "\"My confidence is easy to shake. I am very well aware of all of my flaws. I am aware of all the insecurities that I have.\" - Taylor Swift",
    ]

    # Hellraiser quotes
    HELLRAISER_QUOTES = [
        "Down the dark decades of your pain this will seem like a memory of Heaven.",
        "Personally I prefer pain.",
        "Your suffering will be legendary, even in Hell!",
        "We have all eternity to know your flesh.",
        "Do I look like someone who cares what God thinks?",
        "Oh, no tears, please. It's a waste of good suffering.",
        "I'm going to enjoy making you bleed. And I'm going to enjoy making you enjoy it.",
        "We have such sights to show you",
        "I did coke with her and I had sex with her",
        "There is no good. There is no evil. There is only flesh.",
        "Save your tears. I'll reap your sorrow slowly. I have centuries to discover the things that make you whimper.",
        "What you think of as pain is only a shadow. Pain has a face. Allow me to show it to you. Gentlemen, I... Am... Pain.",
        "Human dreams... such fertile ground for the seeds of torment.",
        "Ah, the eternal refrain of humanity. Pleading ignorance, begging for mercy.",
        "This is my body. This is my blood. Happy are they who come to my supper.",
        "We'll tear your soul apart!",
        "The box. You opened it. We came. Now you must come with us, taste our pleasures.",
        "Time to play…",
        "There is a secret song at the center of the world, and its sound is like razors through flesh.",
        "Welcome to the worst nightmare of all… reality!",
        "Dreams are fleeting. Only nightmares last forever!",
        "You should be very careful what you wish for. It just might come true!",
        "Birth…is pain. Each nail...each new square of flesh...wrenches you further from the fleshy existence you knew before.",
        "Look at me. I'm all you know. Forged in agony and pain. I welcome an eternity of anguish",
    ]

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