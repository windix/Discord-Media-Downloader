from arguments import get_args

from discord_dl import DiscordDownloader

if __name__ == "__main__":
    options = vars(get_args())
    dd = DiscordDownloader(options)
    dd.run()
