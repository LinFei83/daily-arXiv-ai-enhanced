# today=`date -u "+%Y-%m-%d"`
today="2025-07-06"
cd daily_arxiv
# 检查文件是否已存在且行数大于20行
if [ -f "../data/${today}.jsonl" ]; then
    line_count=$(wc -l < "../data/${today}.jsonl")
    if [ "$line_count" -gt 20 ]; then
        echo "文件 ../data/${today}.jsonl 已存在，共 $line_count 行 (>20)，跳过爬虫程序..."
    else
        echo "文件 ../data/${today}.jsonl 已存在但仅有 $line_count 行 (<=20)，重新运行爬虫..."
        scrapy crawl arxiv -o ../data/${today}.jsonl
    fi
else
    echo "文件 ../data/${today}.jsonl 不存在，开始运行爬虫..."
    scrapy crawl arxiv -o ../data/${today}.jsonl
fi

cd ../ai
python enhance.py --data ../data/${today}.jsonl

cd ../to_md
python convert.py --data ../data/${today}_AI_enhanced_${LANGUAGE}.jsonl

cd ..
# python update_readme.py

ls data/*.jsonl | sed 's|data/||' > assets/file-list.txt
