from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Social Media Server")

@mcp.tool()
def get_followers():
    return 707

if __name__ == "__main__":
    mcp.run()