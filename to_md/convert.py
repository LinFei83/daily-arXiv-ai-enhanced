import json
import argparse
import os
import sys
from itertools import count

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, help="Path to the jsonline file")
    args = parser.parse_args()
    
    # 检查文件是否存在
    if not args.data:
        print("错误: 请提供数据文件路径", file=sys.stderr)
        exit(1)
    
    if not os.path.exists(args.data):
        print(f"错误: 找不到数据文件 {args.data}", file=sys.stderr)
        exit(1)
    
    data = []
    preference = os.environ.get('CATEGORIES', 'cs.CV, cs.CL').split(',')
    preference = list(map(lambda x: x.strip(), preference))
    def rank(cate):
        if cate in preference:
            return preference.index(cate)
        else:
            return len(preference)

    try:
        with open(args.data, "r", encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    line = line.strip()
                    if line:  # 跳过空行
                        data.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"跳过第 {line_num} 行，JSON解析错误: {e}", file=sys.stderr)
                    continue
    except Exception as e:
        print(f"读取文件时出错: {e}", file=sys.stderr)
        exit(1)

    if not data:
        print("警告: 没有找到有效的数据", file=sys.stderr)
        exit(1)

    # 检查数据完整性并过滤无效数据
    valid_data = []
    for i, item in enumerate(data):
        try:
            # 检查必要字段
            required_fields = ["categories", "title", "authors", "summary", "abs", "AI"]
            missing_fields = [field for field in required_fields if field not in item or not item[field]]
            
            if missing_fields:
                print(f"跳过第 {i+1} 条数据，缺少字段: {missing_fields}", file=sys.stderr)
                continue
                
            # 检查AI字段的完整性
            if isinstance(item["AI"], dict):
                ai_fields = ["tldr", "motivation", "method", "result", "conclusion"]
                missing_ai_fields = [field for field in ai_fields if field not in item["AI"]]
                if missing_ai_fields:
                    print(f"跳过第 {i+1} 条数据，AI字段不完整: {missing_ai_fields}", file=sys.stderr)
                    continue
            else:
                print(f"跳过第 {i+1} 条数据，AI字段格式错误", file=sys.stderr)
                continue
                
            valid_data.append(item)
        except Exception as e:
            print(f"跳过第 {i+1} 条数据，处理时出错: {e}", file=sys.stderr)
            continue
    
    data = valid_data
    if not data:
        print("错误: 没有找到有效的论文数据", file=sys.stderr)
        exit(1)
    
    print(f"找到 {len(data)} 篇有效论文", file=sys.stderr)

    categories = set([item["categories"][0] for item in data])
    
    # 读取模板文件，添加错误处理
    try:
        with open("paper_template.md", "r", encoding='utf-8') as f:
            template = f.read()
    except FileNotFoundError:
        print("错误: 找不到模板文件 paper_template.md", file=sys.stderr)
        exit(1)
    except Exception as e:
        print(f"读取模板文件时出错: {e}", file=sys.stderr)
        exit(1)
    
    categories = sorted(categories, key=rank)
    cnt = {cate: 0 for cate in categories}
    for item in data:
        if item["categories"][0] not in cnt.keys():
            continue
        cnt[item["categories"][0]] += 1

    markdown = f"<div id=toc></div>\n\n# Table of Contents\n\n"
    for idx, cate in enumerate(categories):
        markdown += f"- [{cate}](#{cate}) [Total: {cnt[cate]}]\n"

    idx = count(1)
    for cate in categories:
        markdown += f"\n\n<div id='{cate}'></div>\n\n"
        markdown += f"# {cate} [[Back]](#toc)\n\n"
        
        # 为每篇论文添加错误处理
        papers_in_category = []
        for item in data:
            if item["categories"][0] == cate:
                try:
                    formatted_paper = template.format(
                        title=item["title"],
                        authors=",".join(item["authors"]) if isinstance(item["authors"], list) else str(item["authors"]),
                        summary=item["summary"],
                        url=item['abs'],
                        tldr=item['AI']['tldr'],
                        motivation=item['AI']['motivation'],
                        method=item['AI']['method'],
                        result=item['AI']['result'],
                        conclusion=item['AI']['conclusion'],
                        cate=item['categories'][0],
                        idx=next(idx)
                    )
                    papers_in_category.append(formatted_paper)
                except Exception as e:
                    print(f"格式化论文时出错，跳过: {e}", file=sys.stderr)
                    continue
        
        markdown += "\n\n".join(papers_in_category)
    
    # 写入输出文件，添加错误处理
    try:
        output_filename = args.data.split('_')[0] + '.md'
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(markdown)
        print(f"成功生成 Markdown 文件: {output_filename}", file=sys.stderr)
    except Exception as e:
        print(f"写入输出文件时出错: {e}", file=sys.stderr)
        exit(1)
