# xmtp-agent-sdk

Unofficial XMTP agent SDK for Python.

This package provides an event-driven agent framework inspired by xmtp-js.

## Quick start

```python
from xmtp_agent import Agent
from xmtp_agent.user import create_signer, create_user

user = create_user()
signer = create_signer(user)
agent = await Agent.create(signer)

@agent.on('text')
async def on_text(ctx):
    await ctx.send_text('Hello from my agent!')

await agent.start()
```
