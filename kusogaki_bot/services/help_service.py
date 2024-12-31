from typing import Dict, Optional

from discord import Embed

from kusogaki_bot.utils.embeds import EmbedType, get_embed


class HelpService:
    def __init__(self):
        self.command_details: Dict = {
            'gtaquiz': {
                'title': 'GTA Quiz Game',
                'description': """
The GTA Quiz Game allows users to participate in trivia games about GTA.

**Subcommands:**
• `start` - Begins a new quiz game session
• `join` - Join an ongoing game before it starts
• `stop` - Ends the current game session

**Examples:**
```
kuso gtaquiz start
kuso gtaquiz join
kuso gq stop
```

**Aliases:** `gq`
""",
            },
            'poll': {
                'title': 'Poll System',
                'description': """
Create and manage polls. This command is restricted to staff members.

**Usage:**
`kuso poll <question> <duration> <multiple> <options...>`

**Parameters:**
• `question` - The poll question
• `duration` - Duration in hours
• `multiple` - Allow multiple choices (true/false)
• `options` - Space-separated poll options

**Related Commands:**
• `endpoll <question>` - End an active poll
• `listpolls` - Show all active polls

**Example:**
```
kuso poll "Favorite manga?" 24 false "One Piece" "Naruto" "Bleach"
```
""",
            },
            'reminder': {
                'title': 'Reminder System',
                'description': """
Set and manage personal reminders.

**Subcommands:**
• `set <time> <message>` - Create a new reminder
• `list` - View your active reminders
• `delete <index>` - Remove a reminder

**Time Format:**
Use combinations of: `d` (days), `h` (hours), `m` (minutes)

**Examples:**
```
kuso reminder set 1h30m Take a break
kuso rem list
kuso reminder delete 1
```

**Aliases:** `rem`
""",
            },
            'thread': {
                'title': 'Thread Management',
                'description': """
Create and manage private threads. Requires "Manage Threads" permission.

**Subcommands:**
• `create <role> <name> [message]` - Create a thread immediately
• `schedule <role> <time> <name> [message]` - Schedule a thread
• `list` - View scheduled threads
• `delete <id>` - Remove a scheduled thread

**Examples:**
```
kuso thread create @Role "thread name" "Initial message"
kuso thread schedule @Role 2h "Future thread" "Starting soon!"
```
""",
            },
            'awaiz': {
                'title': 'Food Counter',
                'description': """
Track food mentions for Awaiz.

**Commands:**
• `awaiz` - Increment the counter
• `awaizcount` - Display current count

**Aliases:**
• `awaiz` → `caseoh`
• `awaizcount` → `drywall`
""",
            },
        }

    async def get_overview_embed(self) -> Embed:
        """Generate the overview embed for the help command."""
        description = """
Welcome to the Kusogaki Bot! Here's a quick overview of what I can do:

* **GTA Quiz Game**: Run GTA style guessing game
* **Polls**: Create and manage polls (Staff only)
* **Reminders**: Set and manage reminders
* **Threads**: Create and schedule private threads
* **Food Counter**: Track food mentions
### Command List
To see all available commands, click the `View all Commands` button below.

For detailed information about a command, use: `kuso help <command>`.
"""
        return await get_embed(EmbedType.NORMAL, 'Kusogaki Bot', description)

    async def get_all_commands_embed(self) -> Embed:
        """Generate the embed containing all commands."""
        description = """
**GTA Quiz Game Commands** (Base: `gtaquiz`, `gq`)
• `kuso gtaquiz start` - Start a new GTA quiz game
• `kuso gtaquiz join` - Join an ongoing game
• `kuso gtaquiz stop` - Stop the current game

**Poll Commands** (Staff Only)
• `kuso poll <question> <duration> <multiple> <options...>` - Create a poll
• `kuso endpoll <question>` - End an active poll
• `kuso listpolls` - List all active polls

**Reminder Commands** (Base: `reminder`, `rem`)
• `kuso reminder set <time> <message>` - Set a new reminder
• `kuso reminder list` - List your active reminders
• `kuso reminder delete <index>` - Delete a reminder

**Thread Commands** (Requires "Manage Threads" permission)
• `kuso thread create <role> <name> [message]` - Create a private thread
• `kuso thread schedule <role> <time> <name> [message]` - Schedule a thread
• `kuso thread list` - List scheduled threads
• `kuso thread delete <id>` - Delete a scheduled thread

**Food Counter Commands**
• `kuso awaiz` (alias: `caseoh`) - Increment food counter
• `kuso awaizcount` (alias: `drywall`) - Display current count
"""
        return await get_embed(EmbedType.INFORMATION, 'All Commands', description)

    async def get_command_help(self, command: str) -> Optional[Embed]:
        """Get detailed help for a specific command."""
        command = command.lower()
        if command in self.command_details:
            details = self.command_details[command]
            return await get_embed(
                EmbedType.INFORMATION, details['title'], details['description']
            )
        return None

    async def get_command_not_found_embed(self, command: str) -> Embed:
        """Generate an error embed for when a command is not found."""
        return await get_embed(
            EmbedType.ERROR,
            'Command Not Found',
            f'The command `{command}` was not found. Use `kuso help` to see all available commands.',
        )
