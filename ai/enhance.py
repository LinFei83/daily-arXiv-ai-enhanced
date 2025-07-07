import os
import json
import sys

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

def main():
    args = parse_args()
    model_name = os.environ.get("MODEL_NAME", 'deepseek-chat')
    language = os.environ.get("LANGUAGE", 'Chinese')

    # 构建输出文件名
    output_file = args.data.replace('.jsonl', f'_AI_enhanced_{language}.jsonl')
    
    # 加载已有的论文ID
    existing_ids = load_existing_ids(output_file)
    print(f'已有论文数量: {len(existing_ids)}', file=sys.stderr)

    data = []
    with open(args.data, "r") as f:
        for line in f:
            data.append(json.loads(line))

    seen_ids = set()
    unique_data = []
    for item in data:
        item_id = item['id']
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

    llm = ChatOpenAI(model=model_name).with_structured_output(Structure, method="function_calling")
    print('Connect to:', model_name, file=sys.stderr)
    prompt_template = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system),
        HumanMessagePromptTemplate.from_template(template=template)
    ])

    chain = prompt_template | llm

    for idx, d in enumerate(data):
        try:
            response: Structure = chain.invoke({
                "language": language,
                "content": d['summary']
            })
            d['AI'] = response.model_dump()
        except langchain_core.exceptions.OutputParserException as e:
            print(f"{d['id']} has an error: {e}", file=sys.stderr)
            d['AI'] = {
                 "tldr": "Error",
                 "motivation": "Error",
                 "method": "Error",
                 "result": "Error",
                 "conclusion": "Error"
            }
        with open(output_file, "a", encoding='utf-8') as f:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")

        print(f"Finished {idx+1}/{len(data)}", file=sys.stderr)

if __name__ == "__main__":
    main()
