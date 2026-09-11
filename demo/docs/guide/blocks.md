# 区块总览

十六种区块。下表列出每种区块**独有**的属性，通用属性见[语法速查](syntax.md#_2)。

| 区块 | 用途 |
| --- | --- |
| [`hero`](#hero) | 首屏：大标题、说明、按钮、配图、要点 |
| [`cards`](#cards) | 卡片墙，带 3D 倾斜与高光 |
| [`showcase`](#showcase) | 图文交替的叙事行，一左一右地向下延伸 |
| [`features`](#features) | 无边框的特性网格 |
| [`testimonials`](#testimonials) | 引用 / 评价，可带头像与星级 |
| [`logos`](#logos) | 品牌墙、"使用方" 走马灯 |
| [`image`](#image) | 单张图片：图注、浏览框、浮动环绕 |
| [`gallery`](#gallery) | 可滚动 / 分页的图片带 |
| [`split`](#split) | 多栏图文 |
| [`text`](#text) | 正文段落，可加浅底面板 |
| [`stats`](#stats) | 数字，滚动到可见时计数 |
| [`steps`](#steps) | 步骤 / 时间线 |
| [`links`](#links) | 链接列表、胶囊、按钮 |
| [`cta`](#cta) | 收尾的行动号召，可带装饰底纹 |
| [`anim`](#anim) | 动画容器：漂浮、呼吸、走马灯、逐字 |
| [`divider`](#divider) | 分隔线 |
| `homepage-<类型>`（别名） | `card` `grid` `sections` `rows` `spotlight` `quotes` `reviews` `brands` `clients` `columns` `carousel` `prose` `numbers` `timeline` `quicklinks` `banner` `cta` `hr` `animate` …… |

## hero

| 属性 | 说明 |
| --- | --- |
| `eyebrow` / `title` / `subtitle` | 眉标、标题（`h1`）、副标题 |
| `image` | 配图；配上 `ratio`（默认 `16/10`）与 `alt`、`caption` |
| `mirror` | 配图放到左侧 |
| `actions` | 按钮列表：`text` / `link` / `style`（`primary` 或 `secondary`）/ `icon` |
| `highlights` | 标题下方的一排要点：`value` / `label` / `icon` |
| `note` | 按钮下方的小字 |
| 正文 | 作为导语段落，排在按钮之前 |

默认带 `aurora` 底纹与 `shadow` 配图；`pattern: none` 与 `shadow: false` 关掉。

```homepage-hero
eyebrow: 示例
title: 一个首屏区块
subtitle: 标题默认是一级标题，正文作为导语。
actions:
  - 主按钮 | / | primary
  - 次按钮 | /guide/
highlights:
  - 0 | 运行时依赖 | package-variant-closed
  - 16 | 区块类型 | view-dashboard-outline
note: 装完即用，不需要额外的主题补丁。
```

## cards

| 属性 | 说明 |
| --- | --- |
| `cards` | 卡片列表，见下 |
| `card_style` | `elevated`（默认）`outlined` `filled` `glass` `plain` |
| `link_text` | 页脚文案的默认值 |

单张卡片：`title` / `desc` / `icon` / `link` / `link_text` / `badge` / `tags` /
`meta` / `theme` / `image` + `ratio` / `span: 2` / `featured` / `class` / `external`。

```homepage-cards
columns: 3
card_style: elevated
cards:
  - title: 普通卡片
    icon: file-document-outline
    desc: 图标、标题、描述、页脚
    link: /guide/
  - title: 带标签
    icon: bookmark-outline
    desc: 标签适合放分类
    tags: [标签一, 标签二]
    theme: cyan
  - title: 宽卡片
    icon: view-dashboard-outline
    desc: "span: 2 或 featured: true 让它占两列"
    span: 2
    theme: amber
```

## showcase

图文交替的叙事行。每行一个主张配一张图，左右交替，视线自然地向下走。
块上的 `reverse` 会把整个序列翻转（第一行的图换到左边），`alternate: false`
则让每行都保持"文左图右"。

| 属性 | 说明 |
| --- | --- |
| `showcase` | 行列表，见下 |
| `alternate` | 默认 `true`，逐行左右交替 |
| `reverse` | 翻转整个序列 |
| `link_text` | 「了解更多」的默认文案 |
| `ratio` | 配图宽高比，默认 `16/10` |

单行：`title` / `eyebrow` / `desc` / `image` + `ratio` / `link` + `link_text` /
`features`（要点列表，`icon` 默认 `check-circle-outline`）/ `reverse` / `theme` /
`frame` / `shadow` / `glow` / `zoom`。

```homepage-showcase
showcase:
  - eyebrow: 第一步
    title: 用 Markdown 写首页
    desc: 语法就是页面本身，改文案不需要看 HTML。
    image: ../assets/shot-1.svg
    link: syntax.md
    features:
      - 一个围栏代码块就是一块内容
      - 属性是标准 YAML
  - title: 风格由主题决定
    desc: 颜色从一个色相推导，浅色与深色都不需要单独调。
    image: ../assets/shot-2.svg
    theme: cyan
```

## features

`features` 列表 + `icon_style`（`plain` `soft` `circle` `square` `solid`）。
条目字段：`title` / `desc` / `icon` / `link` / `theme`。

```homepage-features
columns: 3
icon_style: circle
features:
  - title: 圆形
    icon: compass-outline
    desc: "icon_style: circle"
  - title: 圆角方形
    icon: shape-outline
    desc: "icon_style: soft"
  - title: 实心
    icon: lightning-bolt-outline
    desc: "icon_style: solid"
    theme: cyan
```

## testimonials

| 属性 | 说明 |
| --- | --- |
| `testimonials` | 条目列表，见下 |
| `style` | `cards`（默认）/ `quote`（无边框、只剩引号）/ `plain` |
| `rating` | 显示五颗星 |

条目字段：`quote` / `name` / `role` / `avatar` + `link` / `theme`。
`quote` 用站点自己的扩展渲染，可以带列表、代码、链接。

```homepage-testimonials
columns: 3
rating: true
testimonials:
  - quote: 首页第一次做到"不用改主题就能排版"。
    name: 一位用户
    role: 文档维护者
    avatar: ../assets/avatar-1.svg
    theme: indigo
  - quote: |
      属性是 YAML，所以可以随意嵌套：

      - 列表
      - 引用
    name: 另一位用户
    role: 前端工程师
    avatar: ../assets/avatar-2.svg
    theme: cyan
```

## logos

"使用方" 品牌墙。品牌标来自内置的 **Simple Icons** 集合，用
`simple/<名字>` 指定；MDI 里几乎没有品牌标，所以这一块默认查的是另一套图标。

| 属性 | 说明 |
| --- | --- |
| `logos` | 条目列表，见下 |
| `style` | `row`（默认）/ `grid` / `marquee`（无缝走马灯） |
| `colored` | 保留品牌原色（默认跟随主题文字色） |
| `size` | 图标尺寸 |
| `caption` | 品牌墙上方的说明文字 |

条目字段：`icon`（`simple/github` 或 `material/github`）/ `name` / `link` / `desc`。
自有 logo 用**映射**写 `image:`：

```homepage-logos
caption: 用它构建的文档
style: marquee
logos:
  - simple/github | GitHub | https://github.com
  - simple/python | Python | https://python.org
  - simple/docker | Docker | https://docker.com
  - image: ../assets/shot-1.svg
    name: 自己的 Logo
    link: https://example.com
```

## image

| 属性 | 说明 |
| --- | --- |
| `src` / `alt` / `caption` / `link` | 图片与图注 |
| `ratio` | 强制宽高比，例如 `16/9` |
| `zoom` | 默认点击放大（`lightbox: false` 关闭全站） |
| `float` | `left` / `right`，让后续正文环绕 |
| `float_width` | 浮动宽度，默认 `42%` |
| `frame` | `browser` / `window` / `screenshot` 浏览器框 |
| `shadow` / `glow` | 阴影 / 光晕 |
| 正文 | 追加在图注下方 |

```homepage-image
src: ../../assets/shot-1.svg
frame: browser
caption: "frame: browser 会画一圈窗口外框"
```

## gallery

| 属性 | 说明 |
| --- | --- |
| `images` | 图片列表；省略时用**正文里的 Markdown 图片**，`title` 作为图注 |
| `mode` | `scroll`（默认，一次一张）/ `paged`（一次一屏）/ `grid` |
| `per_view` | 一屏放几张，可以是小数（例如 `1.3` 露出一角） |
| `ratio` | 默认 `16/9` |

```homepage-gallery
mode: paged
per_view: 2
---
![一](../../assets/shot-1.svg "第一张")

![二](../../assets/shot-2.svg "第二张")

![三](../../assets/shot-3.svg "第三张")
```

## split

正文用单独一行的 `===` 切成多栏（两栏以上都可以）。`panes` 可以按顺序给每一栏
单独设置 `theme` / `class` / `title`。

| 属性 | 说明 |
| --- | --- |
| `ratio` | 栏宽比例，`1.2 1` 即 `1.2fr 1fr`；也可以用 `minmax(0, 1fr) auto` |
| `gap` | 栏间距 |
| `divider` | 栏之间画一条竖线 |
| `reverse` | 视觉上左右互换（DOM 顺序不变，读屏顺序仍然正确） |
| `sticky` | 第一栏在滚动时吸顶 |

```homepage-split
ratio: 1 1
divider: true
panes:
  - theme: indigo
    title: 左栏
  - theme: cyan
    title: 右栏
---
左边的内容。

===
右边的内容。
```

## text

| 属性 | 说明 |
| --- | --- |
| `panel` / `callout` | 加浅底与左侧强调线 |
| `lead` | 首段放大 |
| `columns` | 用 CSS 多栏排版 |
| `icon` | 左侧图标 |
| `collapsible` + `summary` | 折叠成 `<details>` |

```homepage-text
panel: true
icon: information-outline
---
浅底面板适合放一段"注意事项"，它不会像卡片那样抢视觉重心。
```

## stats

`stats` 列表：`value` / `label` / `icon` / `theme`；`animate: false` 关闭计数。
`value` 里的前缀与后缀会自动分离，例如 `98.6%` 只对 `98.6` 做动画。

```homepage-stats
columns: 4
stats:
  - 16 | 区块类型 | view-dashboard-outline
  - 95 | 内置图标 | shape-outline
  - "99.9% | 可用性 | check-circle-outline"
  - "< 1s | 构建增量 | speedometer"
```

## steps

`steps` 列表：`title` / `desc` / `icon` / `link` / `theme`；
`direction`（`vertical` / `horizontal`）、`numbered`。

```homepage-steps
direction: horizontal
steps:
  - 安装 | index.md | download-outline
  - 编写 | syntax.md | text-box-outline
  - 预览 | ../reference/index.md | console
```

## links

`links` 列表：`text` / `link` / `desc` / `icon` / `theme`；
`style`：`list`（默认）`chips` `buttons` `cards`。

```homepage-links
style: buttons
columns: 3
links:
  - 指南 | index.md | book-open-page-variant-outline
  - 语法 | syntax.md | text-box-outline
  - 设计 | ../reference/index.md | palette-outline
```

## cta

收尾的行动号召：居中、可带装饰底纹，视觉上比正文重、比首屏轻。

| 属性 | 说明 |
| --- | --- |
| `eyebrow` / `title` / `subtitle` | 标题层级默认是 `h2` |
| `actions` | 按钮列表，同 `hero` |
| `note` | 按钮下方的小字 |
| `image` + `ratio` | 右侧配图，默认 `1/1` |
| `pattern` | `aurora`（默认）/ `grid` / `dots` / `rays` / `none` |
| `gradient` | 标题用渐变文字 |

```homepage-cta
gradient: true
pattern: rays
title: 现在就可以写第一块内容
actions:
  - 开始使用 | index.md | primary
  - 看全部区块 | blocks.md
note: 不需要任何主题覆盖文件。
```

## anim

`effect`：`float` `pulse` `shimmer` `gradient` `marquee` `typetext`；
`duration` / `delay` 控制节奏。走马灯会复制一份内容来实现无缝滚动，逐字动画在
鼠标移入时立刻显示完整文本。

```homepage-anim
effect: typetext
---
用 Markdown 写首页，写法本身就是文档的一部分。
```

## divider

`style`：`line` `space` `dots` `wave` `gradient`；`size` 用于 `space`；
`text` / `label` 会在线的中间放一个标签。

```homepage-divider
style: dots
```
