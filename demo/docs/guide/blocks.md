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

单张卡片：`title` / `link` / `desc` / `icon` / `link_text` / `badge` / `tags` /
`meta` / `theme` / `image` + `ratio` / `span: 2` / `featured` / `class` / `external`。

卡片上的 `image:` 是**封面图**（见下），所以卡片的圆形成员标记用 `icon:` 写图片路径。

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
  - title: 图片标记
    icon: ../assets/mark-orbit.svg
    desc: "icon: 指向图片文件时裁成圆形，并保留原色"
    theme: teal
  - title: 图片标记
    icon: ../assets/mark-orbit.svg
    desc: 图标位置写图片路径就是圆形图片，原色保留
    link: /guide/
```

## 间距与空位

**任何可以重复的列表都允许留空。** 空位占位但什么都不画，列数按你写的算：

```yaml
cards:
  - 第一张
  - 第二张
  -             # 空
```

四种写法等价：`-`、`- {}`、`- empty`、`- blank`。需要一张**真的叫 empty**
的条目时，只要带上分隔符就还是条目：`- empty | /guide/`。

关键在**尺寸按 `columns` 算**：下面 4 列只有 3 张卡，卡片宽度就是四列的宽度，
不会因为少一张而变宽——第 4 个位置是空的，但第 4 列仍然算数：

```homepage-cards
columns: 4
cards:
  - title: 一
    icon: layers-outline
    desc: 4 列里的第 1 张
  - title: 二
    icon: view-gallery-outline
    desc: 4 列里的第 2 张
  - title: 三
    icon: shape-outline
    desc: 4 列里的第 3 张
  -
```

`columns` 仍然是响应式的：位置排不下时列数会自然减少（一列最小 8.5em），
但**只要放得下，就一定是你要的那个列数**——`columns: 4` 和 `columns: 3`
在宽屏上是两种不同的宽度。

## 卡片的宽高比

卡片自己的 `ratio` 控制**整张卡**的外形；封面图的 `image_ratio` 单独控制：

```yaml
cards:
  - title: 方卡
    ratio: 1/1            # 整张卡
    image: /cover.svg
    image_ratio: 16/9     # 封面图
```

写 `ratio` 的卡片不再被同行里最高的那张拉齐（否则行高会盖掉比例），
所以同一行里不同比例的卡片会各自按自己的比例显示、顶对齐。内容比框高时
卡片内部可以滚动，页脚不会被裁掉。

```homepage-cards
columns: 3
cards:
  - title: '4:3'
    ratio: 4/3
    icon: shape-outline
    desc: 整张卡是 4:3
  - title: '1:1'
    ratio: 1/1
    icon: view-gallery-outline
    desc: 方形卡片
  - title: '2:3'
    ratio: 2/3
    icon: image-outline
    desc: 竖长卡片
```

!!! warning "比例要写斜杠，不要写冒号"
    想写 `4:3` 的时候写 **`4/3`**。YAML 会把不带引号的 `4:3` 当成
    *六十进制数*（`4*60+3 = 243`），于是卡片会高到 243 倍宽；插件会识别
    这种值、在构建时报警并回退到默认比例。写成 `"4:3"`（带引号）也可以。

## 一卡一栏

`layout: rows` 把卡片摊成一行行：左边卡片，右边是它的说明文字（Markdown）。
没写 `body` 的行右侧留空，这样连续几行的卡片仍然对齐。

```homepage-cards
layout: rows
cards:
  - title: 左边卡片
    icon: file-document-outline
    desc: 卡片本体
    body: |
      ### 右边是正文

      可以写任意 Markdown：

      - 列表
      - **强调**
  - title: 这一行没有说明
    icon: text-box-outline
    desc: 右边留空，但卡片宽度不变
  - title: 这一段反过来
    icon: refresh
    desc: "reverse: true"
    reverse: true
    body: |
      图左文右，或者反过来。
```

## 单张卡片的配色

卡片可以**自己**指定底色和光色，不跟主题走：

| 键 | 说明 |
| --- | --- |
| `bg` | 底色，浅色与深色都用它 |
| `bg_dark` | 只在深色模式覆盖 `bg` |
| `glow` | 光照（描边、光晕、强调色），同 `bg` |
| `glow_dark` | 只在深色模式覆盖 `glow` |

别名：`surface` = `bg`，`accent` / `color` = `glow`。值是任意合法 CSS 颜色
（`#4f6bed`、`rgb(...)`、`oklch(...)`、`rebeccapurple`），写错会在构建时报警并忽略。

所以**只写 `bg`** 是两种模式都换成它，**只写 `bg_dark`** 才是"只有深色模式变，
浅色模式继续用主题推导的颜色"：

```homepage-cards
columns: 3
cards:
  - title: 只写 bg
    desc: 浅色与深色都换成这个底色
    bg: '#eef1ff'
    glow: '#4f6bed'
  - title: 只写 bg_dark
    desc: 只有深色模式变，浅色模式用主题推导
    bg_dark: '#161a2b'
    glow_dark: '#8fa4ff'
  - title: 两个都写
    desc: 切换明暗可以看到各用各的
    bg: '#eafaf1'
    bg_dark: '#122117'
    glow: '#12a150'
    glow_dark: '#4ade80'
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
  - title: 用图片
    icon: ../assets/mark-orbit.svg
    desc: "icon: 指向图片文件时，气泡让位，图片按圆形填满整格"
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
| `colored` | 图标标记是否用强调色（默认跟主题文字色），见下 |
| `size` | 图标 / 图片直径 |
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
  - image: ../assets/avatar-1.svg
    name: 自己的 Logo
    link: https://example.com
```

**图标标记与图片是两种东西，规则也不同：**

| | 图标标记（`icon: simple/github`） | 图片（`image: …`） |
| --- | --- | --- |
| 颜色 | 跟随主题文字色；`colored: true` 时用强调色 | **永远是图片自己的颜色** |
| 形状 | 原样 | 裁成**圆形** |
| `colored` | 生效 | **不生效** |
| 默认观感 | 半透明，鼠标移上去才变实 | 原样 |

图片会被裁成圆形，所以**请用正方形图片**：正方形原样呈现，非正方形会居中裁切
（16:9 的截图放进去会掉掉两边）。`colored` 是给**我们自己着色**的图标标记用的，
作者提供的品牌图有自己的配色，这个开关不会去动它。

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
columns: 3
stats:
  - 16 | 区块类型 | view-dashboard-outline
  - 95 | 内置图标 | shape-outline
  - "99.9% | 可用性 | check-circle-outline"
  - "< 1s | 构建增量 | speedometer"
  - 2 | 配色方案 | layers-outline
  - 3.4 | 评分 | ../assets/mark-orbit.svg
```

## steps

`steps` 列表：`title` / `link` / `desc` / `icon` / `theme`；
`direction`（`vertical` / `horizontal`）、`numbered`。

```homepage-steps
direction: horizontal
steps:
  - 安装 | index.md | 一条命令 | download-outline
  - 编写 | syntax.md | 围栏里写属性 | text-box-outline
  - 预览 | ../reference/index.md | 本地实时刷新 | console
```

## links

`links` 列表：`text` / `link` / `desc` / `icon` / `theme`；
`style`：`list`（默认）`chips` `buttons` `cards`。

```homepage-links
style: buttons
columns: 3
links:
  - 指南 | index.md | 从零开始 | book-open-page-variant-outline
  - 语法 | syntax.md | 属性与正文 | text-box-outline
  - 设计 | ../reference/index.md | 样式约定 | palette-outline
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

## 图标与图片

**每个画图标的位置都可以写图片路径。** 两者用的是**同一个键** `icon:`，靠扩展名区分：

```yaml
icon: rocket-launch-outline      # 图标名 -> 单色字形，由主题着色
icon: ../assets/logo.svg         # 图片路径 -> 圆形图片，保留原色
```

同样的写法适用于所有图标位：`hero` 的按钮与要点、`cards`、`features`、`stats`、`steps`、
`links`、`showcase` 的要点列表、`text`，以及 `logos`（那里另有历史更久的 `image:` 键）。

| | 图标名 | 图片路径 |
| --- | --- | --- |
| 外形 | 原样 | 裁成**圆形** |
| 颜色 | 由主题着色（强调色 / 文字色） | **图片自己的颜色** |
| 大小 | 该位置为图标留的尺寸 | 气泡类位置**填满整个气泡**，其余同上 |
| 气泡 | 保留浅底与描边 | 气泡让位（正方形底衬套在圆形图片后面看着像一圈） |
| 无障碍 | 有配套文字时视为装饰 | 有 `alt:` 时用它，否则为空 |

几条要知道的：

- **用正方形图片。** 正方形原样呈现，其它比例会居中裁切——16:9 的截图放进去会掉两边。
- **气泡位置会把图片放大到整个气泡**（卡片图标 2.25em、特性图标 2.4em、步骤序号 2em），
  比字形大一圈：一个徽标要看清需要比一条线段更多的空间，而布局属于那个位置，所以其它
  东西不会挪动。
- **扩展名是唯一的判据**，所以图标名里不能有点——内置的两套图标（95 个）都不含点，
  测试会钉住这一点。
- 图片路径同样由插件按 MkDocs 的规则解析（`../assets/x.svg` 相对**当前页面**），
  写错会被构建测试抓出来，而不是在线上变成一张裂图。
