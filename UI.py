# Copyright 2025 KSkya
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import streamlit as st
from streamlit_calendar import calendar
from datetime import datetime, timedelta
import uuid

from event_storage import load_events, save_events


# LLMEventParserの読み込み関数で隔離（watcher対策）
@st.cache_resource(show_spinner="モジュールを読み込んでいます...")
def get_llm_parser():
    from NLParser import LLMEventParser
    return LLMEventParser()  # パスは適宜書き換えてください



# セッション状態の初期化
if "events" not in st.session_state:
    st.session_state["events"] = load_events()

if "edit_index" not in st.session_state:
    st.session_state["edit_index"] = None

# UIセットアップ
st.header("NL Calendar")
parser = get_llm_parser()

tab1, tab2 = st.tabs(["自然言語入力", "形式入力"])

with tab1:
    st.text("※予定変更処理は, 具体的な時間（2025/4/1など）を指定するとうまくいきやすいです。")
    if "natural_text_input" not in st.session_state:
        st.session_state["natural_text_input"] = ""

    st.text_input(
        "自然言語入力",
        key="natural_text_input",
        on_change=lambda: st.session_state.update({"trigger_parse": True})
    )

    if st.button("解析") or st.session_state.get("trigger_parse"):
        try:
            input_text = st.session_state["natural_text_input"]
            result = parser.parse(input_text)
            print(f"parsed -> {result}")
            action = result.get("action", "add")
            if action == "add":
                st.session_state["parsed_event"] = {
                    "title": result["title"],
                    "start": result["start"],
                    "end": result["end"],
                    "allDay": result["all_day"]
                }
            elif action == "modify":
                # 編集対象を検索
                index_to_update = next(
                    (i for i, e in enumerate(st.session_state["events"])
                     if e["title"] == result["original_title"]
                     and e["start"].startswith(result["original_start"][:16])  # 時分まで比較
                    ), None)
                if index_to_update is not None:
                    st.session_state["events"][index_to_update] = {
                        "title": result["title"],
                        "start": result["start"],
                        "end": result["end"],
                        "allDay": result["all_day"]
                    }
                    st.success("予定を編集しました")
                    st.session_state["CalKey"] = str(uuid.uuid4())
                    save_events(st.session_state["events"])
                    st.rerun()
                else:
                    st.warning("該当する編集対象が見つかりませんでした")
            elif action == "delete":
                st.session_state["events"] = [
                    e for e in st.session_state["events"]
                    if not (e["title"] == result["original_title"]
                            and e["start"].startswith(result["original_start"][:16]))
                ]
                save_events(st.session_state["events"])
                st.success("予定を削除しました")
                st.session_state["CalKey"] = str(uuid.uuid4())
                st.rerun()
        except Exception as e:
            st.error(f"予定の解析に失敗しました: {e}")
            st.session_state.pop("parsed_event", None)
        finally:
            st.session_state["trigger_parse"] = False  # フラグリセット
            

    # 確認UI
    if "parsed_event" in st.session_state:
        parsed = st.session_state["parsed_event"]

        start_dt = datetime.fromisoformat(parsed["start"])
        end_dt = datetime.fromisoformat(parsed["end"])

        if parsed["allDay"]:
            start_str = start_dt.strftime("%Y/%m/%d")
            end_str = end_dt.strftime("%Y/%m/%d")  # 終日予定は範囲的
            datetime_label = f"{start_str}～{end_str}（終日）"
        else:
            datetime_label = f"{start_dt.strftime('%Y/%m/%d %H:%M')}～{end_dt.strftime('%H:%M')}"

        st.markdown("### 📝 登録内容の確認")
        st.write(f"**日程**：{datetime_label}")
        st.write(f"**内容**：{parsed['title']}")
        confirm_col1, confirm_col2 = st.columns(2)
        with confirm_col1:
            if st.button("登録", key="confirm_register"):
                st.session_state["events"].append(parsed)
                save_events(st.session_state["events"])
                st.session_state["CalKey"] = str(uuid.uuid4())
                st.session_state.pop("parsed_event", None)
                st.rerun()
        with confirm_col2:
            if st.button("キャンセル", key="cancel_register"):
                st.session_state.pop("parsed_event", None)


with tab2:
    st.subheader("形式入力")

    # 編集対象を選択
    event_titles = [f"{i+1}: {e['title']} ({e['start']}～{e['end']})" for i, e in enumerate(st.session_state["events"])]
    selected_event = st.selectbox("予定を選択（編集・削除）", ["新規追加"] + event_titles)

    is_edit = selected_event != "新規追加"
    event_index = event_titles.index(selected_event) if is_edit else None
    event_data = st.session_state["events"][event_index] if is_edit else {}

    # 一時保存用セッションキー（新規追加時も維持）
    if "form_cache" not in st.session_state:
        st.session_state["form_cache"] = {}

    # キャッシュ初期化
    cache = st.session_state["form_cache"]
    if not is_edit and "init_done" not in cache:
        now = datetime.now()
        cache["title"] = "予定のタイトル"
        cache["allDay"] = True
        cache["start_date"] = now.date()
        cache["start_time"] = now.time().replace(second=0, microsecond=0)
        cache["end_date"] = (now + timedelta(days=1)).date()
        cache["end_time"] = now.time().replace(second=0, microsecond=0)
        cache["init_done"] = True
    elif is_edit:
        start_dt = datetime.fromisoformat(event_data["start"])
        end_dt = datetime.fromisoformat(event_data["end"])
        cache["title"] = event_data["title"]
        cache["allDay"] = event_data.get("allDay", True)
        cache["start_date"] = start_dt.date()
        cache["start_time"] = start_dt.time()
        cache["end_date"] = end_dt.date()
        cache["end_time"] = end_dt.time()

    # 各フィールドの初期値
    default_title = event_data.get("title", "")
    default_start = datetime.fromisoformat(event_data.get("start", datetime.now().isoformat()))
    default_end = datetime.fromisoformat(event_data.get("end", (datetime.now() + timedelta(days=1)).isoformat()))
    default_all_day = event_data.get("allDay", True)

    # 入力項目
    title = st.text_input("予定のタイトル", value=cache["title"], key="title_input")
    all_day = st.checkbox("終日予定", value=cache["allDay"], key="all_day_toggle")
    start_date = st.date_input("開始日", value=cache["start_date"], key="start_date_input")
    if not all_day:
        start_time = st.time_input("開始時刻", value=cache["start_time"], key="start_time_input")
        end_time = st.time_input("終了時刻", value=cache["end_time"], key="end_time_input")
    else:
        # dummy time (00:00) for all-day events
        start_time = datetime.min.time()
        end_time = datetime.min.time()
    end_date = st.date_input("終了日", value=cache["end_date"], key="end_date_input")

    # 登録ボタン群
    col1, col2 = st.columns(2)
    with col1:
        if st.button("登録（新規 / 更新）"):
            start_dt = datetime.combine(start_date, start_time)
            end_dt = datetime.combine(end_date, end_time)
            new_event = {
                "title": title,
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat(),
                "allDay": all_day
            }
            if is_edit:
                st.session_state["events"][event_index] = new_event
            else:
                st.session_state["events"].append(new_event)
            st.session_state.pop("form_cache", None)  # キャッシュクリア
            save_events(st.session_state["events"])
            st.session_state["CalKey"] = str(uuid.uuid4())
            st.rerun()

    with col2:
        if is_edit and st.button("この予定を削除"):
            st.session_state["events"].pop(event_index)
            save_events(st.session_state["events"])
            st.session_state["CalKey"] = str(uuid.uuid4())
            st.rerun()



# カレンダーの表示
calendar_options = {
    "editable": True,
    "selectable": True,
    "initialView": "dayGridMonth",
    "height": 700,
}

event_return = calendar(
    events=st.session_state["events"],
    options=calendar_options,
    key=st.session_state.get("CalKey", "default")
)

# イベントがクリックされたときの詳細表示
if event_return.get("eventClick") is not None:
    event_click = event_return.get("eventClick")
    event = event_click["event"]

    title = event.get("title", "")
    start = event.get("start", "")
    end = event.get("end", "")
    all_day = event.get("allDay", False)

    start_dt = datetime.fromisoformat(start)
    start_str = start_dt.strftime("%Y/%m/%d %H:%M") if not all_day else start_dt.strftime("%Y/%m/%d")

    if end:
        try:
            end_dt = datetime.fromisoformat(end)
            end_str = end_dt.strftime("%Y/%m/%d %H:%M") if not all_day else end_dt.strftime("%Y/%m/%d")
        except ValueError:
            end_str = "(無効な終了日時)"
    else:
        end_str = "(終了時間なし)"

    st.markdown("### 📅 選択された予定")
    st.write(f"**タイトル**: {title}")
    st.write(f"**開始**: {start_str}")
    st.write(f"**終了**: {end_str}")
    st.write(f"**終日**: {'はい' if all_day else 'いいえ'}")
