Examples
========

Python SDK
----------

.. code-block:: python

   import asyncio

   from xmtp import Client
   from xmtp.signers import create_signer
   from xmtp.types import ClientOptions


   async def main() -> None:
       signer = create_signer('0xYOUR_PRIVATE_KEY')
       options = ClientOptions(env='dev')
       client = await Client.create(signer, options)

       dm = await client.conversations.new_dm('0x...')
       await dm.send('Hello from Python!')


   asyncio.run(main())

Agent SDK
---------

.. code-block:: python

   import asyncio

   from xmtp_agent import Agent
   from xmtp_agent.user import create_signer, create_user


   async def main() -> None:
       user = create_user()
       signer = create_signer(user)
       agent = await Agent.create(signer)

       @agent.on('text')
       async def handle_text(ctx):
           await ctx.send_text('Hello from my XMTP Agent!')

       await agent.start()


   asyncio.run(main())
