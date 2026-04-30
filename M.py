import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import json
import datetime
import re
import os
import random
import time
import urllib.parse
import binascii
import uuid
import secrets
import string
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Thread
import queue
import threading
import sys
import threading
import uuid
from urllib.parse import urlencode
from user_agent import generate_user_agent as g

try:
    from MedoSigner import Argus, Gorgon, Ladon, md5
    MEDOSIGNER_AVAILABLE = True
except:
    MEDOSIGNER_AVAILABLE = False

try:
    import SignerPy
    SIGNERPY_AVAILABLE = True
except:
    SIGNERPY_AVAILABLE = False

BOT_TOKEN = input("-  : ").strip()
BOT_O
bot = telebot.TeleBot(BOT_TOKEN)

user_states = {}
user_sessions = {}
user_progress_messages = {}

users_db = {
    "total_users": 0,
    "private_users": 0,
    "channels_groups": 0,
    "banned_users": 0,
    "daily_stats": {},
    "user_data": {},
    "subscribed_users": {},
    "active_subscriptions": {}
}

def conv(ts):
    return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

def get_user_info(chat_id):
    try:
        user = bot.get_chat(chat_id)
        return {
            "name": user.first_name,
            "username": user.username,
            "id": user.id
        }
    except:
        return {"name": "غير معروف", "username": "غير معروف", "id": chat_id}

def notify_new_user(chat_id):
    if chat_id == BOT_OWNER:
        return
    
    user_info = get_user_info(chat_id)
    users_db["total_users"] += 1
    users_db["user_data"][chat_id] = {
        "join_date": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "name": user_info["name"],
        "username": user_info["username"]
    }
    
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    if today not in users_db["daily_stats"]:
        users_db["daily_stats"][today] = {"users": 0, "messages": 0, "starts": 0}
    users_db["daily_stats"][today]["users"] += 1
    
    message = f"""
تم دخول شخص جديد إلى البوت الخاص بك
--------------------------------
الاسم: {user_info['name']}
معرف: @{user_info['username'] if user_info['username'] else 'لا يوجد'}
الايدي: {user_info['id']}
--------------------------------
عدد الأعضاء الكلي: {users_db['total_users']}
"""
    try:
        bot.send_message(BOT_OWNER, message)
    except:
        pass

def balance(session):
    url = "https://webcast.tiktok.com/webcast/wallet_api/fs/diamond_buy/permission_v2"
    params = {"aid": "1988"}
    headers = {
        "Cookie": f"sessionid={session}",
        "User-Agent": "Mozilla/5.0"
    }
    try:
        return requests.get(url, headers=headers, params=params, timeout=10)
    except:
        return None

def generalinfo(session):
    url = "https://www.tiktok.com/passport/web/account/info/"
    headers = {
        "accept": "*/*",
        "cookie": f"sessionid={session}",
        "user-agent": "Mozilla/5.0"
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        return r.json()
    except:
        return {"message": "error"}

def get_tiktok_user_id(username):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(f'https://www.tiktok.com/@{username}', headers=headers, timeout=10)
        if response.status_code == 200:
            html = response.text
            
            pattern1 = r'"userId":"(\d+)"'
            match1 = re.search(pattern1, html)
            if match1:
                return match1.group(1)
            
            pattern2 = r'"user_id":"(\d+)"'
            match2 = re.search(pattern2, html)
            if match2:
                return match2.group(1)
            
            pattern3 = r'user_id[\\"]*:[\\"]*(\d+)[\\"]*'
            match3 = re.search(pattern3, html)
            if match3:
                return match3.group(1)
    except:
        pass
    
    return None

def get_tiktok_level(username):
    user_id = get_tiktok_user_id(username)
    if not user_id:
        return None, "لم يتم العثور على المستخدم"
    
    url = f"https://webcast.tiktok.com/webcast/room/user_info/?aid=1988&user_id={user_id}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
        "Origin": "https://www.tiktok.com",
        "Referer": "https://www.tiktok.com/"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return None, f"خطأ في الاتصال: {response.status_code}"
        
        response_text = response.text
        
        try:
            data = response.json()
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, dict):
                        if "level" in value:
                            return str(value["level"]), None
                        if "user_level" in value:
                            return str(value["user_level"]), None
        except:
            pass
        
        patterns = [
            r'"level":\s*"?(\d+)"?',
            r'"user_level":\s*"?(\d+)"?',
            r'"support_level":\s*"?(\d+)"?',
            r'level["\']?\s*:\s*["\']?(\d+)["\']?',
            r'userLevel["\']?\s*:\s*["\']?(\d+)["\']?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response_text)
            if match:
                return match.group(1), None
        
        return None, "لم يتم العثور على مستوى الدعم"
        
    except requests.exceptions.Timeout:
        return None, "انتهت مهلة الاتصال"
    except requests.exceptions.ConnectionError:
        return None, "خطأ في الاتصال بالخادم"
    except Exception as e:
        return None, f"حدث خطأ: {str(e)}"

def extract_ids(username):
    cookies2 = {
        '_ttp': '2vgirjOnuSrSOnprbKT4f6H0h4U',
        'tt_chain_token': 'aI+tyWRBH/hxDwK2jQqVFg==',
    }
    headers2 = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    url = f"https://www.tiktok.com/@{username}"
    try:
        response = requests.get(url, cookies=cookies2, headers=headers2, timeout=10)
        if response.status_code == 200:
            html = response.text
            
            user_id_patterns = [
                r'"userId":"(\d+)"',
                r'"user_id":"(\d+)"',
                r'user_id["\']?\s*:\s*["\']?(\d+)["\']?',
                r'"id":"(\d+)"'
            ]
            
            user_id = None
            for pattern in user_id_patterns:
                match = re.search(pattern, html)
                if match:
                    user_id = match.group(1)
                    break
            
            sec_uid_patterns = [
                r'"secUid":"([^"]+)"',
                r'"sec_uid":"([^"]+)"',
                r'secUid["\']?\s*:\s*["\']?([^"\']+)["\']?'
            ]
            
            sec_uid = None
            for pattern in sec_uid_patterns:
                match = re.search(pattern, html)
                if match:
                    sec_uid = match.group(1)
                    break
            
            return user_id, sec_uid
    except:
        pass
    
    return None, None

def fetch_followings(user_id, sec_user_id, chat_id=None, message_id=None, username_display=""):
    if not user_id or not sec_user_id:
        return []
    
    c = '0123456789abcdef'
    session = ''.join(random.choices(c, k=32))
    cookies = {
        'sessionid': session,
        'sessionid_ss': session,
        'sid_tt': session,
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
        'Referer': f'https://www.tiktok.com/@{username_display}'
    }

    cursor = "0"
    followings = []
    max_pages = 10

    for page in range(max_pages):
        url = f"https://api19-normal-c-alisg.tiktokv.com/lite/v2/relation/following/list/?user_id={user_id}&count=50&page_token={cursor}&sec_user_id={sec_user_id}"
        try:
            response = requests.get(url, headers=headers, cookies=cookies, timeout=20)
            if response.status_code != 200:
                break
            
            data = response.json()
            follow_list = data.get("followings", [])
            
            if not follow_list:
                break

            for user in follow_list:
                username = user.get("unique_id")
                if username:
                    follower_count = user.get("follower_count", 0)
                    followings.append((username, follower_count))

            if chat_id and message_id:
                try:
                    bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=f"- 🕜 ¦ - سحب {len(followings)} متابع من [ @{username_display} ]...."
                    )
                except:
                    pass

            has_more = data.get("rec_has_more", False)
            cursor = data.get("next_page_token", "")
            
            if not has_more or not cursor:
                break
                
        except:
            break

    return followings

def run_privater(sessionid, user_id):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    cookies = {
        'sessionid': sessionid,
        'sessionid_ss': sessionid,
        'sid_tt': sessionid,
    }

    try:
        r = requests.get("https://www.tiktok.com/passport/web/account/info/", headers=headers, cookies=cookies, timeout=10)
        r.raise_for_status()
        data = r.json().get("data", {})
        sec_user_id = data.get("sec_user_id")
        user_id_api = data.get("user_id")
        if not sec_user_id or not user_id_api:
            bot.send_message(user_id, "- ❌ ¦ - لم يتم العثور على user_id أو sec_user_id.")
            return
    except Exception as e:
        bot.send_message(user_id, f"خطأ في الحصول على بيانات الحساب: {e}")
        return

    converted_total = 0
    cursor = 0
    status_message = bot.send_message(user_id, f"- ✅ ¦-  تم تحويل 0 فيديو إلى خاص")

    try:
        while True:
            url = f'https://api16-normal-c-alisg.tiktokv.com/lite/v2/public/item/list/?source=0&sec_user_id={sec_user_id}&user_id={user_id_api}&count=100&filter_private=1&cursor={cursor}'
            
            r = requests.get(url, headers=headers, cookies=cookies, timeout=15)
            r.raise_for_status()
            json_data = r.json()
            aweme_list = json_data.get("aweme_list", [])
            has_more = json_data.get("has_more", False)
            cursor = json_data.get("cursor", 0)

            if not aweme_list:
                break

            aweme_ids = [item.get("aweme_id") for item in aweme_list if item.get("aweme_id")]

            for aweme_id in aweme_ids:
                mod_url = f'https://api19-normal-c-alisg.tiktokv.com/aweme/v1/aweme/modify/visibility/?aweme_id={aweme_id}&type=2'
                mod_res = requests.get(mod_url, headers=headers, cookies=cookies, timeout=10)

                if mod_res.status_code == 200:
                    converted_total += 1
                    if converted_total % 5 == 0:
                        new_text = f"- ✅ ¦- تم تحويل {converted_total} فيديو إلى خاص"
                        try:
                            bot.edit_message_text(
                                chat_id=user_id,
                                message_id=status_message.message_id,
                                text=new_text
                            )
                        except:
                            pass

            if not has_more:
                break

    except Exception as e:
        bot.send_message(user_id, f"- ❌ ¦ - خطأ أثناء المعالجة: {e}")
    
    final_text = f"- ✅ ¦- تم تحويل {converted_total} فيديو إلى خاص"
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=status_message.message_id,
            text=final_text
        )
    except:
        bot.send_message(user_id, final_text)

def fetch_aweme_ids(sessionid):
    cookies = {
        'sessionid': sessionid,
        'sessionid_ss': sessionid,
        'sid_tt': sessionid,
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    try:
        resp = requests.get('https://api16-normal-c-alisg.tiktokv.com/lite/v2/public/item/list/?max_cursor=0&count=100', headers=headers, cookies=cookies, timeout=10)
        if resp.status_code == 200:
            html = resp.text
            aweme_ids = sorted(set(re.findall(r'"aweme_id"\s*:\s*"(\d+)"', html)))
            return aweme_ids
    except Exception as e:
        print(f"خطأ في جلب صفحة المستخدم: {e}")
    
    return set()

def delete_aweme(sessionid, aweme_id):
    cookies = {
        'sessionid': sessionid,
        'sessionid_ss': sessionid,
        'sid_tt': sessionid,
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Content-Type': 'application/json',
    }

    url = f'https://www.tiktok.com/api/aweme/delete/?aweme_id={aweme_id}'
    try:
        resp = requests.post(url, headers=headers, cookies=cookies, timeout=20)
        return resp.status_code == 200
    except Exception as e:
        print(f"- ❌ ¦- خطأ في حذف الفيديو {aweme_id}: {e}")
        return False

def delete_videos_loop(chat_id, sessionid):
    deleted_count = 0
    try:
        while True:
            aweme_ids = fetch_aweme_ids(sessionid)
            if not aweme_ids:
                bot.send_message(chat_id, "- ✅ ¦- تم الانتهاء من حذف جميع الفيديوهات")
                break

            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(delete_aweme, sessionid, aweme_id) for aweme_id in aweme_ids]
                for future in as_completed(futures):
                    if future.result():
                        deleted_count += 1
                        if deleted_count % 5 == 0:
                            try:
                                bot.edit_message_text(
                                    chat_id=chat_id,
                                    message_id=user_progress_messages[chat_id],
                                    text=f"- ✅¦- عدد الفيديوهات المحذوفة: [ {deleted_count} ]"
                                )
                            except:
                                pass
    except Exception as e:
        bot.send_message(chat_id, f"- ❌ ¦- خطأ: {e}")

class TikTokUnfollowBot:
    def __init__(self, session_id):
        self.unfollowed = 0
        self.failed = 0
        self.total = 0
        self.stop_threads = False
        self.queue = queue.Queue()
        self.session_id = session_id
        
    def sig(self, prm, pl=None, aid=1340):
        if not MEDOSIGNER_AVAILABLE:
            return {}
            
        t = int(time.time())
        ps = urllib.parse.urlencode(prm)
        
        if pl:
            pls = urllib.parse.urlencode(pl)
            xst = md5(pls.encode('utf-8')).hexdigest().upper()
        else:
            pls = ""
            xst = None
        
        gd = Gorgon(ps, t, pls, None).get_value()
        ln = Ladon.encrypt(t, 1611921764, aid)
        
        ag = Argus.get_sign(
            ps, 
            xst, 
            t, 
            platform=19, 
            aid=aid,
            license_id=1611921764, 
            sec_device_id="",
            sdk_version="2.3.15.i18n", 
            sdk_version_int=2
        )
        
        sigs = {
            "x-ladon": ln,
            "x-khronos": str(t),
            "x-argus": ag,
            "x-gorgon": gd.get("x-gorgon", ""),
            "x-ss-req-ticket": str(int(time.time() * 1000))
        }
        
        if xst:
            sigs["x-ss-stub"] = xst
        
        return sigs
    
    def get_user(self, name):
        url = f"https://www.tiktok.com/@{name}"
        hd = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        try:
            r = requests.get(url, headers=hd, timeout=15)
            if r.status_code != 200:
                return None
            
            ht = r.text
            
            pat1 = r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.*?)</script>'
            pat2 = r'{"props":{"pageProps":.*?}}'
            
            data = None
            for pat in [pat1, pat2]:
                m = re.search(pat, ht, re.DOTALL)
                if m:
                    try:
                        data = json.loads(m.group(1) if pat == pat1 else m.group(0))
                        break
                    except:
                        continue
            
            if not data:
                return None
            
            def find(d):
                if isinstance(d, dict):
                    if 'user' in d and 'id' in d['user']:
                        return d['user']
                    for v in d.values():
                        res = find(v)
                        if res:
                            return res
                elif isinstance(d, list):
                    for i in d:
                        res = find(i)
                        if res:
                            return res
                return None
            
            u = find(data)
            if u:
                return {
                    'uid': str(u.get('id', '')),
                    'sec': u.get('secUid', ''),
                    'name': u.get('nickname', ''),
                }
            
            return None
            
        except:
            return None
    
    def get_page(self, uid, sec, tok=""):
        url = "https://api16-normal-c-alisg.tiktokv.com/lite/v2/relation/following/list/"
        
        prm = {
            'user_id': uid,
            'count': "100",
            'page_token': tok,
            'source_type': "4",
            'request_tag_from': "h5",
            'sec_user_id': sec,
            'manifest_version_code': "400603",
            '_rticket': str(int(time.time() * 1000)),
            'app_language': "ar",
            'app_type': "normal",
            'iid': "7583278212717954823",
            'app_package': "com.zhiliaoapp.musically.go",
            'channel': "googleplay",
            'device_type': "RMX3834",
            'language': "ar",
            'host_abi': "arm64-v8a",
            'locale': "ar",
            'resolution': "720*1454",
            'openudid': "b57299cf6a5bb211",
            'update_version_code': "400603",
            'ac2': "wifi",
            'cdid': "f7e5f9fe-bce4-48d5-8857-7caa1b0d34b8",
            'sys_region': "EG",
            'os_api': "34",
            'timezone_name': "Asia/Baghdad",
            'dpi': "272",
            'carrier_region': "IQ",
            'ac': "wifi",
            'device_id': "7456376313159714309",
            'os': "android",
            'os_version': "14",
            'timezone_offset': "10800",
            'version_code': "400603",
            'app_name': "musically_go",
            'ab_version': "40.6.3",
            'version_name': "40.6.3",
            'device_brand': "realme",
            'op_region': "IQ",
            'ssmix': "a",
            'device_platform': "android",
            'build_number': "40.6.3",
            'region': "EG",
            'aid': "1340",
            'ts': str(int(time.time()))
        }
        
        s = self.sig(prm)
        
        hd = {
            'User-Agent': "com.zhiliaoapp.musically.go/400603 (Linux; U; Android 14; ar; RMX3834; Build/UP1A.231005.007;tt-ok/3.12.13.44.lite-ul)",
            'Cookie': f"sessionid={self.session_id};"
        }
        
        if s:
            hd.update({
                'x-ladon': s.get("x-ladon", ""),
                'x-khronos': s.get("x-khronos", ""),
                'x-argus': s.get("x-argus", ""),
                'x-gorgon': s.get("x-gorgon", ""),
                'x-ss-req-ticket': s.get("x-ss-req-ticket", "")
            })
            if 'x-ss-stub' in s:
                hd['x-ss-stub'] = s['x-ss-stub']
        
        try:
            r = requests.get(url, params=prm, headers=hd, timeout=10)
            if r.status_code == 200:
                return r.json()
            else:
                return None
        except:
            return None
    
    def get_all(self, uid, sec):
        all_users = []
        page = 0
        more = True
        token = ""
        max_pages = 50
        
        while more and page < max_pages:
            page += 1
            
            d = self.get_page(uid, sec, token)
            
            if not d:
                break
            
            if d.get('status_code') != 0:
                break
            
            users = d.get('followings', [])
            all_users.extend(users)
            
            more = d.get('has_more', False)
            token = d.get('next_page_token', "")
            
            if more:
                time.sleep(0.3)
        
        return all_users
    
    def unfollow(self, target_id):
        url = "https://api16-normal-c-alisg.tiktokv.com/lite/v2/relation/follow/"
        
        prm = {
            'request_tag_from': "h5",
            'manifest_version_code': "400603",
            '_rticket': str(int(time.time() * 1000)),
            'app_language': "ar",
            'app_type': "normal",
            'iid': "7583278212717954823",
            'app_package': "com.zhiliaoapp.musically.go",
            'channel': "googleplay",
            'device_type': "RMX3834",
            'language': "ar",
            'host_abi': "arm64-v8a",
            'locale': "ar",
            'resolution': "720*1454",
            'openudid': "b57299cf6a5bb211",
            'update_version_code': "400603",
            'ac2': "wifi",
            'cdid': "f7e5f9fe-bce4-48d5-8857-7caa1b0d34b8",
            'sys_region': "EG",
            'os_api': "34",
            'timezone_name': "Asia/Baghdad",
            'dpi': "272",
            'carrier_region': "IQ",
            'ac': "wifi",
            'device_id': "7456376313159714309",
            'os': "android",
            'os_version': "14",
            'timezone_offset': "10800",
            'version_code': "400603",
            'app_name': "musically_go",
            'ab_version': "40.6.3",
            'version_name': "40.6.3",
            'device_brand': "realme",
            'op_region': "IQ",
            'ssmix': "a",
            'device_platform': "android",
            'build_number': "40.6.3",
            'region': "EG",
            'aid': "1340",
            'ts': str(int(time.time()))
        }
        
        pl = {
            'user_id': str(target_id),
            'from_page': "following_list",
            'from': "34",
            'type': "0"
        }
        
        s = self.sig(prm, pl)
        
        hd = {
            'User-Agent': "com.zhiliaoapp.musically.go/400603 (Linux; U; Android 14; ar; RMX3834; Build/UP1A.231005.007;tt-ok/3.12.13.44.lite-ul)",
            'Cookie': f"sessionid={self.session_id};",
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        

        if s:
            hd.update({
                'x-ladon': s.get("x-ladon", ""),
                'x-khronos': s.get("x-khronos", ""),
                'x-argus': s.get("x-argus", ""),
                'x-gorgon': s.get("x-gorgon", ""),
                'x-ss-req-ticket': s.get("x-ss-req-ticket", "")
            })
            if 'x-ss-stub' in s:
                hd['x-ss-stub'] = s['x-ss-stub']
        
        try:
            r = requests.post(url, params=prm, data=pl, headers=hd, timeout=10)
            if r.status_code == 200:
                res = r.json()
                return res.get('status_code') == 0
            else:
                return False
        except:
            return False
    
    def worker(self):
        while not self.stop_threads:
            try:
                u = self.queue.get(timeout=1)
                uid = u.get('uid', '')
                uname = u.get('unique_id', 'N/A')
                
                if uid:
                    ok = self.unfollow(uid)
                    if ok:
                        self.unfollowed += 1
                    else:
                        self.failed += 1
                
                self.queue.task_done()
                
            except queue.Empty:
                break
            except:
                self.queue.task_done()
                continue
    
    def unfollow_all(self, users):
        if not users:
            return False, "- ❌ ¦- لا يوجد مستخدمين"
        
        self.total = len(users)
        self.unfollowed = 0
        self.failed = 0
        
        for u in users:
            self.queue.put(u)
        
        threads_count = 5
        threads = []
        for i in range(threads_count):
            t = threading.Thread(target=self.worker)
            t.daemon = True
            t.start()
            threads.append(t)
        
        self.queue.join()
        
        self.stop_threads = True
        for t in threads:
            t.join(timeout=2)
        
        return True, f"- ✅ ¦- تم الغاء متابعة  [ {self.unfollowed} ]حساب"

def process_unfollow(chat_id, session_id, username):
    try:
        bot.send_message(chat_id, f"- 🕜 ¦- جاري البحث عن الحساب @{username}...")
        
        tiktok_bot = TikTokUnfollowBot(session_id)
        user_info = tiktok_bot.get_user(username)
        
        if not user_info:
            bot.send_message(chat_id, "- ❌ ¦- لم استطع العثور على الحساب")
            return
        
        bot.send_message(chat_id, 
            f"- ✅ ¦- تم العثور على الحساب\n"
            f"- ✅ ¦- الاسم =  {user_info['name']}\n"
            f"- ✅ ¦- الايدي : {user_info['uid']}\n\n"
            f"جاري استخراج المتابعين..."
        )
        
        users_list = tiktok_bot.get_all(user_info['uid'], user_info['sec'])
        
        if not users_list:
            bot.send_message(chat_id, "- ❌ ¦- لا يوجد متابعين في هذا الحساب")
            return
        
        bot.send_message(chat_id, f"- ✅ ¦- تم استخراج {len(users_list)} متابع\nجاري الغاء المتابعة... )")
        
        progress_msg = bot.send_message(chat_id, f"0/{len(users_list)}")
        
        def update_progress():
            while tiktok_bot.unfollowed + tiktok_bot.failed < tiktok_bot.total:
                try:
                    current = tiktok_bot.unfollowed + tiktok_bot.failed
                    bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=progress_msg.message_id,
                        text=f"{current}/{len(users_list)}"
                    )
                except:
                    pass
                time.sleep(2)
        
        progress_thread = threading.Thread(target=update_progress)
        progress_thread.daemon = True
        progress_thread.start()
        
        success, result = tiktok_bot.unfollow_all(users_list)
        
        if success:
            ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            karbo_content = f"تم إلغاء متابعة {tiktok_bot.unfollowed} حساب من @{username}\nالوقت: {ts}"
            
            bot.send_message(chat_id, f"- ✅ ¦-تمت العملية بنجاح\n\n{result}")
            
            filename = f"karbo_{username}_{ts}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(karbo_content)
            
            with open(filename, "rb") as f:
                bot.send_document(chat_id, f)
            
            try:
                os.remove(filename)
            except:
                pass
            
        else:
            bot.send_message(chat_id, f"- ❌ ¦-فشلت العملية: {result}")
        
    except Exception as e:
        bot.send_message(chat_id, f"- ❌ ¦-حدث خطأ: {str(e)}")

def get_stats():
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    
    today_stats = users_db["daily_stats"].get(today, {"users": 0, "messages": 0, "starts": 0})
    yesterday_stats = users_db["daily_stats"].get(yesterday, {"users": 0, "messages": 0, "starts": 0})
    
    new_today = today_stats["users"]
    new_yesterday = yesterday_stats["users"]
    
    current_month = datetime.datetime.now().strftime('%Y-%m')
    new_this_month = sum(stats["users"] for date, stats in users_db["daily_stats"].items() 
                        if date.startswith(current_month))
    
    last_month = (datetime.datetime.now().replace(day=1) - datetime.timedelta(days=1)).strftime('%Y-%m')
    new_last_month = sum(stats["users"] for date, stats in users_db["daily_stats"].items() 
                        if date.startswith(last_month))
    
    stats_message = f"""
احصائيات البوت:

المستخدمون:
- العدد الإجمالي للمستخدمين: {users_db['total_users']}
- عدد المستخدمين في الخاص: {users_db['private_users']}
- عدد القنوات والمجموعات: {users_db['channels_groups']}
- عدد المحظورين: {users_db['banned_users']}

التفاعل:
- اليوم ({today}):
  - المستخدمون: {today_stats['users']}
  - المستخدمون النشطون: {today_stats['users']}
  - بداية الاشتراك: {today_stats['starts']}
  - الرسائل: {today_stats['messages']}

- في الأمس ({yesterday}):
  - المستخدمون: {yesterday_stats['users']}
  - المستخدمون النشطون: {yesterday_stats['users']}
  - بداية الاشتراك: {yesterday_stats['starts']}
  - الرسائل: {yesterday_stats['messages']}

- عدد المستخدمين الجدد اليوم: {new_today}
- عدد المستخدمين الجدد بالأمس: {new_yesterday}
- عدد المستخدمين الجدد هذا الشهر: {new_this_month}
- عدد المستخدمين الجدد في الشهر الماضي: {new_last_month}
"""
    return stats_message

def broadcast_message(text, exclude_users=None):
    if exclude_users is None:
        exclude_users = []
    
    sent_count = 0
    failed_count = 0
    
    for user_id in users_db["user_data"].keys():
        if user_id in exclude_users or user_id == BOT_OWNER:
            continue
        
        try:
            bot.send_message(user_id, text)
            sent_count += 1
            time.sleep(0.2)
        except:
            failed_count += 1
    
    return sent_count, failed_count

def parse_duration(duration_str):
    duration_str = duration_str.lower().strip()
    
    if duration_str.endswith('h'):
        hours = int(duration_str[:-1])
        return hours * 3600, f"{hours} ساعة"
    elif duration_str.endswith('m'):
        minutes = int(duration_str[:-1])
        return minutes * 60, f"{minutes} دقيقة"
    elif duration_str.endswith('d'):
        days = int(duration_str[:-1])
        return days * 86400, f"{days} يوم"
    else:
        try:
            hours = int(duration_str)
            return hours * 3600, f"{hours} ساعة"
        except:
            return 3600, "ساعة واحدة"

def send_subscription_notification(user_id, duration_text, expiry_date):
    try:
        message = f"""
- ✅ ¦- تم تفعيل الاشتراك لك

- 🕜 ¦- مدة اشتراكك: {duration_text}
- 🕜 ¦- اشتراكك صالح لغاية: {expiry_date}

"""
        bot.send_message(user_id, message)
    except:
        pass


def change_nickname(session, nickname):
    url = "https://api16-normal-c-alisg.tiktokv.com/aweme/v1/commit/user/"

    params = {
        "manifest_version_code": "210501",
        "_rticket": str(int(time.time() * 1000)),
        "app_language": "ar",
        "app_type": "normal",
        "iid": "7572486558667163400",
        "channel": "googleplay",
        "device_type": "RMX3263",
        "language": "ar",
        "cpu_support64": "true",
        "host_abi": "arm64-v8a",
        "locale": "ar",
        "resolution": "720*1504",
        "openudid": "1756a74dd357324d",
        "update_version_code": "210501",
        "ac2": "wifi",
        "cdid": "ac3a500a-b48f-43ac-90ae-45e2cae97a66",
        "sys_region": "EG",
        "os_api": "30",
        "uoo": "0",
        "timezone_name": "Africa/Cairo",
        "dpi": "320",
        "carrier_region": "EG",
        "ac": "wifi",
        "device_id": "7564809370804012600",
        "os_version": "11",
        "timezone_offset": "7200",
        "version_code": "210501",
        "carrier_region_v2": "602",
        "app_name": "musically_go",
        "ab_version": "21.5.1",
        "version_name": "21.5.1",
        "device_brand": "realme",
        "op_region": "EG",
        "ssmix": "a",
        "pass-region": "1",
        "pass-route": "1",
        "device_platform": "android",
        "build_number": "21.5.1",
        "region": "EG",
        "aid": "1340",
        "ts": str(int(time.time())),
    }

    payload = {
        "page_from": "0",
        "nickname": nickname,
        "confirmed": "0"
    }

    headers = {
        "User-Agent": "com.zhiliaoapp.musically.go/210501 (Linux; U; Android 11; ar_EG; RMX3263; Build/RKQ1.200826.002; Cronet/58.0.2991.0)",
        "Accept-Encoding": "gzip",
        "sdk-version": "2",
        "passport-sdk-version": "19",
        "Connection": "Keep-Alive",
        "Cookie": f"sessionid={session}; store-country-code=eg; store-idc=alisg"
    }

    params["ts"] = str(int(time.time()))
    params["_rticket"] = str(int(time.time() * 1000))

    if MEDOSIGNER_AVAILABLE:
        sig = signs(
            urlencode(params),
            urlencode(payload),
            sec_device_id=params.get("device_id", ""),
            cookie=f"sessionid={session}",
            aid=1340
        )
        headers.update(sig)

    client = requests.session()
    client.cookies.update({"sessionid": session})

    try:
        r = client.post(url, data=payload, headers=headers, params=params, timeout=15)

        if r.status_code == 200 and ("success" in r.text or r.json().get("status_code") == 0):
            return True, nickname
        else:
            return False, r.text
    except Exception as e:
        return False, str(e)

def signs(params, payload: str = None, sec_device_id: str = "", cookie: str or None = None,
          aid: int = 1340, license_id: int = 1611921764,
          sdk_version_str: str = "2.3.1.i18n", sdk_version: int = 2,
          platform: int = 19, unix: int = None):
    if not MEDOSIGNER_AVAILABLE:
        return {}
        
    x_ss_stub = md5(payload.encode('utf-8')).hexdigest() if payload else None
    if not unix:
        unix = int(time.time())
    return Gorgon(params, unix, payload, cookie).get_value() | {
        "x-ladon": Ladon.encrypt(unix, license_id, aid),
        "x-argus": Argus.get_sign(
            params, x_ss_stub, unix,
            platform=platform, aid=aid,
            license_id=license_id,
            sec_device_id=sec_device_id,
            sdk_version=sdk_version_str,
            sdk_version_int=sdk_version
        )
    }


def block_user(ses, user_id, unique_id, counter, lock):
    url = "https://api16-normal-c-alisg.tiktokv.com/lite/v2/relation/block/"
    params = {
        'lite_flow_schedule': 'new',
        'user_id': user_id,
        'sec_user_id': unique_id,
        'block_type': '1',
        'source': '0',
        'manifest_version_code': '370804',
        '_rticket': '1764335458916',
        'app_language': 'ar',
        'app_type': 'normal',
        'iid': '7545453944668276487',
        'app_package': 'com.zhiliaoapp.musically.go',
        'channel': 'googleplay',
        'device_type': 'RMX3710',
        'language': 'ar',
        'host_abi': 'arm64-v8a',
        'locale': 'ar',
        'resolution': '1080*2158',
        'openudid': 'bd414b5aa37aa495',
        'update_version_code': '370804',
        'ac2': 'wifi',
        'cdid': 'a098bd2b-27e1-4435-bf83-934e23d091cb',
        'sys_region': 'IQ',
        'os_api': '35',
        'timezone_name': 'Asia%2FBaghdad',
        'dpi': '480',
        'ac': 'wifi',
        'device_id': '7545452907198875143',
        'os_version': '15',
        'timezone_offset': '10800',
        'version_code': '370804',
        'version_name': '37.8.4',
        'app_name': 'musically_go',
        'ab_version': '37.8.4',
        'device_brand': 'realme',
        'op_region': 'IQ',
        'ssmix': 'a',
        'device_platform': 'android',
        'build_number': '37.8.4',
        'region': 'IQ',
        'aid': '1340',
        'ts': '1764331525'
    }
    
    if SIGNERPY_AVAILABLE:
        params.update(SignerPy.get(params=params))
    
    headers = {
        'User-Agent': "com.zhiliaoapp.musically.go/370804",
        'Cookie': f"sessionid={ses};"
    }
    
    if SIGNERPY_AVAILABLE:
        headers.update(SignerPy.sign(params=params))
    
    try:
        r = requests.post(url, params=params, data={"body": "null"}, headers=headers, timeout=10)
        if r.status_code == 200:
            with lock:
                counter[0] += 1
            return True
    except:
        pass
    return False

def start_blocking(chat_id, ses):
    reo = 'https://api16-normal-c-alisg.tiktokv.com/passport/web/account/info/'
    hes = {'Cookie': f'sessionid={ses}'}
    try:
        rel = requests.get(url=reo, headers=hes, timeout=10).json()
    except:
        bot.send_message(chat_id, "❌ ¦- فشل الاتصال بالسيشن")
        return

    if 'data' not in rel or 'user_id' not in rel['data']:
        bot.send_message(chat_id, "❌ ¦- فشل جلب بيانات الحساب")
        return

    iid = rel['data']['user_id']
    bot.send_message(chat_id, "🕜 ¦- جاري حظر المتابعين...")

    total_blocked = [0]
    lock = threading.Lock()
    found_any = False

    while True:
        u = "https://api16-normal-c-alisg.tiktokv.com/lite/v2/relation/follower/list/"
        p = {
            'sss-network-channel': '6577337044136',
            'offset': '0',
            'user_id': iid,
            'count': '200',
            'source_type': '1',
            'max_time': '0',
            'request_tag_from': 'h5',
            'manifest_version_code': '370804',
            '_rticket': '1764335682916',
            'app_language': 'ar',
            'app_type': 'normal',
            'iid': '7545453944668276487',
            'app_package': 'com.zhiliaoapp.musically.go',
            'channel': 'googleplay',
            'device_type': 'RMX3710',
            'language': 'ar',
            'host_abi': 'arm64-v8a',
            'locale': 'ar',
            'resolution': '1080*2158',
            'openudid': 'bd414b5aa37aa495',
            'update_version_code': '370804',
            'ac2': 'wifi',
            'cdid': 'a098bd2b-27e1-4435-bf83-934e23d091cb',
            'sys_region': 'IQ',
            'os_api': '35',
            'timezone_name': 'Asia%2FBaghdad',
            'dpi': '480',
            'ac': 'wifi',
            'device_id': '7545452907198875143',
            'os_version': '15',
            'timezone_offset': '10800',
            'version_code': '370804',
            'version_name': '37.8.4',
            'app_name': 'musically_go',
            'ab_version': '37.8.4',
            'device_brand': 'realme',
            'op_region': 'IQ',
            'ssmix': 'a',
            'device_platform': 'android',
            'build_number': '37.8.4',
            'region': 'IQ',
            'aid': '1340',
            'ts': '1764331525'
        }
        
        if SIGNERPY_AVAILABLE:
            p.update(SignerPy.get(params=p))
        
        h = {
            'User-Agent': "com.zhiliaoapp.musically.go/370804",
            'Cookie': f"sessionid={ses};"
        }
        
        if SIGNERPY_AVAILABLE:
            h.update(SignerPy.sign(params=p))
        
        try:
            r = requests.get(url=u, params=p, headers=h, timeout=10).json()
        except:
            break

        if 'followers' not in r or not r['followers']:
            break

        found_any = True
        threads = []
        for f in r['followers']:
            t = threading.Thread(target=block_user, args=(ses, f['uid'], f['unique_id'], total_blocked, lock))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

    if not found_any:
        bot.send_message(chat_id, "❌ ¦- لا يوجد متابعين")
    else:
        bot.send_message(chat_id, f"✅ ¦- تم حظر {total_blocked[0]} متابع")


def delete_music_collections(session):
    params = {
        'sss-network-channel': '3131509517753',
        'cursor': '0',
        'count': '21',
        'request_tag_from': 'h5',
        'manifest_version_code': '370804',
        '_rticket': '1763222926141',
        'app_language': 'ar',
        'app_type': 'normal',
        'iid': '7545453944668276487',
        'app_package': 'com.zhiliaoapp.musically.go',
        'channel': 'googleplay',
        'device_type': 'RMX3710',
        'language': 'ar',
        'host_abi': 'arm64-v8a',
        'locale': 'ar',
        'resolution': '1080*2158',
        'openudid': 'bd414b5aa37aa495',
        'update_version_code': '370804',
        'ac2': 'wifi',
        'cdid': 'a098bd2b-27e1-4435-bf83-934e23d091cb',
        'sys_region': 'IQ',
        'os_api': '35',
        'timezone_name': 'Asia%2FBaghdad',
        'dpi': '480',
        'ac': 'wifi',
        'device_id': '7545452907198875143',
        'os_version': '15',
        'timezone_offset': '10800',
        'version_code': '370804',
        'app_name': 'musically_go',
        'ab_version': '37.8.4',
        'version_name': '37.8.4',
        'device_brand': 'realme',
        'op_region': 'IQ',
        'ssmix': 'a',
        'device_platform': 'android',
        'build_number': '37.8.4',
        'region': 'IQ',
        'aid': '1340',
        'ts': '1763222439'
    }

    if SIGNERPY_AVAILABLE:
        params.update(SignerPy.get(params=params))
    
    url = "https://api16-normal-c-alisg.tiktokv.com/lite/v2/user/music/collect/v1/"
    headers = {
        "User-Agent": g(),
        "Cookie": f"sessionid={session};"
    }
    
    if SIGNERPY_AVAILABLE:
        headers.update(SignerPy.sign(params=params))

    try:
        r = requests.get(url, params=params, headers=headers, timeout=15).json()
        if "mc_list" not in r or not r["mc_list"]:
            return 0

        deleted = 0
        for u2 in r["mc_list"]:
            mid = u2.get("mid")
            if not mid:
                continue

            pa = {
                '_rticket': '1763222590201',
                'ab_version': '37.8.4',
                'ac': 'wifi',
                'ac2': 'wifi',
                'action': '0',
                'aid': '1340',
                'app_language': 'ar',
                'app_name': 'musically_go',
                'app_package': 'com.zhiliaoapp.musically.go',
                'app_type': 'normal',
                'build_number': '37.8.4',
                'cdid': 'a098bd2b-27e1-4435-bf83-934e23d091cb',
                'channel': 'googleplay',
                'device_brand': 'realme',
                'device_id': '7545452907198875143',
                'device_platform': 'android',
                'device_type': 'RMX3710',
                'dpi': '480',
                'host_abi': 'arm64-v8a',
                'iid': '7545453944668276487',
                'language': 'ar',
                'locale': 'ar',
                'manifest_version_code': '370804',
                'music_id': mid,
                'op_region': 'IQ',
                'openudid': 'bd414b5aa37aa495',
                'os_api': '35',
                'os_version': '15',
                'region': 'IQ',
                'request_tag_from': 'h5',
                'resolution': '1080*2158',
                'ssmix': 'a',
                'sss-network-channel': '4530267793467',
                'sys_region': 'IQ',
                'timezone_name': 'Asia%2FBaghdad',
                'timezone_offset': '10800',
                'ts': '1763222439',
                'update_version_code': '370804',
                'version_code': '370804',
                'version_name': '37.8.4'
            }

            if SIGNERPY_AVAILABLE:
                pa.update(SignerPy.get(params=pa))
            
            he = {
                "User-Agent": g(),
                "Cookie": f"sessionid={session};"
            }
            
            if SIGNERPY_AVAILABLE:
                he.update(SignerPy.sign(params=pa))
            
            del_url = "https://api16-normal-c-alisg.tiktokv.com/aweme/v1/music/collect/"
            requests.get(del_url, params=pa, headers=he, timeout=10)
            deleted += 1

        return deleted
    except:
        return -1


def get_level_advanced(username):
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Android 10; Pixel 3 Build/QKQ1.200308.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/125.0.6394.70 Mobile Safari/537.36 trill_350402 JsSdk/1.0 NetType/MOBILE Channel/googleplay AppName/trill app_version/35.3.1 ByteLocale/en ByteFullLocale/en Region/IN AppId/1180 Spark/1.5.9.1 AppVersion/35.3.1 BytedanceWebview/d8a21c6"
    }
    try:
        tikinfo = requests.get(f'https://www.tiktok.com/@{username}', headers=headers, timeout=10).text
        info = tikinfo.split('webapp.user-detail"')[1].split('"RecommenUserList"')[0]
        return info.split('id":"')[1].split('",')[0]
    except:
        return None

def get_user_level(username):
    uid = get_level_advanced(username)
    if not uid:
        return "خطأ في الحصول على ID"
    
    url = (
        "https://webcast16-normal-no1a.tiktokv.eu/webcast/user/"
        f"?request_from=profile_card_v2&request_from_scene=1&target_uid={uid}"
        f"&iid={random.randint(1,10**19)}&device_id={random.randint(1,10**19)}"
        "&ac=wifi&channel=googleplay&aid=1233&app_name=musical_ly"
        "&version_code=300102&version_name=30.1.2&device_platform=android"
        "&os=android&ab_version=30.1.2&ssmix=a&device_type=RMX3511"
        "&device_brand=realme&language=ar&os_api=33&os_version=13"
        f"&openudid={binascii.hexlify(os.urandom(8)).decode()}"
        "&manifest_version_code=2023001020&resolution=1080*2236&dpi=360"
        "&update_version_code=2023001020"
        f"&_rticket={round(random.uniform(1.2,1.6)*100000000)*-1}4632"
        "&current_region=IQ&app_type=normal&sys_region=IQ&mcc_mnc=41805"
        "&timezone_name=Asia%2FBaghdad&carrier_region_v2=418&residence=IQ"
        "&app_language=ar&carrier_region=IQ&ac2=wifi&uoo=0&op_region=IQ"
        "&timezone_offset=10800&build_number=30.1.2&host_abi=arm64-v8a"
        "&locale=ar&region=IQ&content_language=gu%2C"
        f"&ts={round(random.uniform(1.2,1.6)*100000000)*-1}"
        f"&cdid={uuid.uuid4()}"
        "&webcast_sdk_version=2920&webcast_language=ar&webcast_locale=ar_IQ"
    )

    headers = {
        "User-Agent": "com.zhiliaoapp.musically/2023001020 (Linux; Android 13; ar; RMX3511)"
    }
    
    if MEDOSIGNER_AVAILABLE:
        headers.update(signs(
            url.split("?")[1],
            "",
            "AadCFwpTyztA5j9L" + ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(9))
        ))

    try:
        r = requests.get(url, headers=headers, timeout=10)
        m = re.search(r'"default_pattern":"(.*?)"', r.text)
        return m.group(1) if m else "لم يتم العثور على المستوى"
    except:
        return "خطأ في الاتصال"

def get_wallet_info(session):
    url = "https://webcast16-normal-c-alisg.tiktokv.com/webcast/wallet_api_tiktok/mywallet/?request_tag_from=h5&storage_type=0&manifest_version_code=2021705420&_rticket=1761140567508&current_region=IQ&app_language=ar&app_type=normal&iid=7562052812789876536&channel=trassion_int&device_type=RMX3710&language=ar&cpu_support64=true&host_abi=armeabi-v7a&locale=ar&resolution=1080*2158&openudid=bd414b5aa37aa495&content_language=ar%2C&update_version_code=2021705420&ac2=wifi&cdid=4be0926b-0384-4f35-ad45-660f444443c2&sys_region=IQ&os_api=35&uoo=0&timezone_name=Asia%2FBaghdad&dpi=480&residence=IQ&ac=wifi&device_id=7545452907198875143&pass-route=1&os_version=15&timezone_offset=10800&version_code=170542&app_name=musical_ly&ab_version=17.5.42&version_name=17.5.42&device_brand=realme&op_region=IQ&ssmix=a&pass-region=1&device_platform=android&build_number=17.5.42&region=IQ&aid=1233&ts=1761140566"

    headers = {
        "User-Agent": "com.zhiliaoapp.musically/2021705420 (Linux; U; Android 15; ar_IQ; RMX3710; Build/AP3A.240617.008; Cronet/TTNetVersion:a3aa9ea4 2020-08-10 QuicVersion:7aee791b 2020-06-05)",
        "Cookie": f"sessionid={session};"
    }

    try:
        re = requests.get(url, headers=headers, timeout=10).json()
        w = re["data"]["my_wallet"]
        return {
            "total_income": w['total_income'],
            "diamond_count": w['diamond_count']
        }
    except:
        return None

def delete_all_reposts(chat_id, session_id, user_id):
    try:
        deleted_count = 0
        bot.send_message(chat_id, "🕜¦- جاري حذف الريبوستات..")
        
        while True:
            reposts = get_reposts_batch(session_id, user_id)
            
            if not reposts or len(reposts) == 0:
                break
            
            for item in reposts:
                try:
                    success = delete_single_repost(session_id, item['aweme_id'])
                    if success:
                        deleted_count += 1
                        
                        if deleted_count % 75 == 0:
                            bot.send_message(chat_id, 
                                f"- 🕜 ¦- جارِ الحذف\n"
                                f"✅ ¦ - تم حذف =   [ {deleted_count} ] ريبوست"
                            )
                    
                    time.sleep(0.3)
                    
                except Exception as e:
                    continue
            
            if len(reposts) < 75:
                break
        
        bot.send_message(chat_id, f"- ✅ ¦ - تم حذف =  [  {deleted_count} ] ريبوست\n")
            
    except Exception as e:
        bot.send_message(chat_id, f"- ❌ ¦- حدث خطا اثناء الحذف:\n{str(e)}")

def get_reposts_batch(session_id, user_id):
    try:
        params = {
            'user_id': user_id,
            'offset': '0',
            'count': '20',
            'scene': '0',
            'manifest_version_code': '370804',
            '_rticket': '1764060071228',
            'app_language': 'ar',
            'app_type': 'normal',
            'iid': '7545453944668276487',
            'app_package': 'com.zhiliaoapp.musically.go',
            'channel': 'googleplay',
            'device_type': 'RMX3710',
            'language': 'ar',
            'host_abi': 'arm64-v8a',
            'locale': 'ar',
            'resolution': '1080*2158',
            'openudid': 'bd414b5aa37aa495',
            'update_version_code': '370804',
            'ac2': 'wifi',
            'cdid': 'a098bd2b-27e1-4435-bf83-934e23d091cb',
            'sys_region': 'IQ',
            'os_api': '35',
            'timezone_name': 'Asia%2FBaghdad',
            'dpi': '480',
            'ac': 'wifi',
            'device_id': '7545452907198875143',
            'os_version': '15',
            'timezone_offset': '10800',
            'version_code': '370804',
            'app_name': 'musically_go',
            'ab_version': '37.8.4',
            'version_name': '37.8.4',
            'device_brand': 'realme',
            'op_region': 'IQ',
            'ssmix': 'a',
            'device_platform': 'android',
            'build_number': '37.8.4',
            'region': 'IQ',
            'aid': '1340',
            'ts': '1764060062'
        }
        
        if SIGNERPY_AVAILABLE:
            params.update(SignerPy.get(params=params))
        
        headers = {
            'User-Agent': "com.zhiliaoapp.musically.go/370804 (Linux; U; Android 15; ar_IQ; RMX3710; Build/AP3A.240617.008;tt-ok/3.12.13.27-ul)",
            'Cookie': f"sessionid={session_id};"
        }
        
        if SIGNERPY_AVAILABLE:
            headers.update(SignerPy.sign(params=params))
        
        url = "https://api16-normal-c-alisg.tiktokv.com/tiktok/v1/upvote/item/list"
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'aweme_list' in data:
                return data['aweme_list']
    except:
        pass
    
    return []

def delete_single_repost(session_id, item_id):
    try:
        params = {
            'manifest_version_code': '370804',
            '_rticket': str(round(random.uniform(1.2, 1.6) * 100000000) * -1) + "1228",
            'app_language': 'ar',
            'app_type': 'normal',
            'iid': '7545453944668276487',
            'app_package': 'com.zhiliaoapp.musically.go',
            'channel': 'googleplay',
            'device_type': 'RMX3710',
            'language': 'ar',
            'host_abi': 'arm64-v8a',
            'locale': 'ar',
            'resolution': '1080*2158',
            'openudid': str(binascii.hexlify(os.urandom(8)).decode()),
            'update_version_code': '370804',
            'ac2': 'wifi',
            'cdid': str(uuid.uuid4()),
            'sys_region': 'IQ',
            'os_api': '35',
            'timezone_name': 'Asia%2FBaghdad',
            'dpi': '480',
            'ac': 'wifi',
            'device_id': str(random.randint(1, 10**19)),
            'os_version': '15',
            'timezone_offset': '10800',
            'version_code': '370804',
            'app_name': 'musically_go',
            'ab_version': '37.8.4',
            'version_name': '37.8.4',
            'device_brand': 'realme',
            'op_region': 'IQ',
            'ssmix': 'a',
            'device_platform': 'android',
            'build_number': '37.8.4',
            'region': 'IQ',
            'aid': '1340',
            'ts': str(round(random.uniform(1.2, 1.6) * 100000000) * -1)
        }
        
        if SIGNERPY_AVAILABLE:
            params.update(SignerPy.get(params=params))
        
        data = {'item_id': item_id}
        
        headers = {
            'User-Agent': "com.zhiliaoapp.musically.go/370804 (Linux; U; Android 15; ar_IQ; RMX3710; Build/AP3A.240617.008;tt-ok/3.12.13.27-ul)",
            'Cookie': f"sessionid={session_id};"
        }
        
        if SIGNERPY_AVAILABLE:
            headers.update(SignerPy.sign(params=params))
        
        url = "https://api16-normal-c-alisg.tiktokv.com/tiktok/v1/upvote/delete"
        response = requests.post(url, params=params, data=data, headers=headers, timeout=10)
        
        return response.status_code == 200
    except:
        return False

def extract_account_info(session_id):
    cookies = {
        'sessionid': session_id,
        'sessionid_ss': session_id,
        'sid_tt': session_id,
    }

    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    url = "https://www.tiktok.com/passport/web/account/info/"

    try:
        response = requests.get(url, headers=headers, cookies=cookies, timeout=10)
        if response.status_code == 200:
            data = response.json().get("data", {})
            return {
                "user_id": data.get("user_id_str", ""),
                "screen_name": data.get("screen_name", ""),
                "username": data.get("username", ""),
                "email": data.get("email", ""),
                "mobile": data.get("mobile", ""),
                "description": data.get("description") or "nothing",
                "create_time": datetime.datetime.fromtimestamp(data.get("create_time", 0)).strftime('%Y-%m-%d %H:%M:%S'),
            }
        else:
            return None
    except:
        return None

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    current_time = datetime.datetime.now()
    
    if user_id in users_db["active_subscriptions"]:
        subscription = users_db["active_subscriptions"][user_id]
        expiry_date = datetime.datetime.strptime(subscription["expires"], '%Y-%m-%d %H:%M:%S')
        if current_time > expiry_date:
            del users_db["active_subscriptions"][user_id]
    
    if user_id != BOT_OWNER and user_id not in users_db["user_data"]:
        notify_new_user(user_id)
    
    user_states[message.chat.id] = "started"
    
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    if today in users_db["daily_stats"]:
        users_db["daily_stats"][today]["messages"] += 1
        users_db["daily_stats"][today]["starts"] += 1
    
    markup = InlineKeyboardMarkup(row_width=2)
    
    markup.add(
        InlineKeyboardButton("إخفاء الفيديوهات", callback_data="make_private"),
        InlineKeyboardButton("حذف الفيديوهات", callback_data="delete_videos"),
        InlineKeyboardButton("إلغاء المتابعة", callback_data="unfollow_users"),
        InlineKeyboardButton("حذف الريبوستات", callback_data="delete_reposts"),
        InlineKeyboardButton("فحص السيشن", callback_data="check_session"),
        InlineKeyboardButton("فحص المحفظة", callback_data="check_wallet"),
    )
    markup.add(
        InlineKeyboardButton("سحب لستة", callback_data="get_followings"),
        InlineKeyboardButton("معلومات حساب", callback_data="account_info"),
        InlineKeyboardButton("تغيير الاسم", callback_data="change_name"),
    )
    markup.add(
        InlineKeyboardButton("حظر المتابعين", callback_data="block_followers"),
        InlineKeyboardButton("حذف الموسيقى", callback_data="delete_music"),
    )
    markup.add(
        InlineKeyboardButton("سحب سيشن", url="https://vt.tiktok.com/ZSkUaFXQf/")
    )
    markup.add(
        InlineKeyboardButton("المطور", url="https://t.me/Dev_Raven"),
        InlineKeyboardButton("قناة المطور", url="https://t.me/Dev_Raven")
    )
    
    if message.from_user.id == BOT_OWNER:
        markup.add(
            InlineKeyboardButton("اذاعة في البوت", callback_data="broadcast"),
            InlineKeyboardButton("احصائيات البوت", callback_data="stats")
        )
        markup.add(
            InlineKeyboardButton("حظر مستخدم", callback_data="ban_user"),
            InlineKeyboardButton("إلغاء حظر", callback_data="unban_user")
        )
        markup.add(
            InlineKeyboardButton("تفعيل لمستخدم", callback_data="activate_user")
        )
    
    welcome_message = f"""
- Welcome = {message.from_user.first_name}
- The bot specializes in TikTok services
- The bot is paid 	
"""
    
    bot.send_message(
        message.chat.id,
        welcome_message,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    if today in users_db["daily_stats"]:
        users_db["daily_stats"][today]["messages"] += 1
    
    if call.data == "make_private":
        user_states[user_id] = "waiting_session_for_private"
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="- Send the session : "
        )
    
    elif call.data == "delete_videos":
        user_states[user_id] = "waiting_session_for_delete"
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="- Send the session : "
        )
    
    elif call.data == "check_session":
        user_states[user_id] = "waiting_session_for_check"
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="أرسل sessionid للفحص:"
        )
    
    elif call.data == "check_level":
        user_states[user_id] = "waiting_username_for_level"
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="أرسل اسم المستخدم (بدون @) لفحص مستوى الدعم:"
        )
    
    elif call.data == "check_wallet":
        user_states[user_id] = "waiting_session_for_wallet"
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="- Send the session : "
        )
    
    elif call.data == "get_followings":
        user_states[user_id] = "waiting_username_for_followings"
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="أرسل اسم المستخدم (بدون @) لسحب قائمة المتابعين:"
        )
    
    elif call.data == "account_info":
        user_states[user_id] = "waiting_session_for_account"
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="- Send the session : "
        )
    
    elif call.data == "change_name":
        user_states[user_id] = "waiting_session_for_name"
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="- Send the session : "
        )
    
    elif call.data == "block_followers":
        user_states[user_id] = "waiting_session_for_block"
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="- Send the session : "
        )
    
    elif call.data == "delete_music":
        user_states[user_id] = "waiting_session_for_music"
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="- Send the session : "
        )
    
    elif call.data == "delete_reposts":
        user_states[user_id] = "waiting_session_for_reposts"
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="- Send the session : "
        )
    
    elif call.data == "unfollow_users":
        user_states[user_id] = "waiting_unfollow_info"
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="أرسل sessionid واليوزر (مثال: sessionid username):"
        )
    
    elif call.data == "broadcast" and user_id == BOT_OWNER:
        user_states[user_id] = "waiting_broadcast_message"
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="أرسل نص الرسالة التي تريد بثها:"
        )
    
    elif call.data == "stats" and user_id == BOT_OWNER:
        stats = get_stats()
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=stats
        )
    
    elif call.data == "ban_user" and user_id == BOT_OWNER:
        user_states[user_id] = "waiting_user_id_for_ban"
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="أرسل ID المستخدم الذي تريد حظره:"
        )
    
    elif call.data == "unban_user" and user_id == BOT_OWNER:
        user_states[user_id] = "waiting_user_id_for_unban"
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="أرسل ID المستخدم الذي تريد إلغاء حظره:"
        )
    
    elif call.data == "activate_user" and user_id == BOT_OWNER:
        user_states[user_id] = "waiting_user_id_for_activate"
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="أرسل الايدي ثم المدة (مثال: 123456789 3h):"
        )
    
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text.strip()
    
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    if today in users_db["daily_stats"]:
        users_db["daily_stats"][today]["messages"] += 1
    else:
        users_db["daily_stats"][today] = {"users": 0, "messages": 1, "starts": 0}
    
    if user_id in user_states:
        state = user_states[user_id]
        
        if state == "waiting_session_for_private":
            bot.send_message(chat_id, "جاري إخفاء الفيديوهات...")
            Thread(target=run_privater, args=(text, chat_id)).start()
            user_states.pop(user_id, None)
        
        elif state == "waiting_session_for_delete":
            user_sessions[chat_id] = text
            sent_msg = bot.send_message(chat_id, "- ✅ ¦- عدد الفيديوهات المحذوفة: 0")
            user_progress_messages[chat_id] = sent_msg.message_id
            Thread(target=delete_videos_loop, args=(chat_id, text)).start()
            user_states.pop(user_id, None)
        
        elif state == "waiting_session_for_check":
            try:
                info = generalinfo(text)
                bal = balance(text)
                
                if info.get("message") != "success" or not bal:
                    bot.send_message(chat_id, "- ❌ ¦- السيشن غير صالح أو منتهي")
                    return
                
                karb2 = info.get("data", {})
                Karb1 = {}
                try:
                    Karb1 = bal.json().get("data", {})
                except:
                    pass
                
                created = karb2.get("create_time", 0)
                
                msg = f"""
Username: {karb2.get('username', '')}
User ID: {karb2.get('user_id', '')}
Sec User ID: {karb2.get('sec_user_id', '')}
Screen Name: {karb2.get('screen_name', '')}
Bio: {karb2.get('description', '')}
Mobile: {karb2.get('mobile', '')}
Email: {karb2.get('email', '')}
Created At: {conv(created) if created else "N/A"}
Coins: {Karb1.get("coins", "")}
Frozen Coins: {Karb1.get("frozen_coins", "")}
Allow Status: {Karb1.get("is_allow", "")}
Email Confirmed: {Karb1.get("is_email_confirmed", "")}
Quick Payment: {Karb1.get("quick_payment_available", "")}
Dev : @Dev_Raven
"""
                bot.send_message(chat_id, msg)
            except Exception as e:
                bot.send_message(chat_id, f"خطأ: {e}")
            finally:
                user_states.pop(user_id, None)
        
        elif state == "waiting_username_for_level":
            if not text:
                bot.send_message(chat_id, "يجب إرسال اسم مستخدم")
                user_states.pop(user_id, None)
                return
            
            bot.send_message(chat_id, f"جاري فحص @{text}...")
            level, error = get_tiktok_level(text)
            
            if error:
                bot.send_message(chat_id, f"خطأ: {error}")
            else:
                bot.send_message(chat_id, f"""
Username: @{text}
Level: {level}
Dev: @Dev_Raven
""")
            user_states.pop(user_id, None)
        
        elif state == "waiting_session_for_wallet":
            bot.send_message(chat_id, "جاري فحص المحفظة...")
            wallet_info = get_wallet_info(text)
            
            if wallet_info:
                msg = f"""
💰 ¦ - معلومات المحفظة:

💎 ¦ - إجمالي الأرباح: {wallet_info['total_income']}
💎 ¦ - عدد المال داخل الحساب :: {wallet_info['diamond_count']}
"""
                bot.send_message(chat_id, msg)
            else:
                bot.send_message(chat_id, "❌ ¦ - فشل في الحصول على معلومات المحفظة")
            user_states.pop(user_id, None)
        
        elif state == "waiting_username_for_followings":
            if not text:
                bot.send_message(chat_id, "يجب إرسال اسم مستخدم")
                user_states.pop(user_id, None)
                return
            
            bot.send_message(chat_id, f"- 🕜 ¦-جاري سحب متابعات @{text}...")
            user_id_tik, sec_uid = extract_ids(text)
            
            if not user_id_tik or not sec_uid:
                bot.send_message(chat_id, "- ❌ ¦-لم يتم العثور على المستخدم")
                user_states.pop(user_id, None)
                return
            
            followings = fetch_followings(user_id_tik, sec_uid, username_display=text)
            
            if followings:
                with open("followings.txt", "w", encoding="utf-8") as f:
                    for username, count in followings:
                        f.write(f"{username}\n")
                
                with open("followings.txt", "rb") as f:
                    bot.send_document(
                        chat_id,
                        f,
                        caption=f"- ✅ ¦- تم سحب {len(followings)} متابع من @{text}"
                    )
                
                try:
                    os.remove("followings.txt")
                except:
                    pass
            else:
                bot.send_message(chat_id, "- ❌ ¦-لم يتم العثور على متابعين")
            
            user_states.pop(user_id, None)
        
        elif state == "waiting_session_for_account":
            info = extract_account_info(text)
            if info:
                msg = f"""
ID: {info['user_id']}
Name: {info['screen_name']}
Username: {info['username']}
Email: {info['email']}
Phone: {info['mobile']}
Bio: {info['description']}
Created: {info['create_time']}
"""
                bot.send_message(chat_id, msg)
            else:
                bot.send_message(chat_id, "- ❌ ¦- السيشن غير صالح")
            user_states.pop(user_id, None)
        
        elif state == "waiting_session_for_name":
            user_sessions[user_id] = text
            user_states[user_id] = "waiting_nickname_for_name"
            bot.send_message(chat_id, "🎭 ¦ - أرسل الاسم الجديد:")
        
        elif state == "waiting_nickname_for_name":
            session = user_sessions.get(user_id)
            if session:
                bot.send_message(chat_id, "🎭 ¦ - جاري تغيير الاسم...")
                success, result = change_nickname(session, text)
                if success:
                    bot.send_message(chat_id, f"✅ ¦ - تم تغيير الاسم إلى: {result}")
                else:
                    bot.send_message(chat_id, f"❌ ¦ - فشل في تغيير الاسم: {result}")
            else:
                bot.send_message(chat_id, "❌ ¦ - لم يتم العثور على السيشن")
            
            user_states.pop(user_id, None)
            user_sessions.pop(user_id, None)
        
        elif state == "waiting_session_for_block":
            bot.send_message(chat_id, "🕜 ¦ - جاري حظر المتابعين...")
            Thread(target=start_blocking, args=(chat_id, text)).start()
            user_states.pop(user_id, None)
        
        elif state == "waiting_session_for_music":
            bot.send_message(chat_id, "🎵 ¦ - جاري حذف الموسيقى المحفوظة...")
            deleted = delete_music_collections(text)
            if deleted == -1:
                bot.send_message(chat_id, "❌ ¦ - فشل في حذف الموسيقى")
            elif deleted == 0:
                bot.send_message(chat_id, "ℹ️ ¦ - لا توجد موسيقى محفوظة")
            else:
                bot.send_message(chat_id, f"✅ ¦ - تم حذف {deleted} موسيقى محفوظة")
            user_states.pop(user_id, None)
        
        elif state == "waiting_session_for_reposts":
            bot.send_message(chat_id, "📋 ¦ - جاري التحقق من السيشن...")
            check_url = 'https://api16-normal-c-alisg.tiktokv.com/passport/web/account/info/'
            headers = {'Cookie': f'sessionid={text}'}
            
            try:
                response = requests.get(check_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    user_id_api = data.get('data', {}).get('user_id')
                    if user_id_api:
                        Thread(target=delete_all_reposts, args=(chat_id, text, user_id_api)).start()
                    else:
                        bot.send_message(chat_id, "- ❌ ¦- السيشن غير صالح")
                else:
                    bot.send_message(chat_id, "- ❌ ¦- فشل في الاتصال")
            except:
                bot.send_message(chat_id, "- ❌ ¦- خطأ في التحقق من السيشن")
            finally:
                user_states.pop(user_id, None)
        
        elif state == "waiting_unfollow_info":
            try:
                parts = text.split()
                if len(parts) != 2:
                    bot.send_message(chat_id, "- ❌ ¦-  استخدم: sessionid username")
                    return
                
                session_id = parts[0]
                username = parts[1]
                
                bot.send_message(chat_id, f"- 🕜 ¦-جاري بدء عملية الغاء المتابعة لـ @{username}...")
                Thread(target=process_unfollow, args=(chat_id, session_id, username)).start()
                
            except Exception as e:
                bot.send_message(chat_id, f"- ❌¦- خطأ: {str(e)}")
            finally:
                user_states.pop(user_id, None)
        
        elif state == "waiting_broadcast_message" and user_id == BOT_OWNER:
            bot.send_message(chat_id, "جاري الاذاعة...")
            sent, failed = broadcast_message(text)
            bot.send_message(chat_id, f"""
تم إرسال الاذاعة : 
تم الإرسال: {sent}
فشل الإرسال: {failed}
""")
            user_states.pop(user_id, None)
        
        elif state == "waiting_user_id_for_ban" and user_id == BOT_OWNER:
            try:
                target_id = int(text)
                users_db["banned_users"] += 1
                bot.send_message(chat_id, f"تم حظر المستخدم {target_id}")
            except:
                bot.send_message(chat_id, "ID غير صالح")
            user_states.pop(user_id, None)
        
        elif state == "waiting_user_id_for_unban" and user_id == BOT_OWNER:
            try:
                target_id = int(text)
                if users_db["banned_users"] > 0:
                    users_db["banned_users"] -= 1
                bot.send_message(chat_id, f"تم إلغاء حظر المستخدم {target_id}")
            except:
                bot.send_message(chat_id, "ID غير صالح")
            user_states.pop(user_id, None)
        
        elif state == "waiting_user_id_for_activate" and user_id == BOT_OWNER:
            try:
                parts = text.split()
                if len(parts) != 2:
                    bot.send_message(chat_id, "صيغة غير صحيحة. استخدم: الايدي ثم المدة (مثال: 123456789 3h)")
                    return
                
                target_id = None
                duration_str = None
                
                try:
                    target_id = int(parts[0])
                    duration_str = parts[1]
                except:
                    try:
                        duration_str = parts[0]
                        target_id = int(parts[1])
                    except:
                        bot.send_message(chat_id, "صيغة غير صحيحة. تأكد من كتابة الأرقام بشكل صحيح")
                        return

                duration_seconds, duration_text = parse_duration(duration_str)
                expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=duration_seconds)

                users_db["active_subscriptions"][target_id] = {
                    "duration": duration_text,
                    "expires": expiry_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "activated_by": user_id,
                    "activated_at": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }

                activation_info = f"""
- ✅ ¦- Activated for user  | تم تفعيل للمستخدم = {target_id}
🕓 ¦ - المدة: {duration_text}
- 🕜 ¦- وقت التفعيل: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🕜 ¦- وقت الانتهاء: {expiry_time.strftime('%Y-%m-%d %H:%M:%S')}
"""
                bot.send_message(chat_id, activation_info)
                
                send_subscription_notification(target_id, duration_text, expiry_time.strftime('%Y-%m-%d %H:%M:%S'))
                
            except Exception as e:
                bot.send_message(chat_id, f"خطأ: {str(e)}")
            finally:
                user_states.pop(user_id, None)
    
    else:
        start_command(message)

if __name__ == "__main__":
    print("- ✅ ¦ Go to your bot and send an order /start ")
    
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"- ❌ ¦- Error: {e}")
