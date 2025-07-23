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
    """去重Pipeline，支持跨天去重检查（最近15天），从AI增强文件中加载已有论文ID"""
    
    def __init__(self):
        self.seen_ids = set()
        self.data_dir = "../../data"  # 相对于daily_arxiv/daily_arxiv目录的数据目录路径
        self.days_to_check = 15  # 只检查最近15天的数据
        self.logger = None  # 将在open_spider中初始化
        # 获取环境变量中的today值，如果不存在则使用当前日期
        self.today_str = os.environ.get('TODAY', None)
    
    def open_spider(self, spider):
        """爬虫启动时初始化"""
        self.logger = spider.logger
        self.load_recent_ids()
    
    def get_recent_date_files(self):
        """获取最近15天的AI增强数据文件路径"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(current_dir, self.data_dir)
        
        if not os.path.exists(data_path):
            if self.logger:
                self.logger.warning(f"数据目录不存在: {data_path}")
            return []
        
        # 生成最近15天的日期列表
        if self.today_str:
            try:
                # 尝试解析环境变量中的日期
                today = datetime.strptime(self.today_str, "%Y-%m-%d")
            except ValueError:
                # 如果解析失败，使用当前日期并记录警告
                if self.logger:
                    self.logger.warning(f"无法解析环境变量TODAY的值: {self.today_str}，将使用当前日期")
                today = datetime.now()
        else:
            today = datetime.now()
            
        recent_dates = []
        for i in range(self.days_to_check):
            date = today - timedelta(days=i)
            recent_dates.append(date.strftime("%Y-%m-%d"))
        
        # 查找对应日期的AI增强文件，支持多种语言
        recent_files = []
        for date_str in recent_dates:
            # 查找所有可能的AI增强文件模式
            ai_enhanced_patterns = [
                f"{date_str}_AI_enhanced_Chinese.jsonl",
                f"{date_str}_AI_enhanced_English.jsonl", 
                f"{date_str}_AI_enhanced_*.jsonl"
            ]
            
            for pattern in ai_enhanced_patterns:
                if '*' in pattern:
                    # 使用glob匹配通配符模式
                    file_pattern = os.path.join(data_path, pattern)
                    matching_files = glob.glob(file_pattern)
                    recent_files.extend(matching_files)
                else:
                    # 直接检查文件是否存在
                    file_path = os.path.join(data_path, pattern)
                    if os.path.exists(file_path):
                        recent_files.append(file_path)
        
        # 去重（因为可能有重复的文件路径）
        recent_files = list(set(recent_files))
        
        return recent_files
    
    def load_recent_ids(self):
        """加载最近15天AI增强数据中的所有论文ID"""
        try:
            recent_files = self.get_recent_date_files()
            
            if not recent_files:
                if self.logger:
                    self.logger.info("未找到最近15天的AI增强历史数据文件，将进行首次运行去重检查")
                return
            
            if self.logger:
                self.logger.info(f"找到 {len(recent_files)} 个最近15天的AI增强数据文件")
                for file_path in recent_files:
                    self.logger.debug(f"加载文件: {os.path.basename(file_path)}")
            
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
                self.logger.info(f"已从AI增强文件中加载 {len(self.seen_ids)} 个论文ID用于去重检查")
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"加载最近15天AI增强数据ID时出错: {e}")
    
    def process_item(self, item, spider):
        """检查论文ID是否重复"""
        paper_id = item.get('id')
        
        if not paper_id:
            raise DropItem("论文缺少ID字段")
        
        if paper_id in self.seen_ids:
            # 在去重阶段，title可能还未设置，所以显示paper_id作为标识
            title = item.get('title', f'Paper {paper_id}')
            spider.logger.info(f"发现重复论文: {paper_id} ({title})")
            raise DropItem(f"重复论文ID: {paper_id}")
        
        # 添加到已见集合中
        self.seen_ids.add(paper_id)
        spider.logger.debug(f"论文ID {paper_id} 通过去重检查")
        return item


class DailyArxivPipeline:
    def __init__(self):
        self.page_size = 100
        # arxiv库在请求之间默认有3秒的延迟，以遵守API使用礼仪。
        # 日志中的 "INFO: Sleeping: ..." 就来源于此。
        # 我们可以覆盖这个设置。
        self.client = arxiv.Client(
            page_size=self.page_size,
            delay_seconds=1.2,
            num_retries=3
        )

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
