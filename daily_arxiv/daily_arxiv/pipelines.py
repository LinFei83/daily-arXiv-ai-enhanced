# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import arxiv
import json
import os
import glob
from scrapy.exceptions import DropItem
from datetime import datetime, timedelta


class DuplicatesPipeline:
    """去重Pipeline，支持跨天去重检查（最近15天）"""
    
    def __init__(self):
        self.seen_ids = set()
        self.data_dir = "../data"  # 相对于daily_arxiv目录的数据目录路径
        self.days_to_check = 15  # 只检查最近15天的数据
        self.load_recent_ids()
    
    def get_recent_date_files(self):
        """获取最近15天的数据文件路径"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(current_dir, self.data_dir)
        
        if not os.path.exists(data_path):
            print(f"数据目录不存在: {data_path}")
            return []
        
        # 生成最近15天的日期列表
        today = datetime.now()
        recent_dates = []
        for i in range(self.days_to_check):
            date = today - timedelta(days=i)
            recent_dates.append(date.strftime("%Y-%m-%d"))
        
        # 查找对应日期的.jsonl文件
        recent_files = []
        for date_str in recent_dates:
            file_pattern = os.path.join(data_path, f"{date_str}.jsonl")
            if os.path.exists(file_pattern):
                recent_files.append(file_pattern)
        
        return recent_files
    
    def load_recent_ids(self):
        """加载最近15天数据中的所有论文ID"""
        try:
            recent_files = self.get_recent_date_files()
            
            if not recent_files:
                print("未找到最近15天的历史数据文件")
                return
            
            print(f"找到 {len(recent_files)} 个最近15天的数据文件")
            
            for file_path in recent_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line_num, line in enumerate(f, 1):
                            line = line.strip()
                            if line:
                                try:
                                    data = json.loads(line)
                                    if 'id' in data:
                                        self.seen_ids.add(data['id'])
                                except json.JSONDecodeError as e:
                                    print(f"JSON解析错误 {os.path.basename(file_path)}:{line_num}: {e}")
                except Exception as e:
                    print(f"读取文件错误 {os.path.basename(file_path)}: {e}")
            
            print(f"已加载最近15天内 {len(self.seen_ids)} 个论文ID用于去重检查")
            
        except Exception as e:
            print(f"加载最近15天ID时出错: {e}")
    
    def process_item(self, item, spider):
        """检查论文ID是否重复"""
        paper_id = item.get('id')
        
        if not paper_id:
            raise DropItem("论文缺少ID字段")
        
        if paper_id in self.seen_ids:
            raise DropItem(f"重复论文ID: {paper_id} (标题: {item.get('title', 'N/A')})")
        
        # 添加到已见集合中
        self.seen_ids.add(paper_id)
        return item


class DailyArxivPipeline:
    def __init__(self):
        self.page_size = 100
        self.client = arxiv.Client(self.page_size)

    def process_item(self, item: dict, spider):
        item["pdf"] = f"https://arxiv.org/pdf/{item['id']}"
        item["abs"] = f"https://arxiv.org/abs/{item['id']}"
        search = arxiv.Search(
            id_list=[item["id"]],
        )
        paper = next(self.client.results(search))
        item["authors"] = [a.name for a in paper.authors]
        item["title"] = paper.title
        item["categories"] = paper.categories
        item["comment"] = paper.comment
        item["summary"] = paper.summary
        print(item)
        return item
