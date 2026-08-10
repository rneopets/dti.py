import asyncio

from dti import Client
from dti.errors import NeopetNotFound


async def main() -> None:
    dti_client = Client()

    try:
        pet = await dti_client.fetch_neopet_by_name("diceroll123456789")

        await pet.render("./pet.png")
    except NeopetNotFound as e:
        # raised if the pet by that name does not exist
        print(e)


asyncio.run(main())
