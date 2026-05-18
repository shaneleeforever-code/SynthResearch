"""
SynthResearch - OpenAI API 引擎封装
支持 OpenAI 原生 SDK + 兼容 DeepSeek/Ollama/Kimi 等
"""

import json
import openai
import httpx
import time
from typing import Optional, Generator


def _current_language(default: str = "English") -> str:
    try:
        import streamlit as st
        lang = st.session_state.get("ui_lang_radio", st.session_state.get("ui_lang", default))
        return lang if lang in ("中文", "English") else default
    except Exception:
        return default


class SynthEngine:
    """OpenAI API 调用封装引擎"""

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1", model: str = "gpt-4o"):
        # Some local agent/sandbox environments inject a dead proxy such as
        # 127.0.0.1:9. Do not inherit proxy env vars unless configured in code.
        http_client = httpx.Client(trust_env=False, timeout=180)
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url, http_client=http_client)
        self.model = model

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        json_mode: bool = False,
    ) -> str:
        """同步聊天调用"""
        # 注入多语言要求
        try:
            output_lang = _current_language()
            if output_lang:
                lang_instruction = f"\n\n[CRITICAL REQUIREMENT] You MUST reply in the following language: {output_lang}"
                system_prompt += lang_instruction
        except Exception:
            pass

        kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(**kwargs)
                return response.choices[0].message.content.strip()
            except openai.RateLimitError:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise
            except openai.APIConnectionError as e:
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    from .i18n import t
                    raise Exception(f"{t('API Connection Failed')}: {e}")

    def chat_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> Generator[str, None, None]:
        """流式聊天调用"""
        # 注入多语言要求
        try:
            output_lang = _current_language()
            if output_lang:
                lang_instruction = f"\n\n[CRITICAL REQUIREMENT] You MUST reply in the following language: {output_lang}"
                system_prompt += lang_instruction
        except Exception:
            pass

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def chat_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3, # Lower temperature for JSON
        max_tokens: int = 1000,   # Increased tokens to prevent truncation
    ) -> dict:
        """
        JSON Mode 调用，自动解析返回。
        增加了极其严格的格式指令和多层级解析兜底。
        """
        import re
        # 确定语言偏好
        output_lang = _current_language("English")
        
        # 强制注入 JSON 指令，要求键名匹配 Schema
        strict_json_prompt = (
            f"\n\n[OUTPUT RULE: STRICT JSON ONLY]\n"
            f"1. You MUST output ONLY a valid JSON object.\n"
            f"2. All JSON KEYS must match the provided schema EXACTLY. Do NOT translate or change them.\n"
            f"3. All JSON text values must be in {output_lang} where applicable.\n"
            f"4. Do NOT include markdown code blocks (```json ... ```) or any other text.\n"
            f"5. Do NOT include any preamble, conversational text, or headers.\n"
        )
        
        messages = [
            {"role": "system", "content": system_prompt + strict_json_prompt},
            {"role": "user", "content": user_prompt},
        ]

        max_retries = 4
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format={"type": "json_object"}
                )
                raw = response.choices[0].message.content.strip()
                break
            except (openai.APIConnectionError, openai.APITimeoutError, openai.RateLimitError) as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                from .i18n import t
                raise RuntimeError(t("API 连接失败，请检查网络、Base URL 或代理设置。")) from e
            except Exception:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                raw = response.choices[0].message.content.strip()
                break

        # 清理可能的 markdown 噪点
        content = raw.strip()
        # 移除可能存在的 markdown 代码块包裹
        content = re.sub(r"^```(?:json)?", "", content, flags=re.MULTILINE)
        content = re.sub(r"```$", "", content, flags=re.MULTILINE)
        content = content.strip()

        # 多重尝试解析
        try:
            # 1. 尝试直接解析（最理想情况）
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # 2. 尝试从第一个 { 或 [ 开始提取并修复
        match = re.search(r"([\{\[].*)", content, re.DOTALL)
        if match:
            candidate = match.group(1)
            try:
                # 尝试直接解析提取的部分
                # 注意：这里需要再次尝试正则提取最完整的 {} 或 [] 结构
                inner_match = re.search(r"(\{.*\}|\[.*\])", candidate, re.DOTALL)
                if inner_match:
                    return json.loads(inner_match.group(1))
            except:
                pass
                
            try:
                # 尝试修复提取的部分
                fixed = self._fix_truncated_json(candidate)
                return json.loads(fixed)
            except:
                pass

        # 3. 提取首个数组作为 fallback (针对极端乱码/中途截断情况)
        try:
            start_idx = content.find('[')
            if start_idx != -1:
                array_str = content[start_idx:]
                fixed_array_str = self._fix_truncated_json(array_str)
                parsed = json.loads(fixed_array_str)
                if isinstance(parsed, list):
                    return {"items": parsed}
        except:
            pass

        # 4. 正则暴力提取所有字符串
        try:
            start_idx = content.find('[')
            if start_idx != -1:
                import re
                array_str = content[start_idx:]
                # 尝试提取键值对中的 values（冒号后的字符串）
                strings = re.findall(r':\s*"([^"\\]*(?:\\.[^"\\]*)*)"', array_str)
                # 如果没找到冒号，可能是纯数组，降级为提取所有字符串并过滤已知键名
                if not strings:
                    strings = re.findall(r'"([^"\\]*(?:\\.[^"\\]*)*)"', array_str)
                    known_keys = {"challenge_name", "challenge_description", "matching_reason", "items", "questions", "dims", "name", "description", "id", "prediction_overview", "specific_challenges", "target_group_overview"}
                    strings = [s for s in strings if s not in known_keys]
                if strings:
                    return {"items": strings}
        except:
            pass

        # 5. 终极兜底：报错
        from .i18n import t
        raise ValueError(f"{t('JSON Parsing Failed')}: {content[:150]}...")


    def _fix_truncated_json(self, json_str: str) -> str:
        """尝试通过闭合括号修复截断的 JSON"""
        json_str = json_str.strip()
        if not json_str:
            return "{}"
        
        # 栈逻辑闭合括号
        stack = []
        in_string = False
        escape = False
        
        fixed_chars = []
        for char in json_str:
            if escape:
                escape = False
                fixed_chars.append(char)
                continue
            if char == '\\':
                escape = True
                fixed_chars.append(char)
                continue
            if char == '"':
                in_string = not in_string
                fixed_chars.append(char)
                continue
            
            if not in_string:
                if char in '{[':
                    stack.append(char)
                elif char in '}]':
                    if stack:
                        opening = stack.pop()
                        # 检查匹配（可选，简单处理）
            fixed_chars.append(char)
        
        fixed_str = "".join(fixed_chars)
        
        # 如果在字符串内部截断，闭合引号
        if in_string:
            fixed_str += '"'
            
        # 闭合所有括号
        while stack:
            opening = stack.pop()
            if opening == '{':
                fixed_str += '}'
            else:
                fixed_str += ']'
                
        return fixed_str
