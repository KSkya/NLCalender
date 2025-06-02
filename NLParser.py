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

import re
from datetime import datetime, timedelta
import dateparser
import os
from typing import Tuple
from typing_extensions import deprecated
from dotenv import load_dotenv
from abc import ABC, abstractmethod
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import torch
import json


os.chdir(os.path.dirname(os.path.abspath(__file__)))
load_dotenv("./setup.env")
MODEL_PATH = os.getenv("MODEL_PATH")
assert MODEL_PATH != None



######## This section should not be changed! ########
class BaseParser(ABC):
    """
    Parser base class

    The inherited class must define `parse` method for parsing inputs
    """
    def __init__(self, reference_time=None, **kwargs):
        self.reference_time = reference_time or datetime.now()
    
    @abstractmethod
    def parse(self, text) -> Tuple[str]:...
#####################################################



class LLMEventParser(BaseParser):
    """
    Natural languages parser with LLM
    """
    def __init__(self, reference_time=None, model_path=MODEL_PATH, device=None, **kwargs):
        super().__init__(reference_time=reference_time, **kwargs)
        
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(model_path, 
                                                          trust_remote_code=True,
                                                          device_map = "auto" if self.device else {"":"cpu"},
                                                          quantization_config=BitsAndBytesConfig(
                                                            load_in_4bit=True,  # ここで指定
                                                            bnb_4bit_quant_type="nf4",
                                                            bnb_4bit_use_double_quant=True,
                                                            bnb_4bit_compute_dtype=torch.float16  # または bfloat16
                                                        )).to(self.device)


    def parse(self, text: str):
        prompt = self._build_prompt(text)
        
        model_inputs = self.tokenizer([prompt], return_tensors="pt").to(self.model.device)

        generated_ids = self.model.generate(
            **model_inputs,
            max_new_tokens=128,  # 必要に応じて調整
            do_sample=True,
            temperature=0.1,
            top_p=0.99,
            top_k=10
        )

        output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()
        output_text = self.tokenizer.decode(output_ids, skip_special_tokens=True).strip()

        try:
            parsed = json.loads(output_text)
            return parsed
        except Exception as e:
            raise ValueError(f"LLM出力の解析に失敗しました: {e}\n生成結果:\n{output_text}")
        

    def _build_prompt(self, user_input: str):
        prompt = f"""以下の文章は、予定に関する自然言語の記述です。
今日の日付は {self.reference_time.strftime("%Y年%m月%d日")} です。文章に「明日」「明後日」などの表現がある場合は、これを基準に日時を解釈してください。

文章: 「{user_input}」

この文章から、次の形式で予定の情報を抽出してください：
- action: 予定の追加/変更/削除のいずれか
- title: 予定の名前
- start: 開始日時（変更の場合は変更後開始日時）
- end: 終了日時（なければ1時間後）（変更の場合は変更後終了日時）
- all_day: 終日か否か
- original_title: 変更前の名前（変更しない場合はtitleと同じ）
- original_start: 変更前の開始日時（変更しない場合はstartと同じ）

出力形式:""""""
{"action": "add"/"modify"/"delete", "title": "...", "start": "yyyy-mm-ddThh:mm:ss", "end": "yyyy-mm-ddThh:mm:ss", "all_day": true/false, "original_title": "...", "original_start": "yyyy-mm-ddThh:mm:ss"}

出力:"""
        
        messages = [
            {"role": "user", "content": prompt}
        ]

        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False
        )

        return text

    def _extract_json_like(self, text: str) -> str:
        """LLM出力からJSONに似た部分だけ抽出する簡易関数"""
        import re
        match = re.search(r"\{[\s\S]*?\}", text)
        return match.group(0) if match else "{}"



@deprecated("This class is not recommended for use in natural language parsing modules. Use LLMEventParser instead.")
class FormatEventParser(BaseParser):
    """
    Formal parsing of natural languages
    """
    def __init__(self, reference_time=None, **kwargs):
        super().__init__(reference_time=reference_time, **kwargs)

    def parse(self, text):
        """
        入力された自然言語からイベント情報を抽出し、
        title, start_datetime, end_datetime, all_day の4つを返す
        """
        original_text = text.strip()
        text = original_text

        # 相対表現変換（明日、明後日など）
        relative_replacements = {
            '明後日': (self.reference_time + timedelta(days=2)).strftime('%Y-%m-%d'),
            '明日': (self.reference_time + timedelta(days=1)).strftime('%Y-%m-%d'),
            '今日': self.reference_time.strftime('%Y-%m-%d'),
        }
        for key, val in relative_replacements.items():
            text = text.replace(key, val)

        # 日時情報の抽出
        time_range_pattern = r'(\d{1,2})[:時](\d{1,2})?[\s〜～-から〜ー]+(\d{1,2})[:時](\d{1,2})?'
        single_time_pattern = r'(\d{1,2})[:時](\d{1,2})?'
        date_range_pattern = r'(\d{4}[\/年]\d{1,2}[\/月]\d{1,2})[\s〜～-]*(\d{4}[\/年]\d{1,2}[\/月]\d{1,2})'
        single_date_pattern = r'(\d{4}[\/年]\d{1,2}[\/月]\d{1,2})'

        time_range_match = re.search(time_range_pattern, text)
        single_time_match = re.search(single_time_pattern, text)
        date_range_match = re.search(date_range_pattern, text)
        single_date_match = re.search(single_date_pattern, text)

        has_time = bool(time_range_match or single_time_match)
        has_date = bool(date_range_match or single_date_match)

        # 日付と時刻の初期値
        start = self.reference_time + timedelta(days=1)
        end = start + timedelta(hours=1)
        all_day = not has_time

        # 日付レンジ処理
        if date_range_match:
            start = dateparser.parse(date_range_match.group(1), settings={'RELATIVE_BASE': self.reference_time})
            end = dateparser.parse(date_range_match.group(2), settings={'RELATIVE_BASE': self.reference_time}) + timedelta(days=1)
            all_day = True

        # 単一日付＋時刻 or 単独時刻処理
        elif single_date_match:
            start = dateparser.parse(single_date_match.group(1), settings={'RELATIVE_BASE': self.reference_time})
            if time_range_match:
                sh, sm, eh, em = time_range_match.groups()
                start = start.replace(hour=int(sh), minute=int(sm or 0))
                end = start.replace(hour=int(eh), minute=int(em or 0))
                if end <= start:
                    end = start + timedelta(hours=1)
                all_day = False
            elif single_time_match:
                hour = int(single_time_match.group(1))
                minute = int(single_time_match.group(2)) if single_time_match.group(2) else 0
                start = start.replace(hour=hour, minute=minute)
                end = start + timedelta(hours=1)
                all_day = False
            else:
                end = start + timedelta(days=1)
                all_day = True

        # 時刻だけある（"10時から12時"のような場合）
        elif time_range_match and not single_date_match:
            start = self.reference_time
            sh, sm, eh, em = time_range_match.groups()
            start = start.replace(hour=int(sh), minute=int(sm or 0))
            end = start.replace(hour=int(eh), minute=int(em or 0))
            if end <= start:
                end = start + timedelta(hours=1)
            all_day = False

        elif single_time_match and not single_date_match:
            hour = int(single_time_match.group(1))
            minute = int(single_time_match.group(2)) if single_time_match.group(2) else 0
            start = start.replace(hour=hour, minute=minute)
            end = start + timedelta(hours=1)
            all_day = False

        # titleの抽出：既知の日時部分を除去した残り
        cleaned_text = original_text
        for pattern in [time_range_pattern, single_time_pattern, date_range_pattern, single_date_pattern] + list(relative_replacements.keys()):
            cleaned_text = re.sub(pattern, '', cleaned_text)

        title_candidates = re.split(r'[\s\-〜～、。]', cleaned_text.strip())
        title = next((t for t in reversed(title_candidates) if t), "無題の予定")

        return title.strip(), start.isoformat(), end.isoformat(), all_day




if __name__ == "__main__":
    parser = LLMEventParser()
    output = parser.parse("今日20時から3時間数学の勉強")
    print(output)

