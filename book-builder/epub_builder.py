"""ePUB3 package builder — generates OPF, TOC, container.xml and packs .epub"""

from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring
import zipfile
import os
import mimetypes

# ── ePUB3 必须的文件布局 ──
META_INF = "META-INF"
OEBPS = "OEBPS"
XHTML_DIR = "xhtml"
CSS_DIR = "css"
IMAGE_DIR = "images"
CONTAINER_PATH = f"{META_INF}/container.xml"
CONTENT_OPF_PATH = f"{OEBPS}/content.opf"
TOC_PATH = f"{OEBPS}/toc.xhtml"
STYLE_CSS_PATH = f"{OEBPS}/{CSS_DIR}/style.css"

# ── 容器模板 ──
CONTAINER_XML = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

# ── CSS 模板：包含视差动效 ──
STYLE_CSS = """@charset "UTF-8";

html, body {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: #000;
}

/* 场景容器 */
.scene {
  position: relative;
  width: 100%;
  height: 100vh;
  perspective: 800px;
  overflow: hidden;
  background: #fff;
}

/* 通用图层 */
.layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
}

/* 背景层：视差效果 */
.layer-bg {
  /* 翻页时产生视差位移 */
}

/* 中景层 */
.layer-mid {
  /* 可选的中间层，静止 */
}

/* 前景层：浮动呼吸动画 */
.layer-fg {
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50%      { transform: translateY(-5px); }
}

/* 文字叠层 */
.text-overlay {
  position: absolute;
  bottom: 8%;
  left: 6%;
  right: 6%;
  padding: 18px 24px;
  background: rgba(0, 0, 0, 0.45);
  border-radius: 12px;
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}

.story-text {
  margin: 0;
  font-size: 1.2em;
  line-height: 1.6;
  color: #fff;
  text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
  animation: fadeInUp 0.8s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 封面专用 */
.cover-page {
  width: 100%;
  height: 100vh;
  background-size: cover;
  background-position: center;
}

/* 翻页视差：Apple Books 通过 @page 控制 */
@page {
  margin: 0;
  padding: 0;
}
"""
