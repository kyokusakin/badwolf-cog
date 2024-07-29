from __future__ import annotations
import os
import asyncio
from datetime import datetime, timezone
from typing import Optional
from jinja2 import Environment, FileSystemLoader

from aiohttp import web
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config

from .vexutils import format_help, format_info, get_vex_logger

log = get_vex_logger(__name__)

class UptimeResponder(commands.Cog):
    __version__ = "2.0.0"
    __author__ = "@vexingvexed, @badwolf_tw"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=418078199982063626, force_registration=True)
        self.config.register_global(port=8710)
        self.uptime = datetime.now(timezone.utc)
        self.app = web.Application()
        self.cog_dir = os.path.dirname(os.path.abspath(__file__))
        self.static_dir = os.path.join(self.cog_dir, 'static')
        self.env = Environment(loader=FileSystemLoader(os.path.join(self.cog_dir, 'templates')))
        self.runner = None

    async def cog_load(self):
        await self.start_webserver()

    async def cog_unload(self):
        await self.shutdown_webserver()

    def format_help_for_context(self, ctx: commands.Context) -> str:
        return format_help(self, ctx)

    @commands.command(hidden=True)
    async def uptimeresponderinfo(self, ctx: commands.Context):
        await ctx.send(await format_info(ctx, self.qualified_name, self.__version__))

    async def shutdown_webserver(self):
        if self.runner:
            await self.runner.cleanup()
            self.runner = None
            log.info("Web server for UptimeResponder pings has been stopped due to cog unload.")

    async def get_status(self, request: web.Request) -> web.Response:
        status = {'latency': f"{self.get_latency():.2f}", 'uptime': self.get_uptime_string()}
        return web.json_response(status)

    async def main_page(self, request: web.Request) -> web.Response:
        name = self.bot.user.name if self.bot.user else "Unknown"
        html_content = self.render_template('uptime_page.html', name=name, uptime=self.get_uptime_string(), latency=f"{self.get_latency():.2f}")
        return web.Response(text=html_content, content_type='text/html', status=200)

    def get_uptime_string(self) -> str:
        uptime = datetime.now(timezone.utc) - self.uptime
        days, remainder = divmod(int(uptime.total_seconds()), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{days:02}:{hours:02}:{minutes:02}:{seconds:02}"

    def get_latency(self) -> float:
        return self.bot.latency * 1000  # Convert to milliseconds

    def render_template(self, template_name: str, **context) -> str:
        return self.env.get_template(template_name).render(**context)

    async def static_file_handler(self, request: web.Request) -> web.Response:
        filename = request.match_info['filename']
        file_path = os.path.join(self.static_dir, filename)
        if not os.path.isfile(file_path):
            file_path_with_txt = os.path.join(self.static_dir, f"{filename}.txt")
            file_path_with_html = os.path.join(self.static_dir, f"{filename}.html")
            if os.path.isfile(file_path_with_txt):
                return web.FileResponse(file_path_with_txt)
            if os.path.isfile(file_path_with_html):
                return web.FileResponse(file_path_with_html)
            raise web.HTTPNotFound()
        return web.FileResponse(file_path)

    async def start_webserver(self, port: Optional[int] = None):
        await asyncio.sleep(1)  # Let previous server shut down if cog was reloaded
        port = port or await self.config.port()
        self.app.router.add_get("/", self.main_page)
        self.app.router.add_get("/status", self.get_status)
        self.app.router.add_route('GET', '/{filename:.*}', self.static_file_handler)
        self.runner = web.AppRunner(self.app, access_log=None)
        await self.runner.setup()
        await web.TCPSite(self.runner, port=port).start()
        log.info(f"Web server for UptimeResponder pings has started on port {port}.")

    @commands.is_owner()
    @commands.command()
    async def uptimeresponderport(self, ctx: commands.Context, port: Optional[int] = None):
        if port is None:
            current_port = await self.config.port()
            await ctx.send(f"The current port is {current_port}.\nTo change it, run `{ctx.clean_prefix}uptimeresponderport <port>`")
            return
        async with ctx.typing():
            await self.shutdown_webserver()
            try:
                await self.config.port.set(port)
                await self.start_webserver(port)
                await ctx.send(f"The web server has been restarted on port {port}.")
            except OSError as e:
                await ctx.send(f"Failed to start web server on port {port}: ```\n{e}```\nPlease choose a different port. No web server is running at the moment.")
