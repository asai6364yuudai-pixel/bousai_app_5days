from flask import Flask, jsonify, request, render_template, session, redirect, url_for
from urllib.parse import urlparse, urljoin
from functools import wraps
import hashlib
import hmac
import json
import math
import os
import re
import threading
import urllib.request
from urllib.parse import urlencode
from datetime import datetime, timedelta, timezone

# app.py はプロジェクト直下に置く。
# 実体（templates / static / data）は bousai_app/ 配下にあるので、そこを参照する。
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(BASE_DIR, 'bousai_app')

app = Flask(
    __name__,
    template_folder=os.path.join(APP_DIR, 'templates'),
    static_folder=os.path.join(APP_DIR, 'static'),
)
app.secret_key = 'your-secret-key-here'

SUPPORTED_LANGUAGES = ('ja', 'en')
TRANSLATIONS = {
    'ja': {
        'app_name': '防災アプリ',
        'home': 'ホーム',
        'shelter_search': '避難所検索',
        'shelter_register': '避難所登録',
        'shelter_name': '避難所名',
        'board': '指示・発信',
        'login': 'ログイン',
        'logout': 'ログアウト',
        'logged_in': 'ログイン中',
        'language': '言語選択',
        'japanese': '日本語',
        'english': 'English',
        'contents': '目次',
        'map': '避難所マップ',
        'map_current_location': '現在地へ移動',
        'map_show_all': '全避難所を表示',
        'map_legend': '混雑度',
        'map_available': '受け入れ可・空き',
        'map_somewhat_crowded': 'やや混雑',
        'map_crowded': '混雑',
        'map_unavailable': '受け入れ不可',
        'map_location_failed': '現在地を取得できませんでした。',
        'report_title': '災害の情報を報告する',
        'report_intro': '身近で起きている災害の状況を入力してください。',
        'disaster_type': '災害の種類',
        'select_disaster_type': '災害の種類を選択してください',
        'earthquake': '地震',
        'flood': '洪水・浸水',
        'landslide': '土砂災害',
        'fire': '火災',
        'strong_wind': '強風・突風',
        'other': 'その他',
        'other_detail': '災害の種類の詳細',
        'other_detail_placeholder': '災害の種類を入力してください',
        'location': '位置情報',
        'location_placeholder': '住所や場所を入力してください',
        'get_location': '現在地を取得',
        'situation': '状況の説明',
        'situation_placeholder': '被害の状況や周囲の様子を入力してください',
        'send_report': '報告を送信する',
        'weather_title': '青森市 気象警報・注意報',
        'area_name': '青森市',
        'auto_refresh': '10分おき自動更新',
        'loading': '読み込み中...',
        'notice_title': '指示・発信ボード',
        'notice_source': '防災対策課が確認した情報のみ表示しています',
        'last_update': '最終更新',
        'unknown_time': '日時不明',
        'shelter_destination': '避難先',
        'status': '状態',
        'notice_empty': '現在、住民向けの指示・発信はありません。',
        'search_description': '登録されている避難所を確認できます。',
        'all_shelters': '全施設一覧',
        'search_results': '検索結果',
        'no_shelters': '該当する避難所が見つかりませんでした',
        'back_to_search': '検索画面に戻る',
        'back_to_home': 'トップページへ戻る',
        'register_description': '新しい避難所情報を登録します。',
        'required': '必須',
        'address': '住所',
        'address_placeholder': '例：青森県青森市中央1-1-1',
        'accepting': '受け入れ可否',
        'accepting_yes': '受け入れ可',
        'accepting_no': '受け入れ不可',
        'congestion': '混雑度',
        'empty': '空き',
        'somewhat_crowded': 'やや混雑',
        'crowded': '混雑',
        'please_select': '選択してください',
        'register': '登録',
        'board_title': '発信ボード',
        'board_description': '住民向けの発信を登録・確認できます。',
        'announcement_list': '発信一覧',
        'content': '内容',
        'no_instructions': '登録されている指示はありません。',
        'data_fetch': 'データ取得',
        'jma_announcement': '気象庁発表',
        'weather_fetch_failed': '気象情報の取得に失敗しました',
        'no_warnings': '現在、警報・注意報は発表されていません',
        'geolocation_unavailable': '現在地を取得できません。位置情報を入力してください。',
        'getting_location': '現在地を取得しています...',
        'location_entered': '現在地を入力しました。',
        'report_sent': '報告を受け付けました',
        'report_failed': '送信に失敗しました。時間をおいて再度お試しください。',
        'report_required': '災害の種類、位置情報、状況を入力してください',
        'other_detail_required': '災害の種類の詳細を入力してください',
        'registration_complete': '登録完了しました。',
        'deletion_complete': '避難所を削除しました。',
        'delete_confirm': '選択中の避難所を削除します。もう一度「削除」を押すと確定します。',
        'shelter_not_found': '対象の避難所が見つかりません。',
        'phone_invalid': '電話番号は数字のみ入力してください。',
        'count_invalid': '人数は0以上の整数で入力してください。',
        'capacity_warning': '受け入れ済み人数が受け入れ可能人数を超えています。もう一度「登録・更新」を押すと、この内容で登録・更新できます。',
        'name_required': '避難所名を入力してください',
        'address_required': '住所を入力してください',
        'accepting_required': '受け入れ可否を選択してください',
        'congestion_required': '混雑度を選択してください',
        'geocode_failed': '住所を地図上の位置に変換できませんでした。住所を確認して再度お試しください。',
        'popup_address': '住所',
        'popup_accepting': '受け入れ可否',
        'popup_congestion': '混雑度',
        'menu_open': 'メニューを開く',
        'emergency_rescue': '救助要請',
        'emergency_rescue_message': '命に関わる緊急の救助要請は、こちらにお電話ください',
        'emergency_placeholder': '仮番号',
        'all_display': 'すべて表示',
        'search': '検索',
        'district': '地区',
        'all_districts': 'すべての地区',
        'sort': '並び替え',
        'default_order': '登録順',
        'name_order': '避難所名順',
        'recommendation_order': 'おすすめ度順',
        'crowding_order': '混雑が少ない順',
        'distance_order': '仮現在地から近い順',
        'recommendation_distance': 'おすすめ度（距離）',
        'travel_time': '避難所までの時間',
        'telephone': '電話番号',
        'back_to_search_screen': '検索画面に戻る',
        'back_to_top': 'トップページへ戻る',
        'percentage_unregistered': '割合未登録',
        'announcement_register': '発信登録',
        'instruction_register': '指示登録',
        'announcement_register_page': '発信登録ページへ',
        'instruction_register_page': '指示登録ページへ',
        'announcement_list': '発信一覧',
        'instruction_list': '指示一覧',
        'filter': '絞り込む',
        'clear': '解除',
        'all_areas': '全地域',
        'all_warning_types': '全種類',
        'no_announcements': '登録されている発信はありません。',
        'no_content': '内容なし',
        'unspecified_area': '指定なし',
        'normal_warning': '通常',
        'target_area': '対象区域',
        'announcement_content_optional': '発信内容（任意）',
        'target': '対象',
        'resident': '住民',
        'warning_type': '警報・注意報',
        'register_announcement': '発信を登録',
        'source_department': '指示元部署',
        'target_department': '対象部署',
        'select_option': '選択してください',
        'instruction_content': '指示内容',
        'shelter_optional': '避難先（任意）',
        'no_registered_shelters': '登録されている避難所はありません。',
        'shelter_list': '避難所一覧',
        'clear_selection': '選択解除',
        'delete': '削除',
        'save_update': '登録・更新',
        'accepted_count': '受け入れ済み人数',
        'capacity': '受け入れ可能人数',
        'telephone_label': '電話番号',
        'unregistered': '未登録',
        'issued': '発令',
        'released': '解除',
        'register_instruction': '指示を登録',
        'pending': '未対応',
        'in_progress': '対応中',
        'completed': '完了',
        'admin_login': '管理者ログイン',
        'admin_notice': '指示ボード・避難所登録の利用には管理者権限が必要です。',
        'password': 'パスワード',
        'password_hint': '「123」と入力してください',
        'map_display_failed': '地図を表示できません',
        'login_failed': 'パスワードが正しくありません。',
        'announcement_area_required': '対象区域を1つ以上選択してください。',
        'announcement_registered': '発信を登録しました。',
        'disaster_department': '防災課',
        'road_department': '道路管理課',
    },
    'en': {
        'app_name': 'Disaster Prevention App',
        'home': 'Home',
        'shelter_search': 'Shelter Search',
        'shelter_register': 'Register Shelter',
        'shelter_name': 'Shelter name',
        'board': 'Announcements',
        'login': 'Log in',
        'logout': 'Log out',
        'logged_in': 'Logged in',
        'language': 'Language',
        'japanese': '日本語',
        'english': 'English',
        'contents': 'Contents',
        'map': 'Shelter Map',
        'map_current_location': 'Go to my location',
        'map_show_all': 'Show all shelters',
        'map_legend': 'Crowding',
        'map_available': 'Available',
        'map_somewhat_crowded': 'Somewhat crowded',
        'map_crowded': 'Crowded',
        'map_unavailable': 'Not accepting',
        'map_location_failed': 'Could not get your location.',
        'report_title': 'Report a Disaster',
        'report_intro': 'Enter information about a disaster in your area.',
        'disaster_type': 'Disaster type',
        'select_disaster_type': 'Select a disaster type',
        'earthquake': 'Earthquake',
        'flood': 'Flooding',
        'landslide': 'Landslide',
        'fire': 'Fire',
        'strong_wind': 'Strong wind',
        'other': 'Other',
        'other_detail': 'Disaster type details',
        'other_detail_placeholder': 'Enter the disaster type',
        'location': 'Location',
        'location_placeholder': 'Enter an address or place',
        'get_location': 'Get current location',
        'situation': 'Situation description',
        'situation_placeholder': 'Describe the damage and surroundings',
        'send_report': 'Send report',
        'weather_title': 'Aomori City Weather Warnings',
        'area_name': 'Aomori City',
        'auto_refresh': 'Refreshes every 10 minutes',
        'loading': 'Loading...',
        'notice_title': 'Announcements',
        'notice_source': 'Only information confirmed by the disaster management office is shown.',
        'last_update': 'Last updated',
        'unknown_time': 'Unknown date',
        'shelter_destination': 'Shelter',
        'status': 'Status',
        'notice_empty': 'There are no announcements for residents.',
        'search_description': 'View registered shelters.',
        'all_shelters': 'All shelters',
        'search_results': 'Search results',
        'no_shelters': 'No matching shelters were found.',
        'back_to_search': 'Back to shelter search',
        'back_to_home': 'Back to home',
        'register_description': 'Register new shelter information.',
        'required': 'required',
        'address': 'Address',
        'address_placeholder': 'Example: 1-1-1 Chuo, Aomori City, Aomori',
        'accepting': 'Accepting evacuees',
        'accepting_yes': 'Accepting',
        'accepting_no': 'Not accepting',
        'congestion': 'Crowding',
        'empty': 'Available',
        'somewhat_crowded': 'Somewhat crowded',
        'crowded': 'Crowded',
        'please_select': 'Please select',
        'register': 'Register',
        'board_title': 'Announcements',
        'board_description': 'Register and review announcements for residents.',
        'announcement_list': 'Announcement list',
        'content': 'Content',
        'no_instructions': 'There are no registered announcements.',
        'data_fetch': 'Data retrieved',
        'jma_announcement': 'JMA announcement',
        'weather_fetch_failed': 'Failed to retrieve weather information.',
        'no_warnings': 'There are currently no active warnings or advisories.',
        'geolocation_unavailable': 'Could not get your location. Please enter it manually.',
        'getting_location': 'Getting your location...',
        'location_entered': 'Current location entered.',
        'report_sent': 'Your report has been received.',
        'report_failed': 'Failed to send. Please try again later.',
        'report_required': 'Please enter the disaster type, location, and situation.',
        'other_detail_required': 'Please enter details for the disaster type.',
        'registration_complete': 'Registration completed.',
        'deletion_complete': 'The shelter was deleted.',
        'delete_confirm': 'This shelter will be deleted. Press "Delete" again to confirm.',
        'shelter_not_found': 'The selected shelter was not found.',
        'phone_invalid': 'Phone number must contain digits only.',
        'count_invalid': 'Counts must be non-negative integers.',
        'capacity_warning': 'Accepted people exceed capacity. Press "Register / Update" again to save these values.',
        'name_required': 'Please enter a shelter name.',
        'address_required': 'Please enter an address.',
        'accepting_required': 'Please select whether the shelter is accepting evacuees.',
        'congestion_required': 'Please select the crowding level.',
        'geocode_failed': 'Could not convert the address to a map location. Check the address and try again.',
        'popup_address': 'Address',
        'popup_accepting': 'Accepting evacuees',
        'popup_congestion': 'Crowding',
        'menu_open': 'Open menu',
        'emergency_rescue': 'Rescue request',
        'emergency_rescue_message': 'For a life-threatening emergency rescue request, please call this number.',
        'emergency_placeholder': 'Placeholder number',
        'all_display': 'Show all',
        'search': 'Search',
        'district': 'District',
        'all_districts': 'All districts',
        'sort': 'Sort by',
        'default_order': 'Registration order',
        'name_order': 'Shelter name',
        'recommendation_order': 'Recommendation',
        'crowding_order': 'Least crowded',
        'distance_order': 'Nearest to the reference location',
        'recommendation_distance': 'Recommendation (distance)',
        'travel_time': 'Travel time to shelter',
        'telephone': 'Phone number',
        'back_to_search_screen': 'Back to search',
        'back_to_top': 'Back to home',
        'percentage_unregistered': 'Rate unavailable',
        'announcement_register': 'Register announcement',
        'instruction_register': 'Register instruction',
        'announcement_register_page': 'Announcement registration',
        'instruction_register_page': 'Instruction registration',
        'announcement_list': 'Announcement list',
        'instruction_list': 'Instruction list',
        'filter': 'Filter',
        'clear': 'Clear',
        'all_areas': 'All areas',
        'all_warning_types': 'All types',
        'no_announcements': 'There are no registered announcements.',
        'no_content': 'No content',
        'unspecified_area': 'Not specified',
        'normal_warning': 'Normal',
        'target_area': 'Target area',
        'announcement_content_optional': 'Announcement content (optional)',
        'target': 'Target',
        'resident': 'Residents',
        'warning_type': 'Warning/advisory type',
        'register_announcement': 'Register announcement',
        'source_department': 'Source department',
        'target_department': 'Target department',
        'select_option': 'Please select',
        'instruction_content': 'Instruction content',
        'shelter_optional': 'Shelter (optional)',
        'no_registered_shelters': 'There are no registered shelters.',
        'shelter_list': 'Shelter list',
        'clear_selection': 'Clear selection',
        'delete': 'Delete',
        'save_update': 'Register / Update',
        'accepted_count': 'Currently accepted',
        'capacity': 'Shelter capacity',
        'telephone_label': 'Phone number',
        'unregistered': 'Not registered',
        'issued': 'Issued',
        'released': 'Released',
        'register_instruction': 'Register instruction',
        'pending': 'Pending',
        'in_progress': 'In progress',
        'completed': 'Completed',
        'admin_login': 'Administrator login',
        'admin_notice': 'Administrator access is required for the instruction board and shelter registration.',
        'password': 'Password',
        'password_hint': 'Enter "123"',
        'map_display_failed': 'The map could not be displayed',
        'login_failed': 'The password is incorrect.',
        'announcement_area_required': 'Please select at least one target area.',
        'announcement_registered': 'The announcement was registered.',
        'disaster_department': 'Disaster Management Office',
        'road_department': 'Road Management Office',
    }
}

# 管理者認証情報
ADMIN_CREDENTIALS = {
    'admin': '123'
}

# ────────────────────────────────
# 気象警報・注意報設定
PREFECTURE_CODE = "020000"  # 青森県
AREA_NAME = "青森市"

# 青森市の市区町村コード
AREA_CODE = "0220100"

# 検索結果の距離順で使う固定の仮現在地
SEARCH_ORIGIN = {'latitude': 40.8244988, 'longitude': 140.7431883}

WARNING_URL = (
    f"https://www.jma.go.jp/bosai/warning/data/r8/{PREFECTURE_CODE}.json"
)

JST = timezone(timedelta(hours=9))

# 警報・注意報のコード一覧
WARNING_CODES = {
    "00": "解除",
    "02": "暴風雪警報",
    "03": "レベル3大雨警報",
    "04": "洪水警報",
    "05": "暴風警報",
    "06": "大雪警報",
    "07": "波浪警報",
    "08": "レベル3高潮警報",
    "09": "レベル3土砂災害警報",
    "10": "レベル2大雨注意報",
    "12": "大雪注意報",
    "13": "風雪注意報",
    "14": "雷注意報",
    "15": "強風注意報",
    "16": "波浪注意報",
    "17": "融雪注意報",
    "18": "洪水注意報",
    "19": "レベル2高潮注意報",
    "20": "濃霧注意報",
    "21": "乾燥注意報",
    "22": "なだれ注意報",
    "23": "低温注意報",
    "24": "霜注意報",
    "25": "着氷注意報",
    "26": "着雪注意報",
    "27": "その他の注意報",
    "29": "レベル2土砂災害注意報",
    "32": "暴風雪特別警報",
    "33": "レベル5大雨特別警報",
    "35": "暴風特別警報",
    "36": "大雪特別警報",
    "37": "波浪特別警報",
    "38": "レベル5高潮特別警報",
    "39": "レベル5土砂災害特別警報",
    "43": "レベル4大雨危険警報",
    "48": "レベル4高潮危険警報",
    "49": "レベル4土砂災害危険警報"
}

AREAS = [
    "青森市全域", "本町", "新町", "古川", "大野", "浅虫", "浪打",
    "甲田", "田屋敷", "三内",
]
WARNING_OPTIONS = [
    "通常", "レベル2大雨注意報", "大雨警報", "レベル3大雨警報",
    "レベル4大雨危険警報", "レベル5大雨特別警報", "洪水注意報", "洪水警報",
    "レベル2高潮注意報", "レベル3高潮警報", "レベル4高潮危険警報",
    "レベル5高潮特別警報", "レベル2土砂災害注意報", "レベル3土砂災害警報",
    "レベル4土砂災害危険警報", "レベル5土砂災害特別警報", "大雪注意報",
    "大雪警報", "大雪特別警報", "風雪注意報", "暴風雪警報", "暴風雪特別警報",
    "強風注意報", "暴風警報", "暴風特別警報", "波浪注意報", "波浪警報",
    "波浪特別警報", "雷注意報", "融雪注意報", "濃霧注意報", "乾燥注意報",
    "なだれ注意報", "低温注意報", "霜注意報", "着氷注意報", "着雪注意報",
    "その他の注意報",
]
DEPARTMENTS = ["防災課", "道路管理課", "住民"]
INSTRUCTION_STATUSES = ["未対応", "対応中", "完了"]
ANNOUNCEMENT_STATUSES = ["発令", "解除"]

# ────────────────────────────────
# サンプルデータの読み込み
DATA_FILE = os.path.join(APP_DIR, 'data', 'shelters.json')
INSTRUCTIONS_FILE = os.path.join(APP_DIR, 'data', 'instructions.json')
DISASTER_REPORTS_FILE = os.path.join(APP_DIR, 'data', 'disaster_reports.json')

def load_json(path, default):
    """JSONファイルを読み込む（存在しない・壊れている場合は default を返す）"""
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

shelters = load_json(DATA_FILE, [])
SHELTER_LOCK = threading.Lock()
instructions = load_json(INSTRUCTIONS_FILE, [])
disaster_reports = load_json(DISASTER_REPORTS_FILE, [])


def get_language():
    """セッションから現在の表示言語を取得する"""
    language = session.get('language', 'ja')
    return language if language in SUPPORTED_LANGUAGES else 'ja'


def translate(key, language=None):
    """現在の言語に対応する表示文言を返す"""
    language = language or get_language()
    return TRANSLATIONS[language].get(key, TRANSLATIONS['ja'].get(key, key))


def translate_warning(value, language=None):
    """警報種別の保存値を表示言語へ変換する"""
    if (language or get_language()) == 'ja':
        return value
    replacements = (
        ('レベル2', 'Level 2 '), ('レベル3', 'Level 3 '),
        ('レベル4', 'Level 4 '), ('レベル5', 'Level 5 '),
        ('大雨', 'Heavy rain'), ('高潮', 'Storm surge'),
        ('土砂災害', 'Landslide'), ('洪水', 'Flood'), ('大雪', 'Heavy snow'),
        ('暴風雪', 'Blizzard'), ('風雪', 'Snowstorm'), ('強風', 'Strong wind'),
        ('暴風', 'Storm'), ('波浪', 'High waves'), ('雷', 'Thunderstorm'),
        ('融雪', 'Snowmelt'), ('濃霧', 'Dense fog'), ('乾燥', 'Dryness'),
        ('なだれ', 'Avalanche'), ('低温', 'Low temperature'), ('霜', 'Frost'),
        ('着氷', 'Icing'), ('着雪', 'Snow accretion'), ('その他の注意報', 'Other advisory'),
        ('特別警報', ' emergency warning'), ('危険警報', ' critical warning'),
        ('警報', ' warning'), ('注意報', ' advisory'), ('通常', 'Normal'),
    )
    translated = str(value)
    for source, target in replacements:
        translated = translated.replace(source, target)
    return translated.strip().capitalize()


def translate_choice(value, language=None):
    """状態・部署などの固定選択値を表示言語へ変換する"""
    labels = {
        '未対応': 'pending', '対応中': 'in_progress', '完了': 'completed',
        '発令': 'issued', '発令中': 'issued', '解除': 'released',
        '防災課': 'disaster_department', '道路管理課': 'road_department',
        '住民': 'resident',
    }
    key = labels.get(value)
    return translate(key, language) if key else value


@app.context_processor
def inject_language_context():
    return {
        'language': get_language(),
        't': translate,
        'translate_warning': translate_warning,
        'translate_choice': translate_choice,
        'translations': TRANSLATIONS[get_language()]
    }

def save_instructions():
    """指示ボードのデータをファイルに保存する"""
    try:
        with open(INSTRUCTIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(instructions, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def next_instruction_id():
    return max(
        (int(item.get('id', 0)) for item in instructions
         if str(item.get('id', '')).isdigit()),
        default=0,
    ) + 1


def item_category(item):
    """旧形式のレコードも発信・指示へ分類する"""
    if item.get('category') in ('announcement', 'instruction'):
        return item['category']
    return 'announcement' if item.get('target') == '住民' else 'instruction'


def display_area(area):
    return str(area or '').replace(',', '、')


def sort_shelters():
    """避難所名の昇順をサーバー側で常に維持する"""
    shelters.sort(key=lambda shelter: str(shelter.get('name', '')).casefold())


def save_shelters():
    """避難所を並び替えてからJSONへ保存する"""
    sort_shelters()
    temporary_file = f'{DATA_FILE}.tmp'
    with open(temporary_file, 'w', encoding='utf-8') as file:
        json.dump(shelters, file, ensure_ascii=False, indent=2)
    os.replace(temporary_file, DATA_FILE)


def shelter_form_values(form):
    """登録画面のフォーム値を正規化する"""
    return {
        'name': form.get('name', '').strip(),
        'accepted_count': form.get('accepted_count', '').strip(),
        'capacity': form.get('capacity', '').strip(),
        'address': form.get('address', '').strip(),
        'phone': form.get('phone', '').strip(),
    }


def shelter_confirmation_token(values, selected_id=''):
    """現在の入力値に結び付いたサーバー検証用トークンを作る"""
    payload = json.dumps(
        {'selected_id': str(selected_id), **values},
        ensure_ascii=False,
        sort_keys=True,
    ).encode('utf-8')
    return hmac.new(app.secret_key.encode('utf-8'), payload, hashlib.sha256).hexdigest()


def valid_shelter_numbers(values):
    """人数が空欄または0以上の整数かを検証する"""
    return all(
        not values[field] or re.fullmatch(r'\d+', values[field])
        for field in ('accepted_count', 'capacity')
    )


def shelter_exceeds_capacity(values):
    """両方が有効な数値のときだけ人数超過を判定する"""
    if not values['accepted_count'] or not values['capacity']:
        return False
    return int(values['accepted_count']) > int(values['capacity'])


sort_shelters()


def geocode_address(address):
    """Nominatimで住所を検索し、緯度・経度を返す"""
    query = urlencode({
        'q': address,
        'format': 'jsonv2',
        'limit': 1,
        'accept-language': 'ja'
    })
    request = urllib.request.Request(
        f'https://nominatim.openstreetmap.org/search?{query}',
        headers={'User-Agent': 'bousai-app/1.0 (shelter-map)'}
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            results = json.loads(response.read().decode('utf-8'))
        if not results:
            return None
        latitude = float(results[0]['lat'])
        longitude = float(results[0]['lon'])
        return {'latitude': latitude, 'longitude': longitude}
    except (ValueError, KeyError, TypeError, json.JSONDecodeError,
            urllib.error.URLError, urllib.error.HTTPError):
        return None
# ────────────────────────────────

# ────────────────────────────────
# 認証関連の設定とヘルパー関数
def is_safe_url(target):
    """リダイレクト先URLが安全かどうかチェック"""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

def login_required(f):
    """認証が必要なページに付けるデコレータ"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            # 現在のURLをnextパラメータとしてログイン画面にリダイレクト
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/set_language', methods=['POST'])
def set_language():
    """ヘッダーの言語選択をセッションに保存する"""
    language = request.form.get('language', '')
    if language in SUPPORTED_LANGUAGES:
        session['language'] = language

    next_url = request.form.get('next') or url_for('index')
    if not is_safe_url(next_url):
        next_url = url_for('index')
    return redirect(next_url)

def get_japan_time():
    """日本時間（JST）の現在時刻を取得する"""
    return datetime.now(JST).strftime("%Y年%m月%d日 %H:%M")


def format_report_time(iso_str):
    """気象庁の発表時刻（ISO形式）をJSTの表示用文字列に変換する"""
    if not iso_str:
        return "不明"
    try:
        parsed = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
        if parsed.tzinfo:
            parsed = parsed.astimezone(JST)
        return parsed.strftime("%Y年%m月%d日 %H:%M")
    except ValueError:
        return iso_str


def filter_and_sort_shelters(items, district='', sort=''):
    """避難所を地区で絞り込み、指定された方法で安定して並べ替える"""
    district = str(district or '').strip()
    sort = sort if sort in ('name', 'recommendation', 'crowding', 'distance') else ''
    results = [
        shelter for shelter in items
        if not district or str(shelter.get('district', '')).strip() == district
    ]

    if sort == 'name':
        results.sort(key=lambda shelter: str(shelter.get('name', '')).casefold())
    elif sort == 'recommendation':
        results.sort(
            key=lambda shelter: str(shelter.get('recommendation', '')).count('★'),
            reverse=True,
        )
    elif sort == 'crowding':
        results.sort(key=lambda shelter: shelter_occupancy_sort_key(shelter))
    elif sort == 'distance':
        results.sort(key=lambda shelter: shelter_distance_sort_key(shelter))
    return results


def shelter_distance(shelter):
    """固定仮現在地からの距離をkmで返す。住所または座標がなければ None。"""
    if not str(shelter.get('address', '')).strip():
        return None
    try:
        latitude = float(shelter.get('latitude'))
        longitude = float(shelter.get('longitude'))
    except (TypeError, ValueError):
        return None
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        return None

    origin_latitude = math.radians(SEARCH_ORIGIN['latitude'])
    latitude_radians = math.radians(latitude)
    delta_latitude = latitude_radians - origin_latitude
    delta_longitude = math.radians(longitude - SEARCH_ORIGIN['longitude'])
    haversine = (
        math.sin(delta_latitude / 2) ** 2
        + math.cos(origin_latitude) * math.cos(latitude_radians)
        * math.sin(delta_longitude / 2) ** 2
    )
    return 6371 * 2 * math.asin(math.sqrt(haversine))


def shelter_distance_sort_key(shelter):
    """距離が計算できない避難所を最後に置く。"""
    distance = shelter_distance(shelter)
    return (distance is None, distance if distance is not None else 0)


def shelter_occupancy_percent(shelter):
    """受け入れ済み人数と容量から混雑率を返す。未登録なら None。"""
    try:
        accepted_count = float(shelter.get('accepted_count', ''))
        capacity = float(shelter.get('capacity', ''))
    except (TypeError, ValueError):
        return None
    if accepted_count < 0 or capacity <= 0:
        return None
    return accepted_count / capacity * 100


def shelter_occupancy_sort_key(shelter):
    """混雑率を優先し、旧形式の星表現にも対応する。"""
    occupancy = shelter_occupancy_percent(shelter)
    if occupancy is not None:
        return (0, occupancy)
    return (1, str(shelter.get('crowding', '')).count('★'))


def prepare_shelters(items):
    """画面表示用に混雑率を付加し、元の保存データは変更しない。"""
    prepared = []
    for shelter in items:
        normalized = dict(shelter)
        occupancy = shelter_occupancy_percent(shelter)
        if occupancy is not None:
            normalized['occupancy_rate'] = occupancy
            normalized['occupancy_display'] = f'{occupancy:g}%'
            normalized['congestion'] = (
                '混雑' if occupancy >= 80 else
                'やや混雑' if occupancy >= 50 else
                '空き'
            )
        prepared.append(normalized)
    return prepared


def filter_shelters(district=None):
    """既存 API 向けの地区絞り込みを維持する"""
    return filter_and_sort_shelters(shelters, district=district)


def parse_area_warnings(warning_data):
    """気象庁の新形式JSONから対象市区町村の発表・継続中の情報を抽出する"""
    if not isinstance(warning_data, list):
        raise ValueError("気象庁の警報・注意報データが新形式の配列ではありません")

    report_datetimes = [
        report.get("reportDatetime", "")
        for report in warning_data
        if isinstance(report, dict) and report.get("reportDatetime")
    ]
    latest_report_datetime = max(report_datetimes, default="")
    warnings = []
    seen_codes = set()

    for report in warning_data:
        if not isinstance(report, dict):
            continue

        report_datetime = report.get("reportDatetime")
        if report_datetime != latest_report_datetime:
            continue

        warning = report.get("warning")
        if not isinstance(warning, dict):
            continue

        class20_items = warning.get("class20Items", [])
        if not isinstance(class20_items, list):
            continue

        area = next(
            (
                item for item in class20_items
                if isinstance(item, dict)
                and item.get("areaCode") == AREA_CODE
            ),
            None
        )
        if not area:
            continue

        kinds = area.get("kinds", [])
        if not isinstance(kinds, list):
            continue

        for kind in kinds:
            if not isinstance(kind, dict):
                continue

            status = kind.get("status", "")
            code = kind.get("code", "")
            if status not in ("発表", "継続") or not code or code in seen_codes:
                continue

            warnings.append({
                "name": WARNING_CODES.get(
                    code,
                    f"不明な警報・注意報 (コード: {code})"
                ),
                "code": code,
                "status": status
            })
            seen_codes.add(code)

    return warnings, latest_report_datetime


def get_weather_warnings():
    """青森市の警報・注意報を取得する"""
    try:
        # 青森県の新形式（令和8年～）警報・注意報データを取得
        with urllib.request.urlopen(url=WARNING_URL, timeout=10) as res:
            warning_data = json.loads(res.read())

        warnings, report_datetime = parse_area_warnings(warning_data)

        return {
            "area_name": AREA_NAME,
            "warnings": warnings,
            "report_time": format_report_time(report_datetime),
            "last_fetch_time": get_japan_time()
        }

    except Exception:
        return {
            "area_name": AREA_NAME,
            "warnings": [],
            "report_time": "取得失敗",
            "last_fetch_time": get_japan_time(),
            "error": True
        }


# トップページ：templates/index.html を返す（住民向け指示も表示する）
@app.route('/')
def index():
    requested_area = request.args.get('area', '').strip()
    area_filter = requested_area if requested_area in AREAS else ''
    resident_notices = sorted(
        (
            i for i in instructions
            if i.get('target') == '住民'
            and (
                not area_filter
                or area_filter in {
                    area.strip() for area in str(i.get('area', '')).split(',')
                }
            )
        ),
        key=lambda instruction: instruction.get('updated_at', ''),
        reverse=True
    )
    return render_template(
        'index.html',
        resident_notices=resident_notices,
        shelters=prepare_shelters(shelters),
        areas=AREAS,
        area_filter=area_filter,
    )


@app.route('/api/disaster_reports', methods=['POST'])
def create_disaster_report():
    """ホーム画面の通報フォームから災害状況を保存する"""
    report = request.get_json(silent=True) or {}
    disaster_type = str(report.get('disaster_type', '')).strip()
    other_detail = str(report.get('other_detail', '')).strip()
    location = str(report.get('location', '')).strip()
    situation = str(report.get('situation', '')).strip()

    if not disaster_type or not location or not situation:
        return jsonify({'error': translate('report_required')}), 400
    if disaster_type == 'その他' and not other_detail:
        return jsonify({'error': translate('other_detail_required')}), 400

    saved_report = {
        'timestamp': get_japan_time(),
        'disaster_type': disaster_type,
        'other_detail': other_detail,
        'location': location,
        'situation': situation
    }
    disaster_reports.append(saved_report)
    with open(DISASTER_REPORTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(disaster_reports, f, ensure_ascii=False, indent=2)

    return jsonify({'message': translate('report_sent')})

# ログインページ
@app.route('/login', methods=['GET', 'POST'])
def login():
    # リダイレクト先を取得（デフォルトは避難所登録画面）
    next_url = request.args.get('next') or request.form.get('next')

    # 安全でないURLの場合はデフォルトページにリダイレクト
    if not next_url or not is_safe_url(next_url):
        next_url = url_for('shelter_register')

    if request.method == 'POST':
        password = request.form.get('password', '').strip()

        # 認証チェック
        username = next(
            (name for name, registered_password in ADMIN_CREDENTIALS.items()
             if registered_password == password),
            None
        )
        if username:
            session['logged_in'] = True
            session['username'] = username
            # ログイン成功後は指定されたページにリダイレクト
            return redirect(next_url)
        return render_template('login.html', error=True, message=translate('login_failed'), next=next_url)

    # ログイン済みの場合は指定されたページにリダイレクト
    if session.get('logged_in'):
        return redirect(next_url)

    return render_template('login.html', next=next_url)

# ログアウト
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# 避難所登録ページ
@app.route('/shelter_register', methods=['GET', 'POST'])
@login_required
def shelter_register():
    values = shelter_form_values(request.form) if request.method == 'POST' else {
        'name': '', 'accepted_count': '', 'capacity': '', 'address': '', 'phone': ''
    }
    selected_id = request.form.get('selected_id', '').strip()
    action = request.form.get('action', 'save')
    confirmation = request.form.get('confirmation', '')

    def page(message='', error=False, confirmation='', selected_id=selected_id):
        return render_template(
            'shelter_register.html',
            shelters=shelters,
            values=values,
            selected_id=selected_id,
            message=message,
            error=error,
            confirmation=confirmation,
        )

    if request.method == 'GET':
        return page()

    if action == 'delete':
        if not selected_id:
            return page()
        token = shelter_confirmation_token(values, selected_id)
        if not hmac.compare_digest(confirmation, token):
            return page(translate('delete_confirm'), error=True, confirmation=token)
        with SHELTER_LOCK:
            original_count = len(shelters)
            shelters[:] = [shelter for shelter in shelters if str(shelter.get('id')) != selected_id]
            if len(shelters) == original_count:
                return page(translate('shelter_not_found'), error=True)
            save_shelters()
        values = {'name': '', 'accepted_count': '', 'capacity': '', 'address': '', 'phone': ''}
        return page(translate('deletion_complete'), selected_id='', confirmation='')

    if not values['name']:
        return page(translate('name_required'), error=True)
    if not values['address']:
        return page(translate('address_required'), error=True)
    if values['phone'] and not re.fullmatch(r'\d+', values['phone']):
        return page(translate('phone_invalid'), error=True)
    if not valid_shelter_numbers(values):
        return page(translate('count_invalid'), error=True)

    expected_token = shelter_confirmation_token(values, selected_id)
    if shelter_exceeds_capacity(values) and not hmac.compare_digest(confirmation, expected_token):
        return page(translate('capacity_warning'), error=True, confirmation=expected_token)

    coordinates = geocode_address(values['address'])
    with SHELTER_LOCK:
        if selected_id:
            shelter = next(
                (item for item in shelters if str(item.get('id')) == selected_id),
                None,
            )
            if shelter is None:
                return page(translate('shelter_not_found'), error=True)
        else:
            next_id = max(
                (int(shelter.get('id', 0)) for shelter in shelters
                 if str(shelter.get('id', '')).isdigit()),
                default=0,
            ) + 1
            shelter = {'id': next_id}
            shelters.append(shelter)

        shelter.update(values)
        if coordinates:
            shelter.update(coordinates)
        else:
            shelter.pop('latitude', None)
            shelter.pop('longitude', None)
        save_shelters()

    values = {'name': '', 'accepted_count': '', 'capacity': '', 'address': '', 'phone': ''}
    return page(translate('registration_complete'), selected_id='', confirmation='')

# 避難所検索ページ
@app.route('/shelter_search')
def shelter_search():
    districts = sorted({
        str(shelter.get('district', '')).strip()
        for shelter in shelters
        if str(shelter.get('district', '')).strip()
    })
    return render_template('shelter_search.html', districts=districts)

# 全施設一覧ページ
@app.route('/all_shelters')
def all_shelters():
    district = request.args.get('district', '')
    sort = request.args.get('sort', '')
    return render_template(
        'search_results.html',
        results=prepare_shelters(filter_and_sort_shelters(shelters, district, sort)),
        district=district.strip(),
        sort=sort if sort in ('name', 'recommendation', 'crowding', 'distance') else '',
    )


@app.route('/board')
@login_required
def board():
    area_filter = request.args.get('area', '').strip()
    warning_filter = request.args.get('warning_type', '').strip()
    announcements = []
    board_instructions = []
    for item in instructions:
        normalized = dict(item)
        normalized['category'] = item_category(item)
        normalized['area_display'] = display_area(item.get('area', ''))
        if normalized['category'] == 'announcement':
            if area_filter and area_filter not in str(item.get('area', '')).split(','):
                continue
            if warning_filter and item.get('warning_type', '') != warning_filter:
                continue
            announcements.append(normalized)
        else:
            board_instructions.append(normalized)
    sort_key = lambda item: item.get('updated_at', item.get('created_at', ''))
    announcements.sort(key=sort_key, reverse=True)
    board_instructions.sort(key=sort_key, reverse=True)
    return render_template(
        'board.html', announcements=announcements, instructions=board_instructions,
        areas=AREAS, warning_options=WARNING_OPTIONS,
        area_filter=area_filter, warning_filter=warning_filter,
    )


@app.route('/announcement_register', methods=['GET', 'POST'])
@login_required
def announcement_register():
    message = ''
    error = ''
    if request.method == 'POST':
        selected_areas = [area for area in request.form.getlist('area') if area in AREAS]
        if not selected_areas:
            error = translate('announcement_area_required')
        else:
            now = get_japan_time()
            instructions.append({
                'id': next_instruction_id(), 'category': 'announcement', 'target': '住民',
                'area': ','.join(selected_areas),
                'warning_type': request.form.get('warning_type', '通常').strip() or '通常',
                'content': request.form.get('content', ''),
                'status': (
                    request.form.get('status', '発令').strip()
                    if request.form.get('status', '').strip() in ANNOUNCEMENT_STATUSES
                    else '発令'
                ),
                'created_at': now, 'updated_at': now,
            })
            save_instructions()
            message = translate('announcement_registered')
    return render_template(
        'announcement_register.html', areas=AREAS, warning_options=WARNING_OPTIONS,
        announcement_statuses=ANNOUNCEMENT_STATUSES, message=message, error=error,
    )


@app.route('/instruction_register', methods=['GET', 'POST'])
@login_required
def instruction_register():
    message = ''
    error = ''
    if request.method == 'POST':
        source = request.form.get('source', '').strip()
        target = request.form.get('target', '').strip()
        content = request.form.get('content', '').strip()
        if source not in DEPARTMENTS or target not in DEPARTMENTS:
            error = '指示元部署と対象部署を選択してください。'
        elif not content:
            error = '指示内容を入力してください。'
        else:
            now = get_japan_time()
            instructions.append({
                'id': next_instruction_id(), 'category': 'instruction',
                'source': source, 'target': target, 'content': content,
                'shelter': request.form.get('shelter', '').strip(),
                'status': request.form.get('status', '未対応').strip() or '未対応',
                'created_at': now, 'updated_at': now,
            })
            save_instructions()
            message = '指示を登録しました。'
    return render_template(
        'instruction_register.html', departments=DEPARTMENTS,
        statuses=INSTRUCTION_STATUSES, shelters=shelters, message=message, error=error,
    )

# 検索結果ページ：templates/search_results.html を返す
@app.route('/search_results')
def search_results():
    district = request.args.get('district', '')
    sort = request.args.get('sort', '')
    return render_template(
        'search_results.html',
        results=prepare_shelters(filter_and_sort_shelters(shelters, district, sort)),
        district=district.strip(),
        sort=sort if sort in ('name', 'recommendation', 'crowding', 'distance') else '',
    )

# JSON API：/shelters?district=地区名
@app.route('/shelters', methods=['GET'])
def get_shelters():
    results = filter_shelters(request.args.get('district'))

    if not results:
        # 見つからなければエラー JSON を返す
        return jsonify({'error': 'No shelters found'}), 404

    # 見つかったらリストを JSON で返す
    return jsonify(results)

# 気象警報・注意報API
@app.route('/api/weather_warnings')
def api_weather_warnings():
    """気象警報・注意報をJSON形式で返すAPI"""
    return jsonify(get_weather_warnings())

if __name__ == '__main__':
    app.run(debug=True, port=5000)
