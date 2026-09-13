# mkdocs-homepage-plugin

用纯 Markdown 编排 [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) 的首页：
首屏、卡片墙、图文交替、评价、品牌墙、画册、数字、步骤、行动号召、动画。所有定制都写在
Markdown 文件里，样式全部长在主题上——不改模板、不写 HTML、不引入前端框架。

```yaml
plugins:
  - homepage
```

````markdown
```homepage-hero
title: 让文档的第一屏，值得多看一眼
subtitle: 用纯 Markdown 编排首页区块
image: assets/hero.svg
actions:
  - 快速开始 | guide/index.md | primary | rocket-launch-outline
```

```homepage-cards
columns: 3
cards:
  - title: 指南
    icon: book-open-page-variant-outline
    desc: 从安装到第一个卡片墙，**五分钟**搞定。
    link: guide/index.md
    badge: 入门
  - title: 语法
    icon: text-box-outline
    desc: 属性块、正文块与分隔线
    link: guide/syntax.md
    theme: cyan
```
````

## 它想解决什么

MkDocs 的首页通常只有两种结局：一屏苍白的正文，或者一堆没人维护的 HTML。这个插件
给出第三条路——**一个围栏代码块就是一块内容**，顺序就是文档顺序，位置、主题、栅格列数
都写在区块自己的属性里，长文本照样用 Markdown 写。

- **不脱离主题。** 颜色要么取 Material 的语义变量，要么由一个色相推导；亮暗两套配色、
  自定义 `primary`/`accent`、高对比度设置都不需要额外处理。
- **不抢视觉重心。** 字号小、留白足、描边细；卡片悬停时轻轻改变视角并有一道跟随光标的
  高光，按下时**边缘发光**（键盘聚焦时同一种光）。间距只有六个档位，
  面板内边距一定大于面板间距，每两个区块之间的距离一定相等。
- **不静默失败。** 写错会输出带行号的警告，并在页面上留下一个写明原因的虚线框；
  `strict: true` 时直接让构建失败，适合放进 CI。
- **关掉 JS 也完整。** 脚本只做倾斜、滚动揭示、画册翻页、数字累加、点击放大这五件事，
  每一件都是渐进增强。

## 安装

```bash
pip install mkdocs-homepage-plugin
```

```yaml
plugins:
  - homepage
```

插件会自己把 Markdown 扩展注册进去，并把样式表和脚本挂到站点上，**不需要**再往
`markdown_extensions` 里加任何东西。

想单独使用 Markdown 扩展（不装插件、或者换别的主题）：

```yaml
markdown_extensions:
  - mkdocs_homepage.extension:HomepageExtension
```

## 语法

````text
```homepage-<类型>          ← 信息字符串：决定这是哪种区块
<属性>                       ← 可选，一段 YAML 映射
---                          ← 可选分隔线：单独一行、顶格
<正文>                       ← 可选，用站点自己的扩展渲染的 Markdown
```
````

只有两条分割规则：

1. **正文里出现单独一行的 `---`，它上面全是属性，下面全是正文。** 正文里要水平线就用 `***`。
2. 没有分隔线时，整段要么是属性要么是正文：第一段里每一行都是 `键: 值`（及其缩进的续行）
   就当属性，否则整段都是正文。

列表项支持竖线简写：`标题 | 链接 | 描述 | 图标`。

```yaml
cards:
  - 指南 | guide/index.md | 从零开始搭建站点 | rocket-launch-outline
```

> 竖线简写只对**整项是一个字符串**时生效。写成 `- text: 甲 | 乙` 时 `text` 就是字面量，
> 因为 YAML 已经把它读成了一个映射。

## 区块

| 区块 | 用途 | 主要属性 |
| --- | --- | --- |
| [`hero`](demo/docs/guide/blocks/hero.md) | 首屏 | `eyebrow` `title` `subtitle` `image` `actions` `highlights` `mirror` |
| [`cards`](demo/docs/guide/blocks/cards.md) | 卡片墙（3D 倾斜 + 高光），支持一卡一栏与单卡配色 | `cards` `card_style` `columns` `min_cols` `layout` |
| [`showcase`](demo/docs/guide/blocks/showcase.md) | 图文交替的叙事行 | `showcase` `alternate` `reverse` `link_text` |
| [`features`](demo/docs/guide/blocks/features.md) | 无边框特性网格 | `features` `icon_style` `columns` |
| [`testimonials`](demo/docs/guide/blocks/testimonials.md) | 引用 / 评价 | `testimonials` `style` `rating` |
| [`logos`](demo/docs/guide/blocks/logos.md) | 品牌墙 / 走马灯 | `logos` `style` `colored` `size` `caption` |
| [`image`](demo/docs/guide/blocks/image.md) | 单张图片 | `src` `caption` `ratio` `float` `frame` `shadow` |
| [`gallery`](demo/docs/guide/blocks/gallery.md) | 可滚动 / 分页画册 | `images` `mode` `per_view` `ratio` |
| [`split`](demo/docs/guide/blocks/split.md) | 多栏图文（正文用 `===` 分栏） | `ratio` `divider` `reverse` `sticky` `panes` |
| [`text`](demo/docs/guide/blocks/text.md) | 正文段落 | `panel` `lead` `columns` `icon` `collapsible` |
| [`stats`](demo/docs/guide/blocks/stats.md) | 数字，滚动到可见时计数 | `stats` `animate` `columns` |
| [`steps`](demo/docs/guide/blocks/steps.md) | 步骤 / 时间线 | `steps` `direction` `numbered` |
| [`links`](demo/docs/guide/blocks/links.md) | 链接列表、胶囊、按钮 | `links` `style` `columns` |
| [`cta`](demo/docs/guide/blocks/cta.md) | 收尾的行动号召 | `eyebrow` `title` `actions` `note` `image` `pattern` |
| [`anim`](demo/docs/guide/blocks/anim.md) | 动画容器 | `effect` `duration` `delay` |
| [`divider`](demo/docs/guide/blocks/divider.md) | 分隔线 | `style` `size` `text` |


别名可用：`card` `grid` `sections` `rows` `spotlight` `quotes` `reviews` `brands` `clients`
`columns` `cols` `img` `figure` `carousel` `slider` `prose` `banner` `numbers` `timeline`
`quicklinks` `hr` `animate`……

每种区块都认识这些通用属性：

| 属性 | 取值 |
| --- | --- |
| `theme` | `indigo` `blue` `cyan` `teal` `green` `lime` `amber` `orange` `deep-orange` `pink` `purple` `deep-purple` `blue-grey` `slate` |
| `class` | 追加自定义类名 |
| `id` / `anchor` | 页面内锚点 |
| `width` | `content`（限制阅读宽度并居中）/ `wide` |
| `align` | `start` `center` `end` `justify` |
| `reveal` | `up` `down` `left` `right` `zoom` `fade` / `false` |
| `tilt` | 卡片倾斜强度（默认 `6`）/ `false` |
| `background` | `tint` `surface` `accent` |
| `pattern` | `aurora` `grid` `dots` `rays` / `none`（`hero` 与 `cta` 默认 `aurora`） |
| `gradient` | 标题使用渐变文字 |
| `gap` | 栅格间距 |
| `columns` | 列数；**尺寸按这个列数算**，放不下时才自动减列 |
| `min_cols` | 没写 `columns` 时单个栅格项的最小宽度，默认 `13em` |
| `ratio` | 该区块图片的默认宽高比（比例写斜杠：`16/10`） |

完整属性表见[区块总览](demo/docs/guide/blocks/index.md)（一个区块一页）；
「想做这样一个页面」看[场景配方](demo/docs/guide/recipes.md)。

### 空位与列数

所有可重复的列表都允许留空，`-`、`- {}`、`- empty`、`- blank` 等价。
空位占住自己的位置，**列数不变**：4 列里只放 3 张卡，卡片宽度仍然是四列的宽度，
不会因为少一张而把三张撑宽。

### 比例写斜杠

`ratio: 4/3` 或 `ratio: "4:3"`。YAML 会把不带引号的 `4:3` 读成六十进制数 243，
而 243 是合法的 CSS 比例——插件会认出这个区间、报警并回退到默认值。

## 微调

只改变量即可，不必重写选择器（它们都声明在 `:root`，所以 `css_vars` 注入真的生效）：

```yaml
plugins:
  - homepage:
      css_vars:
        --md-home-radius: 0.9em
        --md-home-gap: 1.1em
```

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `--md-home-hue` | `231` | 默认色相（indigo） |
| `--md-home-radius` | `0.6em` | 面板圆角 |
| `--md-home-radius-sm` | `0.35em` | 小圆角：图标底、图片 |
| `--md-home-gap` | `0.9em` | 栅格间距 |
| `--md-home-pad` | `1.2em` | 面板内边距 |
| `--md-home-min` | `13em` | 栅格项最小宽度（未指定列数时） |
| `--md-home-min-narrow` | `8.5em` | 指定了 `columns` 时的硬底线 |

间距是一条六档阶梯（`--md-home-space-1` … `-6`，`0.4em` → `2.5em`），
细节见 [设计约定](demo/docs/reference/index.md)。

## 卡片

单张卡片除了通用的 `title` / `desc` / `icon` / `link` / `tags` / `theme` / `image`，
还可以控制自己的外形和颜色：

```yaml
cards:
  - title: 一张 4:3 的卡片
    icon: shape-outline
    ratio: 4/3                 # 整张卡的比例（封面图的单独用 image_ratio）
  - title: 一卡一栏
    body: |                    # layout: rows 时，右栏是这段 Markdown
      右边是**正文**。
    reverse: true              # 左右对调
  - title: 自己的颜色
    bg: '#eef1ff'              # 两套模式都用它
    bg_dark: '#161a2b'         # 只在深色模式覆盖
    glow: '#4f6bed'            # 描边、光晕、强调色
    glow_dark: '#8fa4ff'
```

| 属性 | 说明 |
| --- | --- |
| `ratio` | 整张卡的宽高比；内部内容过高时卡片内部滚动 |
| `image_ratio` / `cover_ratio` | 封面图的比例（覆盖块上的 `ratio`） |
| `layout: rows` | 卡片在左、说明文字在右；没写 `body` 的行右栏留空，保持对齐 |
| `row_ratio` | `layout: rows` 时两边的宽度：`18em`（卡片固定，右边占剩下的）或 `2 3`（两条轨道） |
| `body` / `aside` | `layout: rows` 时的右栏，用站点自己的 Markdown 渲染 |
| `reverse` | 单行左右对调 |
| `bg` / `bg_dark` | 底色（`surface` 是别名；浅色与深色分开写） |
| `glow` / `glow_dark` | 光照（`accent` / `color` 是别名） |

## 图标

图标是构建时从主题源码里拷出的 SVG 路径，内联成单条 `currentColor` 路径——没有图标
字体，也没有额外请求，颜色跟随主题（含深色方案）：

```yaml
icon: book-open-page-variant-outline   # Material Design Icons（默认，约 58 个）
icon: simple/github                    # Simple Icons 品牌标（约 30 个，logos 区块默认）
```

**每个图标位都能改用图片**，共用一个键，靠扩展名区分：

```yaml
icon: ../assets/logo.svg               # 圆形，保留原色
```

字形由主题着色，图片保留自己的颜色并裁成圆形（所以请用正方形图片）；气泡位置（卡片
图标 / 特性图标 / 步骤序号）会让出浅底与描边，把图片放大到填满整格。

写错名字会输出警告并列出可用取值。`scripts/generate_icons.py` 负责重新生成，
`tests/test_icons.py` 会逐 token 对比主题源码，防止拷错。

## 品牌墙

```yaml
style: marquee      # row / grid / marquee，后者是无缝走马灯
colored: true       # 图标标记改用强调色（图片不受影响）
logos:
  - simple/github | GitHub | https://github.com   # 图标标记：跟随主题调色
  - image: assets/logo.svg                        # 图片：裁成圆形，永远是自己的颜色
    name: Acme
```

图片会裁成圆形，所以**请用正方形图片**（非正方形会居中裁切）。`colored` 只管我们自己
着色的图标标记；作者提供的品牌图有自己的配色，这个开关不会去动它。
走马灯是无缝的：两份内容、平移半个轨道，间隙算在周期内，轨道至少两倍视口宽。

## 插件选项

```yaml
plugins:
  - homepage:
      assets: true                 # 是否挂载样式表与脚本
      assets_dir: assets           # 它们在站点里的目录
      tilt: true                   # 卡片倾斜
      tilt_strength: 6             # 倾斜强度（度）
      reveal: auto                 # auto 只让列表类区块错峰出现；也可给固定值或 off
      lightbox: true               # 点击图片放大
      count: true                  # 数字滚动累加
      markdown_extension: true     # 自动注册 Markdown 扩展
      strict: false                # 区块写错时直接让构建失败
      css_vars:                    # 注入到 :root 的自定义属性
        --md-home-radius: 0.9em
```

## 设计约定

- **颜色从不写死。** 每个 `theme` 只声明一个 `--md-home-hue`，强调色、浅底、描边与高光
  都由它推导。浅底是「强调色混进主题自己的背景色」，所以任何一个色相在两种配色方案下
  都有稳定的对比度。
- **重新声明主题的字号。** 区块落在 `.md-typeset` 里，Material 的元素选择器会命中它。
  `[dir="ltr"] .md-typeset ul` 的缩进、`rem` 定长的标题、24px 的 `.md-icon svg` 都在
  `.md-home` 内部被重设，靠**选择器权重**取胜，而不是靠样式表加载顺序。
- **正文区不受重置影响。** 渲染 Markdown 的容器带 `.md-home__prose`，把列表符号、段落
  间距和标题层级交还给文章本身的节奏。
- **栅格没有断点。** 写了 `columns: N`，尺寸就按 N 算：`repeat(auto-fill, …)` 保留没有
  元素落进去的轨道，所以 4 列里只放 3 张卡时卡片仍然是四列的宽度，空位用 `- blank`
  明说。只有窄到放不下时（一列最小 `8.5em`）才减少列。
- **作者写的颜色是唯一例外。** 单张卡片可以用 `bg` / `bg_dark` / `glow` / `glow_dark`
  直接指定颜色，不跟主题走（两套模式的变量都会发出去，由样式表按方案选一个）。
- **渲染安全。** 进入属性的值一律转义；进入 `style` 的值经过白名单校验；`href`/`src`
  拒绝 `javascript:`、`data:` 之类的协议。

## 开发

```bash
pip install -e ".[dev]"
python -m pytest
python -m mkdocs serve -f demo/mkdocs.yml
python scripts/generate_icons.py --write    # 从已安装的主题重新生成 icons.py
```

`demo/` 是一个功能演示站点，同时也是集成测试的输入。

## 许可

MIT
