# from common import video_list
import time
import asyncio
import os
import nodriver as uc
import json
import xmlrpc.client

from pj_secrets import ARIA2_RPC_URL, ARIA2_RPC_SECRET

async def main():
    data = json.loads(open('search-result.json', "r").read())

    # Create an XML-RPC client
    client = xmlrpc.client.ServerProxy(ARIA2_RPC_URL)
    result = client.aria2.addUri(ARIA2_RPC_SECRET, [data["video_list"][data["video_list_result_idx"]]["magnet"]])
    print(result)

    print('Starting UC')
    browser = await uc.start()
    print('Fetching SUBHD')
    page = await browser.get("https://subhd.tv" + data["video_subs"][data["video_subs_result_idx"]]["link"])
    await page.wait_for('.btn.btn-danger.down')
    button = await page.query_selector('.btn.btn-danger.down')
    print(button)
    await button.click()
    time.sleep(100)



if __name__ == '__main__':
    uc.loop().run_until_complete(main())