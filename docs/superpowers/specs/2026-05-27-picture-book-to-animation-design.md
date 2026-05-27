# 儿童电子绘本 → 视差动效电子书 — 设计规格

## 背景

将图文混合的儿童电子绘本（~20页/本）制作成具有**视差动效**的**增强型电子书**，在手机和 iPad 上以 Apple Books 打开观看。

## 推荐方案：ePUB3 + CSS 视差动画

利用 ePUB3（HTML+CSS+JS+图片 的 ZIP 包）在 Apple Books 中通过 CSS 3D 变换实现画面分层视差动效。成本最低，一次制作手机/iPad 通用。

## 整体流程

```
原始页面 → AI 分层(rembg) → 背景补全(inpainting) → 编排 HTML+CSS → 打包 ePUB3
```

## 1. AI 分层标准

每张原始页面拆为最多 3 层：

| 层级 | 内容 | 处理方式 | 输出格式 |
|------|------|----------|----------|
| 背景层 | 天空/远景 | rembg 抠掉前景后，AI inpainting 补全 | `.jpg` |
| 中景层 | 树木/建筑（可选） | 二次 rembg 或手动 | `.png`（透明） |
| 前景层 | 人物/动物 | rembg 分离主体 | `.png`（透明） |

### 工具选择

- **rembg**：免费开源 Python 工具，~2-3 秒/图（有 GPU 更快）
- **Inpainting**：
  - 免费：Stable Diffusion WebUI 本地运行 + ControlNet
  - 付费（~$0.05-0.10/次）：Clipdrop Cleanup API

### 图片基准分辨率

2048×1536（iPad 标准），自动适配手机屏幕。

## 2. ePUB3 包结构

```
book/
├── OEBPS/
│   ├── content.opf          ← 元数据
│   ├── toc.xhtml            ← 目录
│   ├── css/style.css        ← 视差 + 浮动动画样式
│   ├── xhtml/
│   │   ├── cover.xhtml      ← 封面
│   │   ├── page_001.xhtml   ← 第 1 跨页
│   │   └── ...              ← 每页一个 xhtml
│   └── images/
│       ├── fg_001.png       ← 前景（透明PNG）
│       ├── mid_001.png      ← 中景（可选，透明PNG）
│       ├── bg_001.jpg       ← 补全后背景
│       └── ...
└── META-INF/
    └── container.xml
```

### 2.1 content.opf 关键元数据

```xml
<meta property="rendition:layout">pre-paginated</meta>
<meta property="rendition:orientation">auto</meta>
<meta property="rendition:spread">auto</meta>
```

`pre-paginated` 确保 Apple Books 不重新排版，保持原始画面比例。

### 2.2 每页 HTML 模板

```html
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta charset="utf-8"/>
  <link rel="stylesheet" href="../css/style.css"/>
</head>
<body>
  <div class="scene">
    <div class="layer bg" style="background-image: url(../images/bg_001.jpg)"></div>
    <div class="layer mid" style="background-image: url(../images/mid_001.png)"></div>
    <div class="layer fg" style="background-image: url(../images/fg_001.png)"></div>
    <div class="text-overlay">
      <p class="story-text">曾经，有一片森林...</p>
    </div>
  </div>
</body>
</html>
```

## 3. 页面动效定义

| 动画 | CSS 实现 | 参数 | 效果 |
|------|---------|------|------|
| 背景视差 | `transform: translateX()` | 翻页缓动 10-15px | 深远感 |
| 前景浮动 | `@keyframes float` | 3s 循环 Y±4px | 呼吸感 |
| 文字渐显 | `@keyframes fadeInUp` | 0.8s ease-out | 逐段展示 |
| 翻页过渡 | `@page` 属性 | iPad 原生翻页 | 书本感 |

### 3.1 核心 CSS

```css
.scene {
  perspective: 800px;
  overflow: hidden;
}
.layer {
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 100%;
  background-size: cover;
  background-position: center;
}
.bg-layer {
  transform: translateZ(-1px) scale(1.5);
}
.fg-layer {
  animation: float 3s ease-in-out infinite;
}
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50%      { transform: translateY(-4px); }
}
.story-text {
  animation: fadeInUp 0.8s ease-out;
}
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}
```

## 4. 打包工具

- **手动**：Sigil（GUI 操作）
- **自动化**：Python 脚本（输入 JSON 描述 → 自动生成文件结构 → zip 打包）

### 4.1 Python 脚本设计

```python
# 输入：JSON 描述文件
{
  "metadata": { "title": "森林的故事", "author": "..." },
  "pages": [
    {
      "bg": "bg_001.jpg",
      "mid": "mid_001.png",    # 可选
      "fg": "fg_001.png",
      "text": "曾经，有一片森林..."
    }
  ]
}
# 输出：完整的 .epub 文件
```

## 5. 验证方式

1. 用 Apple Books (macOS/iOS) 打开 `.epub` 文件
2. 检查翻页流畅度、视差动效是否生效、文字显示是否完整
3. 在 iPhone 上检查小屏适配效果

## 6. 后续可迭代方向

- 陀螺仪倾斜视差（DeviceOrientation API）
- TTS 自动朗读（ePUB3 Media Overlays）
- 轻交互（点击人物有反馈）
