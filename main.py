import requests
import time
import logging
import sys
import uuid
import re
import random
import json
import base64

logging.basicConfig(level=logging.INFO)

CONNECT_TIMEOUT = 20
READ_TIMEOUT = 20
TIMEOUT = (CONNECT_TIMEOUT, READ_TIMEOUT)
VIDEO_DIR = "out/"
RESULTS_DIR = "results/"
CHECK_INTERVAL_SECONDS = 30
GENERATION_COOLDOWN_SECONDS = 30
ERRORS_COUNT = 0    # Total image generation failures
SUCCESS_COUNT = 0   # Total image generation successes
MAX_ERRORS = 1000   # Max errors before the script gives up and exits
CHECK_PROCESSING_RETRIES = 2
PROMPT_RESULTS = {}
PROMPT_RESULTS_FILE = f"{RESULTS_DIR}results_{str(uuid.uuid4())}.json"
PROMPT_FILE = "prompts.json"
HOSTNAME = base64.b64decode("aGFpbHVvYWkuY29t").decode('utf-8')
API = f"https://{HOSTNAME}/api/"
API_V1 = f"https://{HOSTNAME}/v1/api/"
GLOBAL_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
}


def write_dict_to_file(data: dict, filename: str):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)


def track_prompt_result(prompt: str, inc_generate_success: bool, inc_prompt_refused: bool, inc_check_failed: bool):
    global PROMPT_RESULTS, PROMPT_RESULTS_FILE
                                                # The meaning of the keys in results.json: 
    KEY_GENERATE_SUCCESS = "generate_success"   # A video was generated/downloaded for this prompt
    KEY_PROMPT_REFUSED = "prompt_refused"       # The video failed to generate due to the prompt being refused, likely safety check on prompt
    KEY_CHECK_FAILED = "check_failed"           # An pending video was removed prior to download, likely safety check on produced video
    
    prompt_error = PROMPT_RESULTS.get(prompt, {})
    prompt_refused = prompt_error.get(KEY_PROMPT_REFUSED, 0)
    check_failed = prompt_error.get(KEY_CHECK_FAILED, 0)
    generate_success = prompt_error.get(KEY_GENERATE_SUCCESS, 0)

    if inc_generate_success:
        generate_success += 1

    if inc_prompt_refused:
        prompt_refused += 1

    if inc_check_failed:
        check_failed += 1

    PROMPT_RESULTS[prompt] = {
        KEY_GENERATE_SUCCESS: generate_success,
        KEY_PROMPT_REFUSED: prompt_refused,
        KEY_CHECK_FAILED: check_failed
    }

    return write_dict_to_file(PROMPT_RESULTS, PROMPT_RESULTS_FILE)


def load_json_list_from_file(filename):
  with open(filename, 'r') as f:
    data = json.load(f)

  if not isinstance(data, list):
    raise ValueError("JSON file does not contain an array.")
  
  if len(data) == 0:
      raise ValueError("JSON list is empty")

  return data


def translate_chinese_to_english(chinese_text: str):
    if not chinese_text:
        return ""
    translation_dict = {
        "上一个视频任务未完成，请稍后再试": "The previous video task was not completed, please try again later",
        "正在生成，退出后AI会继续生成": "Generating, AI will continue to generate after exiting",
        "文案内容有点问题，换个内容试试呢": "There is something wrong with the content of the copy. Let's try changing it."
    }

    if chinese_text in translation_dict:
        return translation_dict[chinese_text]
    
    return chinese_text.replace("前面还有", "Ahead of you are ") \
        .replace("位", " people") \
        .replace("预计等待", "Expected waiting time ") \
        .replace("分钟", " minutes")


def to_snake(string):
    string = re.sub(r'(?<=[a-z])(?=[A-Z])|[^a-zA-Z]', ' ', string).strip().replace(' ', '_')
    joined = ''.join(string.lower())
    return joined.replace("__", "_")


def translate_status_info_message(json):
    message = json.get("statusInfo", {}).get("message")
    if message:
        json["statusInfo"]["message"] = translate_chinese_to_english(message)
    return json


def init_session() -> requests.Session:
    s = requests.Session()
    return s


def register(session: requests.Session, uuid) -> str:
    register_url = f"{API_V1}user/device/register?device_platform=web&app_id=3001&version_code=22201&uuid={uuid}&os_name=Mac&browser_name=firefox&cpu_core_num=6&browser_language=en-US&browser_platform=MacIntel&screen_width=1680&screen_height=1050&unix={time.time}"
    r = session.post(url=register_url, timeout=TIMEOUT, headers=GLOBAL_HEADERS, json={"uuid":uuid})
    if not r.ok:
        logging.error(f"failed to register: {r.status_code} {r.text}")
    register_json = r.json()
    device_id = register_json.get("data", {}).get("deviceIDStr")
    logging.info(f"Registered with uuid {uuid}, got device_id {device_id}")

    return device_id


def login_phone(session: requests.Session, uuid, device_id):
    phone_url = f"{API_V1}user/login/phone?device_platform=web&app_id=3001&version_code=22201&uuid={uuid}&device_id={device_id}&os_name=Mac&browser_name=firefox&cpu_core_num=6&browser_language=en-US&browser_platform=MacIntel&screen_width=1680&screen_height=1050&unix={time.time}"
    r = session.post(url=phone_url, timeout=TIMEOUT, headers=GLOBAL_HEADERS, json={"loginType":"3","adInfo":{}})
    if not r.ok:
        logging.error(f"failed to phone: {r.status_code} {r.text}")

    phone_json = r.json()
    token = phone_json.get("data", {}).get("token")
    logging.info(f"Got token: {token}\n")
    return token


def call_generate_video(session: requests.Session, prompt: str, token: str, my_uuid: str, device_id: str) -> str:
    prompt_url = f"{API}multimodal/generate/video?device_platform=web&app_id=3001&version_code=22201&uuid={my_uuid}&device_id={device_id}&os_name=Mac&browser_name=firefox&cpu_core_num=6&browser_language=en-US&browser_platform=MacIntel&screen_width=1680&screen_height=1050&unix={time.time()}"

    headers = GLOBAL_HEADERS | {"token": token}
    r = session.post(url=prompt_url, json={"desc": prompt}, timeout=TIMEOUT, headers=headers)
    if not r.ok:
        logging.error(f"Prompt request not OK: {r.status_code} - {r.text}")
        return ""
    
    prompt_json = r.json()
    generated_id = prompt_json.get("data", {}).get("id")
    if not generated_id:
        logging.error(f"Video generation was not successful: {translate_status_info_message(prompt_json)}")
        return ""
    
    return prompt_json.get("data", {}).get("id")


def check_processing(session: requests.Session, id, uuid, device_id, token):
    processing_url = f"{API}multimodal/video/processing?idList={id}&device_platform=web&app_id=3001&version_code=22201&uuid={uuid}&device_id={device_id}&os_name=Mac&browser_name=firefox&cpu_core_num=6&browser_language=en-US&browser_platform=MacIntel&screen_width=1680&screen_height=1050&unix={time.time()}"

    headers = GLOBAL_HEADERS | {"token": token}
    r = session.get(url=processing_url, timeout=TIMEOUT, headers=headers)
    if not r.ok:
        logging.error(f"Check request not OK: {r.status_code} - {r.text}")
        return False

    check_json = r.json()
    if not check_json: # Does this occur?
        logging.error(f"check failed: {r.text}")
        return False
    
    videos = check_json.get("data", {}).get("videos", [{}])
    if len(videos) == 0:
        logging.error(f"Unexpectedly got no videos: {check_json}")
        return False

    video = videos[0]
    return video


def download_video(session: requests.Session, video_url, filename) -> str:
    headers = GLOBAL_HEADERS | {"token": token}
    r = session.get(url=video_url, timeout=TIMEOUT, headers=headers)
    if not r.ok:
        logging.error(f"Download failed: {r.status_code}")
    
    fn = f"{VIDEO_DIR}{filename}.mp4"
    with open(fn, mode="wb") as file:
        file.write(r.content)

    return filename


def handle_generation(session, prompt, token, my_uuid, device_id):
    logging.info(f"Starting generation:\n\t{prompt}")
    generated_id = call_generate_video(session, prompt, token, my_uuid, device_id)

    if not generated_id:
        track_prompt_result(prompt, False, True, False)
        raise Exception("Prompt generation failed. Giving up on this generation.")
    
    check_retries = 0

    while True:
        if check_retries >= CHECK_PROCESSING_RETRIES:
            track_prompt_result(prompt, False, False, True)
            raise Exception("Check processing failed too many times. Giving up on this generation.")

        # Check processing loop
        video = check_processing(session, generated_id, my_uuid, device_id, token)
        if not video:
            time.sleep(CHECK_INTERVAL_SECONDS)
            check_retries += 1
            continue

        status = video.get("status")
        percent = video.get("percent")
        videoURL = video.get("videoURL")
        message = translate_chinese_to_english(video.get("message", ""))
        logging.info(f"Check - ({status}) {percent}% - {message}")

        if videoURL:
            logging.info(f"Video URL: {videoURL}")
            subfolder_path = to_snake(prompt)
            filename = f"{subfolder_path}_{generated_id}"
            file = download_video(session, videoURL, filename)
            logging.info(f"Video downloaded: {file}")
            track_prompt_result(prompt, True, False, False)
            return
        
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    # Startup
    session = init_session()
    my_uuid = str(uuid.uuid4())
    device_id = register(session, my_uuid)
    token = login_phone(session, my_uuid, device_id)

    while True:
        if ERRORS_COUNT > MAX_ERRORS:
            logging.error("Killing... too many errors")
            sys.exit(1)
        try:
            all_prompts = load_json_list_from_file(PROMPT_FILE)
            prompt = random.choice(all_prompts)
            handle_generation(session, prompt, token, my_uuid, device_id)
            SUCCESS_COUNT += 1
        except Exception as e:
            ERRORS_COUNT += 1
            logging.error(e)
        
        logging.info(f"Sleeping {GENERATION_COOLDOWN_SECONDS} seconds before next generation... ({SUCCESS_COUNT} succeeded, {ERRORS_COUNT} failed)\nSee {PROMPT_RESULTS_FILE} for results.\n")
        time.sleep(GENERATION_COOLDOWN_SECONDS)
