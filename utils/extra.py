import enum


class ChatType(enum.IntEnum):
    public = 0
    developer = 1
    private = 2
    repeat = 3


class FilterType(enum.IntEnum):
    user = 0
    server = 1


rules = """
1. No advertising is allowed in the global chat. 
2. Please refrain from sharing NSFW content in the global chat.
3. Do not share malicious links in the global chat.
4. Racial slurs are strictly prohibited in the global chat.
5. If you have any issues with a user in the global chat, please contact me directly. If I deny your request, I will provide an explanation.
6. If you have concerns about the data collected in the global chat, please DM me. I will provide information on the data collected for bot functions, as required by Discord's Terms of Service.
7. Any other concerns or questions regarding content that may violate the rules should be discussed with me privately before taking any action.
8. I have the authority to revoke access to the global chat for any reason, but this decision will always be discussed privately among the global chat moderators.
9. Moderators have the authority to enforce message blacklisting within their guild based on their established rules and guidelines.
For further questions, feel free to DM me at JDJG or join our Discord server at https://discord.gg/JdDxFpNk8J.
"""
