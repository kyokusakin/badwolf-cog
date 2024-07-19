from redbot.core import commands, Config
import discord
import random

class Counting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=927537080882561025)
        default_guild = {
            "counting_channel": None,
            "current_count": 0,
            "count_board": {},
            "last_counter": None,
            "highest_number": 0,
            "bot_sent_last_message": False,
        }
        self.config.register_guild(**default_guild)
        self.image = [
            "https://media.tenor.com/4BRzlmo2FroAAAAC/kendeshi-anime-smh.gif",
            "https://i.imgur.com/douh7U1.gif",
            "https://i.imgur.com/5niochn.gif",
            "https://i.pinimg.com/originals/63/c0/c6/63c0c6b632dfffd790b60a87007f1bfd.gif",
            "https://i.imgur.com/zuCcShq.gif",
            "https://i.pinimg.com/originals/fa/cc/56/facc56fbd83bf6f8e7ad86bd6a73976c.gif",
            "https://i.gifer.com/79UR.gif",
            "https://memeprod.ap-south-1.linodeobjects.com/user-maker-thumbnail/3dd8f15de8466c5247458d75b7223189.gif"
            ]

    @commands.mod_or_can_manage_channel()
    @commands.hybrid_command()
    async def setcounting(self, ctx, channel: discord.TextChannel):
        """Set a counting channel for the game to began!"""
        await self.config.guild(ctx.guild).counting_channel.set(channel.id)
        await ctx.send(f"Counting channel has been set to {channel.mention}")

    @commands.hybrid_command()
    async def currentcount(self, ctx):
        """Display the current count"""
        count = await self.config.guild(ctx.guild).current_count()
        await ctx.send(f"目前已經數到 `{count}`")

    @commands.mod_or_can_manage_channel()
    @commands.hybrid_command()
    async def resetcountchannel(self, ctx):
        """Reset the counting!"""
        await self.config.guild(ctx.guild).counting_channel.set(None)
        await ctx.send("Counting channel has been reset.")

    @commands.hybrid_command()
    async def countrules(self, ctx):
        """Display the rules for counting."""
        rules = ("1: 一個人不能連續兩次\n"
                 "2: 每個數字都應該有輪番發言的用戶\n"
                 "3: 如果有人數錯了，那就從頭來過吧！")
        await ctx.send(rules)

    async def update_count(self, message, new_count):
        conf = self.config.guild(message.guild)
        async with conf.count_board() as board:
            board[message.author.id] = board.get(message.author.id, 0) + 1
        await conf.current_count.set(new_count)
        await conf.last_counter.set(message.author.id)
        if new_count > await conf.highest_number():
            await conf.highest_number.set(new_count)


    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.guild is None:
            return
        conf = self.config.guild(message.guild)
        channel_id = await conf.counting_channel()
        bot_sent_last_message = await conf.bot_sent_last_message()
        random_image = random.choice(self.image)
        if message.channel.id != channel_id:
            return
        try:
            count = int(message.content)
        except ValueError:
            embed3 = discord.Embed(title="數數機器人", description=f"{message.author.mention}\n 不要在這聊天!!!", color=0x2b2d31)
            embed3.set_image(url=random_image)
            response = await message.reply(embed=embed3, mention_author=True)
            await message.delete(delay=4)
            await response.delete(delay=4)
            return
        last_counter = await conf.last_counter()
        if message.author.id == last_counter:
            await message.add_reaction("❌")
            return await message.reply(embed=self.get_embed(message.author, "你不能連續數兩次!"))
        current_count = await conf.current_count()
        if count != current_count + 1:
            await conf.current_count.set(0)
            await conf.last_counter.set(None)
            highest = await conf.highest_number()
            await message.add_reaction("❌")
            return await message.reply(embed=self.get_embed(message.author, f"BAKA~ BAKA~,你算錯了!計數又得重新從1開始了!\n目前最高數字是:{highest}"))
        await self.update_count(message, count)
        await conf.bot_sent_last_message.set(False)
        await message.add_reaction("✅")

    def get_embed(self, author, description):
        random_image = random.choice(self.image)
        embed = discord.Embed(title="數數機器人", description=f"{author.mention}\n{description}", color=0x2b2d31)
        embed.set_image(url=random_image)
        return embed

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        if message.guild is None:
            return
        conf = self.config.guild(message.guild)
        counting_channel = await conf.counting_channel()
        bot_sent_last_message = await conf.bot_sent_last_message()
        if message.channel.id == counting_channel and not bot_sent_last_message:
            try:
                last_counter = await conf.last_counter()
                if message.author.id != last_counter:
                    return
                current_count = await self.config.guild(message.guild).current_count()
                await message.channel.send(f"目前已經數到 `{current_count}`")
                await conf.bot_sent_last_message.set(True)
            except:
                pass

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if after.author.bot:
            return
        if after.guild is None:
            return
        conf = self.config.guild(after.guild)
        counting_channel = await conf.counting_channel()
        bot_sent_last_message = await conf.bot_sent_last_message()
        if after.channel.id == counting_channel and not bot_sent_last_message:
            try:
                last_counter = await conf.last_counter()
                if after.author.id != last_counter:
                    return
                current_count = await self.config.guild(after.guild).current_count()
                await after.channel.send(f"目前已經數到 `{current_count}`")
                await conf.bot_sent_last_message.set(True)
            except:
                pass