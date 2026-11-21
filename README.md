# video-cutter

![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)

基于FFmpeg的本地无损视频裁剪工具。在浏览器中边看边标记要删除的片段，导出时按关键帧无损剪切并拼接，画质零损失。所有处理均在本机完成，不上传任何视频到云端。

## 1 项目简介

这是一款面向本地使用的视频裁剪小工具，由Python标准库提供的HTTP服务与一个单页Web界面组成。用户打开网页加载本地视频，在时间轴上标记需要删除的片段，工具随即调用FFmpeg按关键帧完成无损剪切与拼接，并把结果保存到项目目录。

之所以强调"无损"，是因为整个裁剪过程使用流复制而非重新编码，切点会就近吸附到关键帧，因而可能存在几秒误差，但画面质量完全不损失，处理速度也很快。工具不依赖任何第三方Python库，唯一的外部依赖是FFmpeg。

## 2 功能特性

工具围绕"标记—预览—导出"这条主线设计，并补充了若干提升体验的细节。

1. **无损裁剪**：基于FFmpeg的`-c copy`流复制，按关键帧切点剪切并拼接，画质零损失。
2. **可视化标记**：在网页中播放视频，按`I`标记删除起点、按`O`标记终点，支持多段标记与手动微调。
3. **实时日志**：导出过程通过SSE把FFmpeg输出实时推送到页面，便于观察每一步进展。
4. **自动保存**：标记结果按文件名与大小缓存在浏览器本地，重新打开同一视频可自动恢复。
5. **音轨校验**：导出后比对源文件与结果的音轨情况，一旦发现音轨缺失即在页面提示。
6. **零第三方依赖**：后端仅使用Python标准库，配置集中于`config.toml`，便于修改和扩展。

这些特性共同保证了工具轻量、可控且易于二次开发。

## 3 快速开始

### 3.1 环境要求

运行前需准备Python3.11及以上版本（代码使用标准库`tomllib`）与FFmpeg可执行程序，并将FFmpeg加入系统PATH。

### 3.2 安装FFmpeg

从FFmpeg官网下载对应平台的构建包，解压后把`bin`目录加入系统PATH，在命令行执行下面的命令确认安装成功。

```bash
ffmpeg -version
ffprobe -version
```

若能正常输出版本号即可。若FFmpeg不在PATH中，也可在`config.toml`里把`ffmpeg_bin`与`ffprobe_bin`改为可执行文件的绝对路径。

### 3.3 启动服务

克隆仓库后进入项目目录，Windows用户可直接双击`start.bat`，或在命令行执行下面的命令。

```bash
python main.py
```

服务默认监听8765端口，启动后会自动打开浏览器；若未自动打开，可手动访问`http://127.0.0.1:8765`。关闭服务在终端按`Ctrl+C`即可。

## 4 使用方法

打开页面后，把视频拖入虚线区域或点击按钮选择文件，视频随即加载到播放器中。边播放边按`I`标记删除片段的起点，到达片段末尾时按`O`标记终点，时间轴上会以红色斜纹显示待删除区间，下方列表可逐段微调起止时间或移除。

标记完成后点击"执行无损裁剪"，页面会实时打印FFmpeg日志并在成功后给出结果文件名与大小。输出文件保存在项目根目录，文件名为"原文件名加`_cut`后缀"，例如`video.mp4`处理为`video_cut.mp4`。

整个过程仅在你本机进行，源视频与中间分段文件都存放在`backup`目录，不会向外发送。

## 5 配置说明

所有可调参数集中在`config.toml`，代码中不硬编码，修改后重启服务即可生效。常用项如下。

| 配置项 | 说明 | 默认值 |
| --- | --- | --- |
| `server.host` | 监听地址 | `0.0.0.0` |
| `server.port` | 服务端口 | `8765` |
| `server.open_browser` | 启动后是否自动打开浏览器 | `true` |
| `ffmpeg.ffmpeg_bin` | FFmpeg路径 | `ffmpeg` |
| `ffmpeg.ffprobe_bin` | FFprobe路径 | `ffprobe` |
| `ffmpeg.log_encoding` | FFmpeg输出解码编码，中文路径乱码时改为`gbk` | `utf-8` |
| `paths.backup_dir` | 源文件与分段等中间产物目录 | `backup` |
| `paths.output_suffix` | 输出文件名后缀 | `_cut` |
| `cut.min_keep_sec` | 过短的保留段直接丢弃，避免空段导致音轨丢失 | `0.5` |

需要局域网内其他设备访问时，把`server.print_host`改为本机局域网IP即可。

## 6 项目结构

项目文件精简，核心逻辑集中在几个Python文件中。

```
video-cutter/
├── main.py          # HTTP服务与接口路由
├── cutter.py        # FFmpeg探测、区间计算与裁剪拼接
├── settings.py      # 配置加载
├── config.toml      # 运行配置
├── web/index.html   # 前端单页界面
├── start.bat        # Windows启动脚本
└── requirements.txt # 依赖说明
```

前端负责交互与标记，后端负责计算区间并驱动FFmpeg，二者通过上传与SSE接口通信。

## 7 许可证

本项目基于Apache License 2.0开源，可自由使用、修改与商用，详见[LICENSE](LICENSE)文件。
