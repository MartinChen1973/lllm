## ⬇️ Local agent tools (Python callables), merged with MCP tools in main.py
from tools.internet_search import get_local_tools, internet_search
from tools.skill_tools import get_skill_tools

__all__ = ["get_local_tools", "get_skill_tools", "internet_search"]
