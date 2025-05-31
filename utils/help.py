from discord.ext import commands
import discord

class CustomHelpCommand(commands.HelpCommand):
    def get_command_signature(self, command:commands.Command):
        # return 'someone get_command_signature\'d here'
        return f"{self.context.clean_prefix}{command.qualified_name} {command.signature}"

    async def send_bot_help(self, mapping):
        embed = discord.Embed(title="Command List", color=discord.Color.blue())
        for cog, commands_list in mapping.items():
            filtered = await self.filter_commands(commands_list, sort=True)
            if filtered:
                name = cog.qualified_name if cog else "Miscellaneous"
                value = "\n".join(f"`{self.get_command_signature(cmd)}` - {cmd.short_doc}" for cmd in filtered)
                embed.add_field(name=name, value=value, inline=False)
        destination = self.get_destination()
        await destination.send(embed=embed)

    async def send_command_help(self, command:commands.Command):
        embed = discord.Embed(title=f"Help for `{command}`", color=discord.Color.green())
        embed.add_field(name="Usage", value=f"`{self.get_command_signature(command)}`", inline=False)
        embed.add_field(name="Description", value=command.help or "No description provided.", inline=False)
        destination = self.get_destination()
        await destination.send(embed=embed)

    async def send_error_message(self, error):
        destination = self.get_destination()
        await destination.send(f"Error: {error}")