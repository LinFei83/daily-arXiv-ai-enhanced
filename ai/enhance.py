import os
import json
import sys
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional

import dotenv
import argparse

import langchain_core.exceptions
from langchain_openai import ChatOpenAI
from langchain.prompts import (
  ChatPromptTemplate,
  SystemMessagePromptTemplate,
  HumanMessagePromptTemplate,
)
from structure import Structure
if os.path.exists('.env'):
    dotenv.load_dotenv()
template = open("template.txt", "r").read()
system = open("system.txt", "r").read()

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, required=True, help="jsonline data file")
    return parser.parse_args()

def load_existing_ids(output_file):
    """加载输出文件中已有的论文ID"""
    existing_ids = set()
    if os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            if 'id' in data:
                                existing_ids.add(data['id'])
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            print(f"读取现有文件时出错: {e}", file=sys.stderr)
    return existing_ids

import json
 
def parse_llm_response(response_text):
    """
    解析LLM返回的文本为结构化数据。
    这个版本会保留原始的UTF-8字符（如中文），而不是转换成Unicode转义序列。
    """
    try:
        # 尝试直接解析整个响应为JSON
        data = json.loads(response_text)
        return data  # 直接返回解析后的数据
    except json.JSONDecodeError:
        # 如果失败，尝试提取JSON部分
        try:
            # 查找可能的JSON开始和结束位置
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                data = json.loads(json_str)
                return data # 直接返回解析后的数据
        except (json.JSONDecodeError, ValueError):
            # 捕获提取和解析过程中可能出现的任何错误
            pass
        
        # 如果以上所有尝试都失败，返回固定的错误结构
        return {
            "tldr": "解析错误",
            "motivation": "解析错误",
            "method": "解析错误",
            "result": "解析错误",
            "conclusion": "解析错误"
        }

def process_single_paper_with_retry(chain, paper_data: Dict[str, Any], language: str, max_retries: int = 3) -> Dict[str, Any]:
    """
    处理单篇论文，带重试机制
    """
    paper_id = paper_data.get('id', 'unknown')
    
    for attempt in range(max_retries):
        try:
            # 添加随机延迟以避免同时请求
            if attempt > 0:
                delay = random.uniform(1, 3) * (2 ** attempt)  # 指数退避
                print(f"论文 {paper_id} 第 {attempt + 1} 次重试，等待 {delay:.2f} 秒...", file=sys.stderr)
                time.sleep(delay)
            
            # 调用LLM处理
            input_data = {"language": language, "content": paper_data['summary']}
            result = chain.invoke(input_data)
            
            # 解析响应为结构化数据
            response_text = result.content
            structured_data = parse_llm_response(response_text)
            
            # 确保所有必要字段都存在
            required_fields = ["tldr", "motivation", "method", "result", "conclusion"]
            for field in required_fields:
                if field not in structured_data:
                    structured_data[field] = "未提供"
            
            paper_data['AI'] = structured_data
            print(f"论文 {paper_id} 处理成功", file=sys.stderr)
            return paper_data
            
        except Exception as e:
            print(f"论文 {paper_id} 第 {attempt + 1} 次尝试失败: {e}", file=sys.stderr)
            
            # 如果是最后一次尝试，返回错误结果
            if attempt == max_retries - 1:
                print(f"论文 {paper_id} 达到最大重试次数，跳过处理", file=sys.stderr)
                paper_data['AI'] = {
                    "tldr": "处理失败",
                    "motivation": "处理失败",
                    "method": "处理失败", 
                    "result": "处理失败",
                    "conclusion": "处理失败"
                }
                return paper_data

def process_papers_concurrently(chain, papers: List[Dict[str, Any]], language: str, 
                               concurrent_requests: int, output_file: str) -> None:
    """
    并发处理论文，每处理完一篇就写入文件
    """
    successful_count = 0
    failed_count = 0
    
    with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
        # 提交所有任务
        future_to_paper = {
            executor.submit(process_single_paper_with_retry, chain, paper, language): paper 
            for paper in papers
        }
        
        # 处理完成的任务
        for future in as_completed(future_to_paper):
            paper = future_to_paper[future]
            try:
                processed_paper = future.result()
                
                # 立即写入文件
                with open(output_file, "a", encoding='utf-8') as f:
                    f.write(json.dumps(processed_paper, ensure_ascii=False) + "\n")
                
                if processed_paper['AI']['tldr'] != "处理失败":
                    successful_count += 1
                else:
                    failed_count += 1
                    
                print(f"进度: 成功 {successful_count}, 失败 {failed_count}, 剩余 {len(papers) - successful_count - failed_count}", file=sys.stderr)
                
            except Exception as e:
                print(f"处理论文时发生意外错误: {e}", file=sys.stderr)
                failed_count += 1
    
    print(f"处理完成! 成功: {successful_count}, 失败: {failed_count}", file=sys.stderr)

def main():
    args = parse_args()
    model_name = os.environ.get("MODEL_NAME", 'deepseek-chat')
    language = os.environ.get("LANGUAGE", 'Chinese')
    concurrent_requests = int(os.environ.get("CONCURRENT_REQUESTS", 5))
    max_retries = int(os.environ.get("MAX_RETRIES", 3))

    # 构建输出文件名
    output_file = args.data.replace('.jsonl', f'_AI_enhanced_{language}.jsonl')
    
    # 加载已有的论文ID
    existing_ids = load_existing_ids(output_file)
    print(f'已有论文数量: {len(existing_ids)}', file=sys.stderr)

    data = []
    try:
        with open(args.data, "r", encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"跳过第 {line_num} 行，JSON解析错误: {e}", file=sys.stderr)
    except FileNotFoundError:
        print(f"错误: 找不到数据文件 {args.data}", file=sys.stderr)
        return
    except Exception as e:
        print(f"读取数据文件时出错: {e}", file=sys.stderr)
        return

    seen_ids = set()
    unique_data = []
    for item in data:
        item_id = item.get('id', 'unknown')
        # 同时检查当前批次的重复和输出文件中的重复
        if item_id not in seen_ids and item_id not in existing_ids:
            seen_ids.add(item_id)
            unique_data.append(item)
        elif item_id in existing_ids:
            print(f'跳过已处理的论文: {item_id}', file=sys.stderr)

    data = unique_data
    print(f'需要处理的新论文数量: {len(data)}', file=sys.stderr)

    if not data:
        print('没有需要处理的新论文', file=sys.stderr)
        return

    print('Open:', args.data, file=sys.stderr)

    try:
        # 不使用function_calling，直接使用LLM
        llm = ChatOpenAI(model=model_name)
        print('Connect to:', model_name, file=sys.stderr)
        prompt_template = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system),
            HumanMessagePromptTemplate.from_template(template=template)
        ])

        chain = prompt_template | llm
        
        print(f"正在以 {concurrent_requests} 的并发数处理 {len(data)} 篇论文，最大重试次数: {max_retries}...", file=sys.stderr)
        
        # 使用新的并发处理函数
        process_papers_concurrently(chain, data, language, concurrent_requests, output_file)
        
    except Exception as e:
        print(f"初始化LLM或处理过程中发生错误: {e}", file=sys.stderr)
        return

if __name__ == "__main__":
    main()
