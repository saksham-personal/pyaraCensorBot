import re
import random
import discord
from discord.ext import commands
import dotenv
import os
from datetime import datetime, timezone

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
    "mongool", "chud", "chuddie", "jeet", "jeetas", "jeets", "jeeta",
    "incel", "incels"
]

# Blackout symbols (used only once per word if chosen)
CENSOR_CHARS = ['*', '█', '▪', '■', '●']

CENSOR_MAP = {
    'a': ['4', '@', 'α', 'ạ', 'ꬱ'],
    'b': ['8', 'ß', 'β'],
    'c': ['<', 'ç', '¢', 'ϛ', 'Ͻ'],
    'd': ['đ', 'ð', 'ɗ', 'Δ', 'ⅅ'],
    'e': ['3', 'ë', '€', '𝜺', '𝟄'],
    'f': ['ƒ', 'ꜰ', 'Ꞙ', 'ℱ'],
    'g': ['9', 'ġ', '⅁', 'ᶃ'],
    'h': ['#', 'ħ', 'һ', '𝚷'],
    'i': ['1', '!', '|', 'í', 'ï', 'î', 'ì', 'ι'],
    'j': ['ĵ', 'ʝ', 'Ʝ'],
    'k': ['κ', 'ꝁ', '𝛋'],
    'l': ['ł', 'ӏ', 'ℓ'],
    'm': ['ꟿ', 'ṃ', 'ɱ', 'ꟽ', 'Ⲙ'],
    'n': ['ŋ', 'ꞃ', 'ͷ'],
    'o': ['0', 'ϴ', 'ø', '〇', '𝞡'],
    'p': ['þ', 'ϼ', '𝝆'],
    'q': ['ℚ', 'ɋ', 'Ꝗ'],
    'r': ['ʁ', 'Γ', 'ℛ'],
    's': ['$', '5', '§', 'ʂ'],
    't': ['7', '+', '†', 'τ'],
    'u': ['ú', 'ü', 'û', 'ù', 'v'],
    'v': ['ⱽ', 'ꝟ', '𝛝', 'ϑ'],
    'w': ['ŵ', 'ω', '𝞏', 'ῷ'],
    'x': ['χ', 'ҳ', '𝛞', '⤫'],
    'y': ['ÿ', '𝟁', '𝛹', '𝜓'],
    'z': ['2', 'ʐ', 'ζ']
}

# Regex for offensive words
pattern = re.compile(
    r'(?<!\w)(?:' + '|'.join(re.escape(word) for word in OFFENSIVE_WORDS) + r')(?!\w)',
    flags=re.IGNORECASE
)

# Regex for custom emojis
emoji_pattern = re.compile(r'(<a?:\w+:\d+>)')

# Regex to detect URLs for auto-embedding
url_pattern = re.compile(r'(https?://[^\s]+)')

def censor_word(word: str) -> str:
    """Returns a partially censored version of an offensive word by replacing 1–2 characters."""
    letters = list(word)
    eligible = [i for i, ch in enumerate(letters) if ch.isalnum()]
    if not eligible:
        return word

    num_to_replace = min(random.choice([1, 2]), len(eligible))
    positions = random.sample(eligible, num_to_replace)
    used_blackout = False
    rc = random.choice

    for pos in positions:
        ch = letters[pos]
        lower_ch = ch.lower()
        if not used_blackout and random.random() < 0.15:
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
    """Censors offensive words while preserving custom emojis."""
    # Temporarily replace custom emojis
    emojis = emoji_pattern.findall(content)
    placeholders = {}
    for i, emoji in enumerate(emojis):
        placeholder = f"__EMOJI_{i}__"
        placeholders[placeholder] = emoji
        content = content.replace(emoji, placeholder)

    # Censor offensive words
    censored = pattern.sub(lambda m: censor_word(m.group()), content)

    # Restore custom emojis
    for placeholder, emoji in placeholders.items():
        censored = censored.replace(placeholder, emoji)

    return censored

def to_monospace(text: str) -> str:
    """
    Converts text to Unicode Mathematical Monospace while preserving custom emojis
    and user mentions. (We won't handle URLs here, because we want them in a separate message.)
    """
    preserve_pattern = re.compile(r'(<a?:\w+:\d+>|<@!?[0-9]+>)')
    segments = preserve_pattern.split(text)

    def convert_char(ch: str) -> str:
        if 'A' <= ch <= 'Z':
            return chr(0x1D670 + (ord(ch) - ord('A')))
        elif 'a' <= ch <= 'z':
            return chr(0x1D68A + (ord(ch) - ord('a')))
        elif '0' <= ch <= '9':
            return chr(0x1D7F6 + (ord(ch) - ord('0')))
        else:
            return ch

    converted_segments = []
    for segment in segments:
        if preserve_pattern.fullmatch(segment):
            # keep custom emojis and mentions unchanged
            converted_segments.append(segment)
        else:
            # convert everything else to monospace
            converted_segments.append("".join(convert_char(c) for c in segment))

    return "".join(converted_segments)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user} (ID: {bot.user.id})")

@bot.event
async def on_message(message: discord.Message):
    # Ignore bot or empty messages
    if message.author.bot or not message.content:
        return

    # Check if there's any offensive word
    if pattern.search(message.content):
        # Attempt to delete the original message
        try:
            await message.delete()
        except discord.Forbidden:
            print("Missing permissions to delete message.")
            return
        except discord.HTTPException as err:
            print(f"Failed to delete message: {err}")
            return

        # Censor the text
        censored_text = censor_message(message.content)

        # Identify any URLs so we can auto-embed them separately
        found_urls = url_pattern.findall(message.content)

        # Build plain-text context line
        send_as_reply = False
        parent_message = None
        if message.reference is not None:
            parent_message = message.reference.resolved
            if isinstance(parent_message, discord.Message):
                context_line = f"{message.author.mention} replied to {parent_message.author.mention}"
                send_as_reply = True
            else:
                context_line = f"{message.author.mention}"
        elif message.mentions:
            tagged = ", ".join(user.mention for user in message.mentions)
            context_line = f"{message.author.mention} tagged {tagged}"
        else:
            context_line = f"{message.author.mention}"

        # Convert the censored text (minus the URLs) to monospace
        # so that the actual link remains in the final embed text if desired.
        # But for auto-embed, we must also send each URL in a separate message.
        monospaced_text = to_monospace(censored_text)

        # Create an embed with the censored text
        embed = discord.Embed(
            title="Message Evaded",
            description=monospaced_text,
            color=discord.Color.pink(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_author(
            name=message.author.display_name,
            icon_url=message.author.avatar.url if message.author.avatar else None
        )
        embed.set_footer(text="tmkr")

        # Send the mention + embed (either as a reply or in the channel)
        if send_as_reply and parent_message is not None:
            try:
                sent_msg = await message.channel.send(
                    content=context_line,
                    embed=embed,
                    reference=parent_message
                )
            except discord.HTTPException as err:
                print(f"Failed to send reply message: {err}")
                sent_msg = await message.channel.send(content=context_line, embed=embed)
        else:
            try:
                sent_msg = await message.channel.send(content=context_line, embed=embed)
            except discord.HTTPException as err:
                print(f"Failed to send censored message: {err}")
                return

        # Finally, send each URL in its own message to auto-embed
        for url in found_urls:
            # If the link is still present in the text, or you want to ensure
            # a preview, do a separate message with just that link.
            try:
                await message.channel.send(url)
            except discord.HTTPException as e:
                print(f"Failed to send URL for auto-embed: {e}")

        return

    # If no offensive content, process commands normally
    await bot.process_commands(message)

if __name__ == "__main__":
    def generate_invite_link(client_id: str, permissions: int) -> str:
        base_url = "https://discord.com/oauth2/authorize"
        scope = "bot"
        return f"{base_url}?client_id={client_id}&permissions={permissions}&scope={scope}"
    
    invite_link = generate_invite_link(
        client_id='1345424377558208622',
        permissions=1689934340025408
    )
    print(f"Invite your bot with this link:\n{invite_link}\n")
    
    bot.run(TOKEN)
