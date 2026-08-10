import asyncio

from dti import Client
from dti.errors import OutfitNotFound


async def main() -> None:
    dti_client = Client()

    try:
        outfit = await dti_client.fetch_outfit(1234567890)

        await outfit.render("./outfit.png")
    except OutfitNotFound as e:
        import traceback

        traceback.print_exc()
        # raised if the outfit by that id does not exist
        print(e)


asyncio.run(main())
