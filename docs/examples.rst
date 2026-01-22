Examples
========

Python SDK
----------

.. code-block:: python

   import asyncio

   import xmtp

   from xmtp import Client
   from xmtp.signers import create_signer
   from xmtp.types import ClientOptions


   async def main() -> None:
       signer = create_signer('0xYOUR_PRIVATE_KEY')
       options = ClientOptions(env='production', disable_history_sync=True)
       client = await Client.create(signer, options)

       dm = await client.conversations.new_dm('0x...')
       await dm.send(f'Hello from xmtp-py {xmtp.__version__}')


   asyncio.run(main())

Agent SDK
---------

.. code-block:: python

   import asyncio

   import xmtp

   from xmtp_agent import Agent
   from xmtp_agent.user import create_signer, create_user
   from xmtp.types import ClientOptions


   async def main() -> None:
       user = create_user()
       signer = create_signer(user)
       agent = await Agent.create(signer, ClientOptions(env='production'))

       dm = await agent.client.conversations.new_dm('0x...')
       await dm.send(f'Hello from xmtp-py {xmtp.__version__}')


   asyncio.run(main())
