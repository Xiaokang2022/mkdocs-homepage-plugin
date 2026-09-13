# 图标与图片

## 每个画图标的位置都可以写图片

两者用的是**同一个键** `icon:`，靠扩展名区分：

```yaml
icon: rocket-launch-outline      # 图标名 -> 单色字形，由主题着色
icon: assets/logo.svg            # 图片路径 -> 圆形图片，保留原色
```

| | 图标名 | 图片路径 |
| --- | --- | --- |
| 外形 | 原样 | 裁成**圆形** |
| 颜色 | 由主题着色（强调色 / 文字色） | **图片自己的颜色** |
| 大小 | 该位置为图标留的尺寸 | 气泡类位置**填满整个气泡**，其余同上 |
| 气泡 | 保留浅底与描边 | 气泡让位（正方形底衬套在圆形图片后面看着像一圈） |
| 无障碍 | 有配套文字时视为装饰 | 有 `alt:` 时用它，否则为空 |

```homepage-cards
columns: 4
title: 同一个键，两种东西
cards:
  - title: 图标名
    icon: rocket-launch-outline
    desc: 单色字形，跟随主题
  - title: 图片
    icon: ../assets/mark-orbit.svg
    desc: 圆形，保留原色
  - title: 气泡里的图片
    icon: ../assets/mark-orbit.svg
    desc: 会填满整个气泡
    theme: teal
  - title: 换个色相
    icon: palette-outline
    desc: 字形跟着主题变色
    theme: amber
```

同一套规则适用于**所有图标位**：

| 区块 | 位置 |
| --- | --- |
| `hero` | `actions[].icon`、`highlights[].icon` |
| `cards` | `cards[].icon` |
| `features` | `features[].icon` |
| `stats` | `stats[].icon` |
| `steps` | `steps[].icon` |
| `links` | `links[].icon` |
| `showcase` | `features[].icon`（要点列表） |
| `text` | `icon` |
| `logos` | `logos[].icon`，另外还有历史更久的 `image:`（两者都行） |

```homepage-steps
title: 步骤的标记也能是图片
steps:
  - 图标名 | | 单色字形 | download-outline
  - 图片 | | 圆形 | ../assets/mark-orbit.svg
  - 没有 | | 回退到序号 3
```

## 内置图标

图标是构建时从**已安装主题的源码**里拷出来的 SVG 路径，内联成一条
`currentColor` 路径——没有图标字体、没有额外请求，颜色跟随主题（含深色方案）。

一共 **95** 个，分两套：

| 集合 | 数量 | 说明 |
| --- | --- | --- |
| Material Design Icons | 66 | 通用图标，写名字即可，如 `rocket-launch-outline` |
| Simple Icons | 29 | 品牌标，写 `simple/` 前缀，如 `simple/github` |

```homepage-features
columns: 4
icon_style: soft
title: 一些常用的
features:
  - title: rocket-launch-outline
    icon: rocket-launch-outline
    desc: 开始 / 发布
  - title: palette-outline
    icon: palette-outline
    desc: 设计 / 外观
  - title: layers-outline
    icon: layers-outline
    desc: 区块 / 结构
  - title: shield-check-outline
    icon: shield-check-outline
    desc: 安全 / 可靠性
  - title: speedometer
    icon: speedometer
    desc: 性能
  - title: timeline-outline
    icon: timeline-outline
    desc: 流程 / 历史
  - title: simple/python
    icon: simple/python
    desc: 品牌标
  - title: simple/docker
    icon: simple/docker
    desc: 品牌标
```

!!! tip "写错会列出来"
    图标名写错不会被静默忽略：构建时输出警告并**列出所有可用取值**，
    页面上那个位置会留一个虚线小方块（不是空白，也不是裂图）。

### 为什么图标名里不能有点

**扩展名是区分图标和图片的唯一判据**，所以图标名里不能出现 `.`。
内置的两套图标（95 个）都不含点，测试会钉住这一点——
哪天有人加进来一个带点的图标名，那条测试会先失败。

### 自定义图标

内置集合是刻意小的：它能覆盖「通用界面 + 常见品牌」，但不打算覆盖所有场合。

- **要品牌标** → 用 `simple/` 集合，或者直接写图片路径。
- **要自己的图形** → 直接写图片路径（SVG 最好，因为是矢量、能用 `currentColor`）。
- **要一整套自己的图标** → 覆盖 `mkdocs_homepage/icons.py` 里的路径表，
  或者给图标位写图片路径。

## 用图片时注意什么

| 注意 | 原因 |
| --- | --- |
| **用正方形图片** | 图标位是圆的，非正方形会居中裁切。16:9 的截图放进去会掉两边 |
| **想跟随主题就存成 SVG 并用 `currentColor`** | 位图颜色写死了；`currentColor` 的 SVG 会跟着主题变色，和内置图标完全一致 |
| **路径相对当前页面写** | 和 Markdown 里写图片一样。`../assets/logo.svg` 是相对于**这个 `.md` 文件** |
| **气泡位置会把图片放大** | 卡片图标 2.25em、特性图标 2.4em、步骤序号 2em。比字形大一圈是故意的：一个徽标要看清需要比一条线段更多的空间 |

图片路径由插件按 MkDocs 的规则解析，**写错会被构建测试抓出来**，
而不是在线上变成一张裂图。

## 品牌墙里的颜色

`logos` 区块的 `colored` 开关只管**我们自己着色的图标标记**。
作者提供的品牌图有自己的颜色，这个开关不会去动它——
把一张彩色 logo 变成单色是件很意外的事。

```homepage-logos
colored: true
caption: colored true
logos:
  - simple/github | GitHub
  - simple/python | Python
  - ../assets/mark-orbit.svg | 图片不受影响
```

```homepage-logos
colored: false
caption: colored false（默认）
logos:
  - simple/github | GitHub
  - simple/python | Python
  - ../assets/mark-orbit.svg | 图片同样不受影响
```
