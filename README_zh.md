# FloodEvacPlanner
- [English README](README_en.md)
- [中文 README](README_zh.md)

## 项目简介
FloodEvacPlanner是一个学术研究项目，旨在为洪灾情境下的疏散规划提供优化解决方案。
该项目支持将 GIS 导出的 SHP 文件作为输入，更加适合非计算机专业同学的需求。
系统集成了多种路径规划算法，并结合洪灾场景数据提供高效的疏散方案。
同时，项目还包含绘图和分析功能，帮助用户可视化疏散路线及其他关键数据，进一步评估疏散方案的效果与安全性。

## 使用方法

1. 获得代码
```bash
git clone https://github.com/missingstuffedbun/FloodEvacPlanner.git
cd FloodEvacPlanner
```
2. 安装依赖
```bash
pip install -r requirements.txt
```
3. 运行程序
```bash
python main.py -c config.yaml
```
可以通过修改配置文件`config.yaml`修改需要执行的任务和输入数据。

## 支持一下
如果你觉得这个项目对你有帮助，欢迎扫码支持，也可以顺便留下微信号交流合作 🚀  
![微信赞赏码](wechat.jpg)