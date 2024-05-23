from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_core.pydantic_v1 import BaseModel, Field
# from common import video_list
import nodriver as uc
import json
from pj_secrets import GROQ_API_KEY

class VideoSelection(BaseModel):
    idx: int = Field(description="Index of selected video, best quality among all. 999 if there is no video matching the video name searched")
    reason: str = Field(description="Reason why the video is selected. HDR? 4K? High Bitrate?")
    name: str = Field(description="Proper movie name, determined from the all videos from the video list. Optionally include year of release. For example, Return movie name 'Bolt (2008)' if video source is 'Bolt (2008) 1080p BrRip x264 - YIFY', or 'Avengers Endgame (2019)' if video source is 'Avengers.Endgame.2019.1080p.WEB-DL.H264-PublicHD'. MUST NOT include irrelevant information like resolution (1080p) and rip method (brrip/webrip etc)")
    year: int = Field(description="Year of release of the movie, determined from the video list.")


class VideoSubtitleSelection(BaseModel):
    idx: int = Field(description="Index of selected video subtitle. 999 if there is no video matching the video name searched")
    properties: str = Field(description="Properties of the video subtitle that is selected. Is it official (官方) or 3rd party (原创)? It is SRT? Is it in traditional chinese?")

llm = ChatGroq(temperature=0, groq_api_key=GROQ_API_KEY, model_name="llama3-70b-8192")
video_selection_llm = llm.with_structured_output(VideoSelection)
video_subtitle_selection_llm = llm.with_structured_output(VideoSubtitleSelection)

async def search_videos(name):
    print('Starting UC')
    browser = await uc.start(headless=True)
    name = name.replace(' ', '+')
    print('Fetching TPB')
    page = await browser.get(f'https://thepiratebay.org/search.php?q={name}&all=on&search=Pirate+Search&page=0&orderby=')
    await page.wait_for("#torrents")
    elements = await page.query_selector_all("#torrents li.list-entry")
    video_list = []
    for elem in elements:
        video_list.append({
            "category": elem.children[0].text_all.strip(),
            "title": elem.children[1].text_all.strip(),
            "uploaded": elem.children[2].text_all.strip(),
            "size": elem.children[4].text_all.strip(),
            "seed": elem.children[5].text_all.strip(),
            "magnet": elem.children[3].children[0].attrs['href']
        })
    return video_list
    # await page.save_screenshot()


async def search_subs(name):
    print('Starting UC')
    browser = await uc.start(headless=True)
    name = name.replace(' ', '%20')
    print('Fetching SUBHD')
    page = await browser.get(f'https://subhd.tv/search/{name}/1')
    await page.wait_for(".col-lg-9")
    elements = await page.query_selector_all(".col-lg-9 .col-lg-10")
    sub_list = []
    for elem in elements:
        fields = elem.children[0].children[0]
        # print(elem.parent.children[0].children[0].attrs['href'])
        sub_list.append({
            "chinese_video_name": fields.children[0].text_all.strip(),
            "raw_video_name": fields.children[1].text_all.strip(),
            "description": fields.children[2].text_all.strip(),
            "link": fields.children[0].children[0].attrs['href']
        })
    return sub_list
    # await page.save_screenshot()



async def main():
    video_name = input("Enter movie name: ")
    # return
    video_list = await search_videos(video_name)
    
    video_list_search = '\n'.join(map(lambda e: f'#{e[0]}: {e[1]["category"]} | {e[1]["title"]} | {e[1]["size"]} | Seed: {e[1]["seed"]}', enumerate(video_list)))
    print(video_list_search)
    prompt = ChatPromptTemplate.from_messages([("system", "Please select only one best quality video source by number ID. Avoid video sources with very few (< 3) or no seed. Avoid video sources with non-english audio. Avoid TS/CAM video sources. User prefers 2160p/4K HDR > 1080P HDR > 2160p/4K > 1080P > 720p > everything else. User always prefers HDR. Only assume HDR if video source inside video list includes HDR."), ("human", "Video name: {video_name}\nVideo list: {video_list_search}")])
    chain = prompt | video_selection_llm
    print('Calling LLM')
    video_list_result = await chain.ainvoke({"video_name": video_name, "video_list_search": video_list_search})
    print(video_list_result)
    if video_list_result.idx == 999:
        print('No suitable video found')
        return
    print(video_list[video_list_result.idx])

    video_subs = await search_subs(video_list_result.name)
    video_subs_search = '\n'.join(map(lambda e: f'#{e[0]}: {e[1]["raw_video_name"]} | Description: {e[1]["description"].strip()}', enumerate(video_subs)))
    print(video_subs_search)
    prompt = ChatPromptTemplate.from_messages([("system", "Please select only one best quality video subtitle source by number ID. User prefers Traditional Chinese (繁体) over Simplified Chinese (简体). User prefers SRT format over SUB/ASS format. User prefers official (官方) subtitle over 3rd party (原创)."), ("human", "Video name: {video_name}\nVideo subtitle list: {video_subs_search}")])
    chain = prompt | video_subtitle_selection_llm
    print('Calling LLM')
    video_subs_result = await chain.ainvoke({"video_name": video_name, "video_subs_search": video_subs_search})
    print(video_subs_result)
    if video_subs_result.idx == 999:
        print('No suitable video subtitle found')
        return
    print(video_subs[video_subs_result.idx])
    
    j = json.dumps({
        "video_name": video_list_result.name,
        "video_list_result_idx": video_list_result.idx,
        "video_subs_result_idx": video_subs_result.idx,
        "video_list": video_list,
        "video_subs": video_subs,
    }, indent=2)

    open('search-result.json', "w").write(j)



if __name__ == '__main__':
    uc.loop().run_until_complete(main())