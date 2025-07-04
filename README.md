# 关于

本项目基于 [dw-dengwei/daily-arXiv-ai-enhanced](https://github.com/dw-dengwei/daily-arXiv-ai-enhanced) 项目进行修改

这个工具会每天爬取 https://arxiv.org 并使用大语言模型对论文进行总结。

在线体验：https://linfei83.github.io/daily-arXiv-ai-enhanced/

# 功能特性

- 使用GitHub Actions和GitHub Pages的免费功能，**无需服务器**
- 每天凌晨开始爬取数据，并使用DeepSeek进行总结。这个时段是DeepSeek的非高峰折扣期，每天仅需约0.2元人民币。
- 提供GitHub Pages前端界面，使用LocalStorage存储**个性化偏好**信息（如感兴趣的关键词和作者），并高亮显示匹配偏好的论文。
- GitHub Pages兼顾了电脑和移动设备的显示效果，确保可以在移动设备上轻松查看论文

# 截图展示
- 主页面。高亮显示感兴趣的关键词和作者。

![image-20250704093851668](https://image.linfei.ink:8888/i/2025/07/04/fis5hv-0.png)

- 设置页面。设置关键词和作者并存储在您的浏览器中。

![image-20250704093915031](https://image.linfei.ink:8888/i/2025/07/04/fj5ifo-0.png)

- 详情页面。显示您点击的论文的详细信息。

![image-20250704094003431](https://image.linfei.ink:8888/i/2025/07/04/fjodh8-0.png)

- 日期选择。支持选择单个日期或日期范围来筛选论文（**注意：较大的日期范围会显示大量论文，可能导致浏览器卡顿。**）。  

![image-20250704094031464](https://image.linfei.ink:8888/i/2025/07/04/fjuhp8-0.png)


- 统计页面（*开发中*）。帮助您分析论文。为您选择的日期提取论文关键词。此外，如果您选择日期范围，将显示关键词趋势图。（幸运的是，选择大范围的论文**不会**导致浏览器卡顿，因为此页面不会显示所有论文。处理关键词可能需要几秒钟。）

<img src="images/keyword.png" alt="single-date" width="600">
<img src="images/trends.png" alt="range-date" width="600">


# 使用方法
此仓库将每天爬取关于**cs.CV、cs.GR、cs.CL和cs.AI**的arXiv论文，并使用**DeepSeek**以**中文**总结论文。
如果您希望爬取其他arXiv类别、使用其他大语言模型或其他语言，请按照说明操作。
否则，您可以直接使用 https://linfei83.github.io/daily-arXiv-ai-enhanced/。如果您喜欢请给个星标 :)

**操作步骤：**
1. 将此仓库Fork到您自己的账户
2. 进入：您的仓库 -> Settings -> Secrets and variables -> Actions
3. 进入Secrets。Secrets是加密的，用于敏感数据
4. 创建两个名为`OPENAI_API_KEY`和`OPENAI_BASE_URL`的仓库密钥，并输入相应的值。
5. 进入Variables。Variables以明文显示，用于非敏感数据
6. 创建以下仓库变量：
   1. `CATEGORIES`：用","分隔类别，如"cs.CL, cs.CV"
   2. `LANGUAGE`：如"Chinese"或"English"
   3. `MODEL_NAME`：如"deepseek-chat"
   4. `EMAIL`：您的邮箱，用于推送到GitHub
   5. `NAME`：您的姓名，用于推送到GitHub
7. 进入您的仓库 -> Actions -> arXiv-daily-ai-enhanced
8. 您可以手动点击**Run workflow**来测试是否正常工作（可能需要约一小时）。默认情况下，此操作将每天自动运行。您可以在`.github/workflows/run.yml`中修改。
9. 设置GitHub Pages：进入您的仓库 -> Settings -> Pages。在`Build and deployment`中，设置`Source="Deploy from a branch"`，`Branch="main", "/(root)"`。等待几分钟，访问 https://\<username\>.github.io/daily-arXiv-ai-enhanced/。请查看此[issue](https://github.com/dw-dengwei/daily-arXiv-ai-enhanced/issues/14)获取更详细的说明。

# CATEGORIES配置说明

CATEGORIES环境变量支持所有arXiv官方分类。以下是主要的分类选项：

## 计算机科学 (Computer Science)
**常用的计算机科学分类：**
- `cs.AI` - 人工智能 (Artificial Intelligence)
- `cs.CV` - 计算机视觉和模式识别 (Computer Vision and Pattern Recognition)
- `cs.CL` - 计算和语言/自然语言处理 (Computation and Language)
- `cs.LG` - 机器学习 (Machine Learning)
- `cs.RO` - 机器人学 (Robotics)
- `cs.CR` - 密码学和安全 (Cryptography and Security)
- `cs.DB` - 数据库 (Databases)
- `cs.DC` - 分布式、并行和集群计算 (Distributed, Parallel, and Cluster Computing)
- `cs.DS` - 数据结构和算法 (Data Structures and Algorithms)
- `cs.GR` - 图形学 (Graphics)
- `cs.HC` - 人机交互 (Human-Computer Interaction)
- `cs.IR` - 信息检索 (Information Retrieval)
- `cs.IT` - 信息理论 (Information Theory)
- `cs.NI` - 网络和互联网架构 (Networking and Internet Architecture)
- `cs.SE` - 软件工程 (Software Engineering)
- `cs.SI` - 社交和信息网络 (Social and Information Networks)

## 物理学 (Physics)
- `physics.optics` - 光学
- `physics.app-ph` - 应用物理
- `physics.comp-ph` - 计算物理
- `astro-ph.CO` - 宇宙学和非银河天体物理
- `cond-mat.mes-hall` - 介观和纳米尺度物理
- `quant-ph` - 量子物理

## 数学 (Mathematics)
- `math.NA` - 数值分析
- `math.OC` - 优化和控制
- `math.ST` - 统计理论
- `math.PR` - 概率论

## 其他领域
- `eess.IV` - 图像和视频处理 (Image and Video Processing)
- `eess.SP` - 信号处理 (Signal Processing)
- `stat.ML` - 统计机器学习 (Machine Learning)
- `q-bio.QM` - 定量生物学方法 (Quantitative Methods)

## 配置格式

CATEGORIES环境变量使用**逗号分隔**的格式配置多个分类：

```bash
# 单个分类
CATEGORIES="cs.CV"

# 多个分类（推荐格式）
CATEGORIES="cs.CV, cs.CL, cs.AI, cs.LG"

# 项目默认配置
CATEGORIES="cs.CV, cs.GR, cs.CL, cs.AI"
```

完整的arXiv分类列表请参考：https://arxiv.org/category_taxonomy

# 待办事项

- [x] 功能：用GitHub Pages前端替换markdown。
- [ ] 修复：在统计页面中，关键词的论文数量不正确。
- [ ] 修复：在日期选择器中，日期和星期不对应。
- [ ] 功能：使用DeepSeek提取关键词。
- [x] 更新Fork用户关于如何使用GitHub Pages的说明。
- [x] 去除重复论文
- [ ] 修复日期范围无法选择无数据日期bug
# 贡献者

感谢以下特别贡献者对此项目的贡献！！！
<table>
  <tbody>
    <tr>
      <td align="center" valign="top">
        <a href="https://github.com/JianGuanTHU"><img src="https://avatars.githubusercontent.com/u/44895708?v=4" width="100px;" alt="JianGuanTHU"/><br /><sub><b>JianGuanTHU</b></sub></a><br />
      </td>
      <td align="center" valign="top">
        <a href="https://github.com/Chi-hong22"><img src="https://avatars.githubusercontent.com/u/75403952?v=4" width="100px;" alt="Chi-hong22"/><br /><sub><b>Chi-hong22</b></sub></a><br />
      </td>
    </tr>
  </tbody>
</table>

# 致谢
我们真诚感谢以下个人和组织的推广和支持！！！
<table>
  <tbody>
    <tr>
      <td align="center" valign="top">
        <a href="https://x.com/GitHub_Daily/status/1930610556731318781"><img src="https://pbs.twimg.com/profile_images/1660876795347111937/EIo6fIr4_400x400.jpg" width="100px;" alt="Github_Daily"/><br /><sub><b>Github_Daily</b></sub></a><br />
      </td>
      <td align="center" valign="top">
        <a href="https://x.com/aigclink/status/1930897858963853746"><img src="https://pbs.twimg.com/profile_images/1729450995850027008/gllXr6bh_400x400.jpg" width="100px;" alt="AIGCLINK"/><br /><sub><b>AIGCLINK</b></sub></a><br />
      </td>
      <td align="center" valign="top">
        <a href="https://www.ruanyifeng.com/blog/2025/06/weekly-issue-353.html"><img src="https://avatars.githubusercontent.com/u/905434" width="100px;" alt="阮一峰的网络日志"/><br /><sub><b>阮一峰的网络日志 <br> 科技爱好者周刊（第 353 期）</b></sub></a><br />
      </td>
      <td align="center" valign="top">
        <a href="https://hellogithub.com/periodical/volume/111"><img src="https://github.com/user-attachments/assets/eff6b6dd-0323-40c4-9db6-444a51bbc80a" width="100px;" alt="《HelloGitHub》第 111 期"/><br /><sub><b>《HelloGitHub》月刊 <br> 第 111 期</b></sub></a><br />
      </td>
    </tr>
  </tbody>
</table>


# 星标历史

[![Star History Chart](https://api.star-history.com/svg?repos=linfei83/daily-arXiv-ai-enhanced&type=Date)](https://www.star-history.com/#linfei83/daily-arXiv-ai-enhanced&Date)
