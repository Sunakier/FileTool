# 文件同步工具

## 简介

一个基于Python开发的文件同步工具，这是鄙人的参赛作品，它或许只是默默无闻而不会被积极维护，非我哪天有新的想法和需求推动我去做，下面是它为数不多的特点罢

- **完全开源**：我的存在是因为大家的存在，它是完全自由开放的！
- **轻量极简**：以轻量和极简为目标，简单的功能极低的占用奠定它的平凡的存在与伟大的使命
- **易于使用**：通过Token标识同步组分别同步，让简单和易用助力效率。
- **灵活部署**：部署简单，提供多平台 pyless 可执行文件(come soon future....)，支持私网和公网部署，易于在各种环境快速部署。
- **高效协同**：文件快速分发自动同步，一人有，大家有，人人为我，我为人人！

这是一个学习性质的作品，我用我不多的业余时间设计了它，它并非那么完美，它的出现注定它只是芸芸众生中的小透明罢了，你的喜欢是我最大的支持

---

## 部署

***前言：请先观看下面的常见问题FAQ，提问时需要遵循《提问的智慧》，不要提出一些令大家反感的问题***

本程序分为客户端和服务端，服务端与客户端应该部署在具有良好网络连接的并且运行有现代操作系统的设备上

很不幸，考虑到此工具的特殊性，我无法提供示例公共服务端，一切需要您自己部署

---

## 使用说明

本程序客户端拥有 WebUI 作为控制台界面, 您亦可以使用控制台进行操作  

计划有两种同步模式, 目前已完整实现一种: **主从分离模式**  

即一台设备订阅的同一个的 Token (暂不允许反复订阅同一Token) 只能为 a/b 模式中的一种  
a (Only-A 强制覆盖云端) / b (Only-B 强制云端同步本地)

---

## 常见问题

1. Q: 在Windwos7下无法使用使用 遇到了无法找到支持库/无法加载支持库/环境损坏等提示    
   A: Windows7 已经于 2020 正式停止安全更新, 它已经过时, 我们将不会考虑费时费力的去支持一个本应该已经踏进棺材的操作系统

---

## 服务端实现的API列表

### 端点合集

- GET /apix/ping 获取服务器状态 应返回 Pong  
- POST /apix/file/create 创建文件上传请求 需传入数组 支持批量   
  参数 belike (JSON) :  
  [{"file_size":1000,"file_md5":"a18e79e691721bc2bb02ed5ba1ca04bf"}]
- And so on in code ...

### 响应代码合集 (这里其实非常乱 这边可以画个饼未来重构 虽然这样不好)

- 404 : 端点错误
- 500 : 服务器内部错误
- 200 : 请求成功
- 998 : 尝试创建文件上传任务 服务器已匹配到此文件跳过上传
- 399 : 参数有误
- 400 : 不允许创建空文件
- 349 : 尝试上传文件实际分片 但是此没有对应的上传任务
- 341 : 尝试上传文件实际分片 文件长度校验错误
- 342 : 尝试上传文件实际分片 文件HASH校验错误
- 533 : 尝试上传文件实际分片 服务器遇到错误 无法保持分片文件
- 990 : 尝试上传文件实际分片 所有分片完成上传
- 200 : 尝试上传文件实际分片 当前分片完成上传
- And so on in code ...