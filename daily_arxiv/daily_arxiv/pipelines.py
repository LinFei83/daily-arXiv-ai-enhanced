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
        self.data_dir = "../../data"  # 相对于daily_arxiv/daily_arxiv目录的数据目录路径
        self.days_to_check = 15  # 只检查最近15天的数据
        self.logger = None  # 将在open_spider中初始化
    
    def open_spider(self, spider):
        """爬虫启动时初始化"""
        self.logger = spider.logger
        self.load_recent_ids()
    
    def get_recent_date_files(self):
        """获取最近15天的数据文件路径"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 尝试多个可能的数据目录路径
        possible_paths = [
            os.path.join(current_dir, self.data_dir),  # ../../data
            os.path.join(current_dir, "../data"),      # ../data
            os.path.join(current_dir, "../../data"),   # ../../data (明确指定)
        ]
        
        # 查找项目根目录下的data文件夹
        project_root = current_dir
        while project_root != os.path.dirname(project_root):  # 直到根目录
            potential_data_path = os.path.join(project_root, "data")
            if os.path.exists(potential_data_path):
                possible_paths.append(potential_data_path)
                break
            project_root = os.path.dirname(project_root)
        
        data_path = None
        for path in possible_paths:
            if os.path.exists(path):
                data_path = path
                break
        
        if not data_path:
            if self.logger:
                self.logger.warning(f"数据目录不存在，已尝试路径: {possible_paths}")
            return []
        
        if self.logger:
            self.logger.debug(f"使用数据目录: {data_path}")
        
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
                if self.logger:
                    self.logger.info("未找到最近15天的历史数据文件，将进行首次运行去重检查")
                return
            
            if self.logger:
                self.logger.info(f"找到 {len(recent_files)} 个最近15天的数据文件")
            
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
                                    if self.logger:
                                        self.logger.warning(f"JSON解析错误 {os.path.basename(file_path)}:{line_num}: {e}")
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"读取文件错误 {os.path.basename(file_path)}: {e}")
            
            if self.logger:
                self.logger.info(f"已加载 {len(self.seen_ids)} 个论文ID用于去重检查")
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"加载最近15天ID时出错: {e}")
    
    def process_item(self, item, spider):
        """检查论文ID是否重复"""
        paper_id = item.get('id')
        
        if not paper_id:
            raise DropItem("论文缺少ID字段")
        
        if paper_id in self.seen_ids:
            title = item.get('title', 'N/A')
            spider.logger.info(f"重复论文ID: {paper_id} (标题: {title})")
            raise DropItem(f"重复论文ID: {paper_id}")
        
        # 添加到已见集合中
        self.seen_ids.add(paper_id)
        spider.logger.debug(f"论文ID {paper_id} 通过去重检查")
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
