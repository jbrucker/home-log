from typing import AsyncGenerator
import asyncio

async def my_async_gen() -> AsyncGenerator[int, None]:
    for n in range(4):
        yield n

# Consuming the async generator
async def main():
    async for value in my_async_gen():
        print(value)


if __name__ == '__main__':
    asyncio.run(main())
