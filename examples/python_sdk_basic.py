import asyncio

from xmtp import Client
from xmtp.signers import create_signer
from xmtp.types import ClientOptions


async def main() -> None:
    signer = create_signer('0xYOUR_PRIVATE_KEY')
    client = await Client.create(signer, ClientOptions(env='dev'))

    dm = await client.conversations.new_dm('0x...')
    await dm.send('Hello from Python!')


if __name__ == '__main__':
    asyncio.run(main())
