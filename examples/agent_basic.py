import asyncio

from xmtp_agent import Agent
from xmtp_agent.user import create_signer, create_user


async def main() -> None:
    user = create_user()
    signer = create_signer(user)
    agent = await Agent.create(signer)

    @agent.on('text')
    async def on_text(ctx) -> None:
        await ctx.send_text('Hello from my XMTP agent!')

    await agent.start()


if __name__ == '__main__':
    asyncio.run(main())
