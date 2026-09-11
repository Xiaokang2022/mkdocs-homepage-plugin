# 快速开始

## 安装

```bash
pip install mkdocs-homepage-plugin
```

## 启用

在 `mkdocs.yml` 里加上插件名即可。**不需要**再往 `markdown_extensions` 里加任何东西：
插件会自己把 Markdown 扩展注册进去，并把样式表和脚本挂到站点上。

```yaml
plugins:
  - homepage
```

## 写下第一个区块

在任意 Markdown 页面里写一个信息字符串以 `homepage` 开头的围栏代码块：

````markdown
```homepage-hero
eyebrow: 我的文档
title: 欢迎
subtitle: 一句话说明这里是做什么的
---
正文用 **Markdown** 写，和页面正文一样的扩展、一样的样式。
```
````

保存，`mkdocs serve`，就能看到了。

## 一个首页长什么样

首页就是一串区块，顺序由它们在 `.md` 里的先后决定：

````markdown
```homepage-hero
title: 项目名
image: assets/hero.svg
actions:
  - 快速开始 | index.md | primary
```

```homepage-cards
columns: 3
cards:
  - 指南 | index.md | 从零开始 | rocket-launch-outline
  - 语法 | syntax.md | 属性怎么填 | text-box-outline
  - 设计 | ../reference/index.md | 为什么好看 | palette-outline
```

```homepage-stats
columns: 3
stats:
  - 16 | 区块类型
  - 95 | 内置图标
  - 0 | 前端依赖
```
````

## 下一步

- [语法速查](syntax.md) —— 围栏、属性、正文的分工
- [全部区块](blocks.md) —— 每种区块支持的属性
- [设计约定](../reference/index.md) —— 它为什么看起来像 Material
