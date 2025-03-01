import re
import random
import discord
from discord.ext import commands
import dotenv
import os
from datetime import datetime

# Load environment variables (ensure you have a .env file with DISCORD_BOT_TOKEN defined)
dotenv.load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
PREFIX = "!"

# Expanded offensive words list (singular, plural, and common variations)
OFFENSIVE_WORDS = [
    # Racial slurs and hate terms
    "nigger", "nigga", "niggers", "niggas", "nig",
    # Sexual violence/rape
    "rape", "raped",
    # Derogatory terms and variations
    "randi", "randis", "raand", "randiya",
    "whore", "whores",
    "bitch", "bitches",
    "aryan", "aryans",
    "pajeet", "pajeeta", "pajeets", "pajeetas", "pajee",
    "chut",
    "lund",
    "fuddi", "fuddia", "fuddiya",
    "loda",
    # Notable hate figures or their names
    "hitler", "hilters", "epstein",
    # Minor terms often used in internet abuse
    "loli", "lolis",
    "child porn", "cp",
    "cunt", "cunts",
    "tranny", "trannies", "cunny",
    "kike", "kikes",
    "nazi",
    "retard",
    "jew", "jews",
    "fag", "faggot", "fags", "faggots",
    "nog",
    "zoophile", "zoophilia",
    "fent", "fenatyl",
    "acid", "lsd", "mdma", "heroine",
    "slut", "sluts",
    "kill yourself",
    "mongool", "chud", "chuddie"
]

# Blackout symbols (used only once per word if chosen)
CENSOR_CHARS = ['*', '█', '▪', '■', '●']

CENSOR_MAP = {
    'a': ['4', '@', 'ä', 'á', 'à', 'â', 'ã', 'å', 'α', 'ª', 'ạ', 'ą', 'ꬱ'],
    'b': ['8', 'ß', 'β'],
    'c': ['<', 'ç', '¢', 'ϛ', 'Ͻ'],
    'd': ['đ', 'ð', 'ɗ', 'Δ'],
    'e': ['3', 'ë', '€', '𝜺', '𝟄'],
    'f': ['ƒ', 'ꜰ', 'ᶠ', 'Ꞙ', 'ℱ'],
    'g': ['9', 'ġ', '⅁', 'ᶃ'],
    'h': ['#', 'ħ', 'һ', '𝚷'],
    'i': ['1', '!', '|', 'í', 'ï', 'î', 'ì', 'ι'],
    'j': ['ĵ', 'ʝ', 'Ʝ', 'ᴶ'],          # removed 'j'
    'k': ['κ', 'ꝁ', 'ᴷ', '𝛋'],          # removed 'k'
    'l': ['1', 'ł', 'ӏ', 'ḷ', 'ℓ'],      # removed 'l'
    'm': ['ꟿ', 'ṃ', 'ɱ', 'ꟽ', 'Ⲙ'],
    'n': ['ŋ', 'ն', 'ꞃ', 'ͷ'],           # removed 'n'
    'o': ['0', 'ϴ', 'ö', 'ø', 'º', '〇', '𝞡'],
    'p': ['þ', 'ϼ', '𝝆', 'ϱ'],
    'q': ['ℚ', 'ɋ', 'Ꝗ', 'Ϙ'],          # removed 'q'
    'r': ['®', 'Ϡ', 'ʁ', 'Γ'],          # removed 'r'
    's': ['$', '5', '§', 'ʂ'],
    't': ['7', '+', '†', 'τ'],
    'u': ['ú', 'ü', 'û', 'ù', 'v'],      # removed 'u'
    'v': ['ⱽ', 'ꝟ', '𝛝', 'ϑ'],
    'w': ['ŵ', 'ω', '𝞏', 'ῷ'],           # removed 'w'
    'x': ['χ', 'ҳ', '𝛞', '⤫'],          # removed 'x'
    'y': ['ÿ', '𝟁', '𝛹', '𝜓'],          # removed 'y'
    'z': ['2', 'ž', 'ʐ', 'ζ']
}

# Precompile a regex pattern for offensive words (using word boundaries).
pattern = re.compile(
    r'(?<!\w)(?:' + '|'.join(re.escape(word) for word in OFFENSIVE_WORDS) + r')(?!\w)',
    flags=re.IGNORECASE
)

def censor_word(word: str) -> str:
    """
    Returns a partially censored version of an offensive word by replacing 1–2 characters.
    Only eligible characters (alphanumeric) are replaced.
    With a 25% chance, a blackout symbol from CENSOR_CHARS is used (only once per word);
    otherwise, a random substitution from CENSOR_MAP is used.
    """
    letters = list(word)
    eligible = [i for i, ch in enumerate(letters) if ch.isalnum()]
    if not eligible:
        return word

    num_to_replace = min(random.choice([1, 3]), len(eligible))
    positions = random.sample(eligible, num_to_replace)
    used_blackout = False
    rc = random.choice  # local alias for speed

    for pos in positions:
        ch = letters[pos]
        lower_ch = ch.lower()
        if not used_blackout and random.random() < 0.25:
            replacement = rc(CENSOR_CHARS)
            used_blackout = True
        elif lower_ch in CENSOR_MAP:
            replacement = rc(CENSOR_MAP[lower_ch])
            if ch.isupper():
                replacement = replacement.upper()
        else:
            replacement = ch
        letters[pos] = replacement
    return "".join(letters)

def censor_message(content: str) -> str:
    """
    Returns a censored version of the message content by replacing offensive words partially.
    """
    return pattern.sub(lambda m: censor_word(m.group()), content)

# Set up Discord bot (ensure message content intent is enabled in the developer portal)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user} (ID: {bot.user.id})")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.content:
        return

    if pattern.search(message.content):
        censored_text = censor_message(message.content)
        try:
            await message.delete()
        except discord.Forbidden:
            print("Missing permissions to delete message.")
            return
        except discord.HTTPException as err:
            print(f"Failed to delete message: {err}")
            return

        # Create a rich embed for the response
        embed = discord.Embed(
            title="Message Censored",
            description=f"Your message was censored:\n\n`{censored_text}`",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(
            name=message.author.display_name,
            icon_url=message.author.avatar.url if message.author.avatar else None
        )
        embed.set_footer(text="tmkr")

        try:
            await message.channel.send(content=message.author.mention, embed=embed)
        except discord.HTTPException as err:
            print(f"Failed to send censored message: {err}")
        return

    await bot.process_commands(message)

if __name__ == "__main__":
    def generate_invite_link(client_id: str, permissions: int) -> str:
        base_url = "https://discord.com/oauth2/authorize"
        scope = "bot"
        return f"{base_url}?client_id={client_id}&permissions={permissions}&scope={scope}"
    
    invite_link = generate_invite_link(client_id='1345424377558208622', permissions=1689934340025408)
    print(f"Invite your bot with this link:\n{invite_link}\n")
    
    bot.run(TOKEN)
