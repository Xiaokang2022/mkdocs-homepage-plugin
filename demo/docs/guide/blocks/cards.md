# cards

一排卡片。每张卡可以只有标题，也可以有图标、描述、标签、页脚、封面图、整卡比例、
自己的颜色；整块可以排成网格，也可以排成「左卡片右说明」的一栏一卡。

```homepage-cards
columns: 3
cards:
  - title: 最小卡片
    desc: 只有标题和描述
  - title: 带图标
    icon: rocket-launch-outline
    desc: icon 决定卡片头上的那个标记
    link: index.md
  - title: 带标签
    icon: bookmark-outline
    desc: 标签适合放分类或状态
    tags: [标签一, 标签二]
    theme: cyan
```

## 块级属性

| 属性 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `cards` | 列表 | 必填 | 卡片列表。别名 `items` |
| `card_style` | 关键词 | `elevated` | 卡片外观。别名 `style` |
| `layout` | 关键词 | `grid` | `grid` 网格 / `rows` 一卡一栏。别名 `card_layout` |
| `row_ratio` | 轨道 | 对半 | `layout: rows` 时两边的宽度，见下。别名 `pane_ratio` `aside_ratio` |
| `link_text` | 文本 | `查看` | 卡片页脚文案的默认值 |
| `ratio` | 比例 | `16/9` | **封面的**默认比例（单张卡可覆盖） |
| `image_ratio` | 比例 | — | 同上，优先于 `ratio` |
| `columns` | 整数 | 自动 | 列数；尺寸按这个列数算 |
| `min_cols` | 长度 | `13em` | 没写 `columns` 时单个卡片的最小宽度 |

### `card_style`

| 取值 | 外观 |
| --- | --- |
| `elevated` | 浅底 + 投影（默认） |
| `outlined` | 透明底 + 一根描边 |
| `filled` | 实心浅底，没有描边 |
| `glass` | 半透明 + 模糊 |
| `plain` | 什么都没有，只有排版 |

```homepage-cards
columns: 3
card_style: outlined
title: '外观：outlined'
subtitle: 同一个列表，换一种外观。
cards:
  - title: outlined
    icon: shape-outline
    desc: 透明底 + 描边
  - title: 也可以写 style
    icon: shape-outline
    desc: style 是 card_style 的别名
  - title: 卡片上的 theme
    icon: palette-outline
    desc: 单张卡可以换色相
    theme: teal
```

## 单张卡片的字段

| 字段 | 说明 |
| --- | --- |
| `title` | 标题。别名 `heading` |
| `desc` | 描述，支持行内 Markdown。别名 `description` `text` |
| `link` | 整张卡变成链接。别名 `url` `href` |
| `link_text` | 页脚文案，默认取块上的 `link_text`，再默认 `查看` |
| `icon` | **图标名或图片路径**，见[图标与图片](../../reference/icons.md) |
| `image` | **封面图**（卡片上方整块）。别名 `img` `cover` |
| `image_ratio` | 这张卡封面的比例。别名 `cover_ratio` |
| `ratio` | **整张卡**的宽高比 |
| `badge` | 卡片右上角的小标。别名 `tag` `label` |
| `tags` | 标签列表，`tags: [甲, 乙]` 或 `tags: 甲, 乙` |
| `meta` | 页脚上方的小字。别名 `note` |
| `span` | 占几列，写 `2` 就是双宽。别名 `cols` |
| `featured` | `true` 等同 `span: 2`，并加一层强调底 |
| `theme` | 这张卡的色相 |
| `class` | 追加自定义类 |
| `body` | `layout: rows` 时右栏的 Markdown。别名 `aside` `more` `detail` |
| `reverse` | `layout: rows` 时左右对调 |
| `row_ratio` | 只改这一行的宽度比例（`1 2`、`18em`），覆盖块上的值 |
| `alt` | `icon` 是图片时的替代文本；一般不用写，见下 |

`image:` 是**封面图**，所以卡片头上那个圆形成员要用 `icon:` 写图片路径：

```homepage-cards
columns: 3
title: 封面图与圆形标记
cards:
  - title: 有封面
    image: ../../assets/shot-2.svg
    desc: image 铺在卡片上方
    icon: ../../assets/mark-orbit.svg
    link: index.md
  - title: 封面比例
    image: ../../assets/shot-2.svg
    image_ratio: 1/1
    desc: image_ratio 单独控制封面
  - title: 双宽卡
    icon: view-dashboard-outline
    desc: "span: 2 占两列"
    span: 2
    theme: amber
```

## 整卡比例

`ratio` 控制**整张卡的外形**。同一行里不同比例的卡片会各自按比例显示、顶对齐
（不会互相拉齐，因为拉齐会把比例盖掉）。

```homepage-cards
columns: 3
title: 卡片自己的宽高比
cards:
  - title: 4 / 3
    ratio: 4/3
    icon: shape-outline
    desc: 整张卡是 4:3
  - title: 1 / 1
    ratio: 1/1
    icon: view-gallery-outline
    desc: 方形卡片
  - title: 2 / 3
    ratio: 2/3
    icon: image-outline
    desc: 竖长卡片
```

内容比框高时**卡片内部可以滚动**，页脚不会被裁掉。

!!! warning "比例写斜杠"
    想写 4:3 时写 **`4/3`**。YAML 会把不带引号的 `4:3` 读成六十进制数
    `4×60+3 = 243`，而 243 是合法的 CSS 比例——卡片会高到 243 倍宽。插件会认出
    这个区间、在构建时报警并回退到默认比例。写成 `"4:3"`（带引号）也可以。

## 一卡一栏：`layout: rows`

卡片在左，说明文字在右；说明用 `body:` 写 Markdown。**没写 `body` 的行右栏会留空**，
所以连续几行的卡片仍然对齐。

```homepage-cards
layout: rows
title: '一栏一卡：layout rows'
subtitle: 左卡片、右说明；reverse 单独对调一行。
cards:
  - title: 左边卡片
    icon: file-document-outline
    desc: 卡片本体
    body: |
      ### 右边是正文

      用站点自己的 Markdown 渲染：

      - 列表
      - **强调**、`代码`
  - title: 这一行没有说明
    icon: text-box-outline
    desc: 右栏留空，但卡片宽度不变
  - title: 这一段反过来
    icon: refresh
    desc: "reverse: true"
    reverse: true
    body: |
      图和文左右对调。
```

### 控制两边的宽度：`row_ratio`

默认是**对半分**。写 `row_ratio` 就能改，值有两种写法：

| 写法 | 含义 |
| --- | --- |
| `row_ratio: 18em` | 只给**卡片**的大小，右边自动占剩下的 |
| `row_ratio: 2 3` | 直接给两条轨道，顺序是「卡片 说明」 |

纯数字会变成 `fr`，所以 `2 3` 读作「卡片占 2 份、说明占 3 份」。

```homepage-cards
layout: rows
row_ratio: 18em
title: 'row_ratio: 18em'
subtitle: 卡片固定 18em，说明占满剩下的宽度——最适合「图标卡 + 一段说明」。
cards:
  - title: 安装
    icon: download-outline
    desc: 一条命令
    body: |
      `pip install mkdocs-homepage-plugin`，然后在 `mkdocs.yml` 里加一行
      `plugins: [homepage]`。不需要再往 `markdown_extensions` 里加东西。

      右边这一栏是完整的 Markdown，可以写多段、列表、引用块。
  - title: 编写
    icon: text-box-outline
    desc: 围栏里写属性
    body: |
      一个围栏代码块就是一块内容：属性写 YAML，`---` 以下是正文。

      卡片本身只有标题和图标，所有说明都放在右边，于是**一眼扫过去**
      看到的是「安装 / 编写 / 预览」，而不是三张一样大的卡片。
```

```homepage-cards
layout: rows
row_ratio: 2 3
title: 'row_ratio: 2 3'
subtitle: 卡片 2 份、说明 3 份。
cards:
  - title: 窄卡宽文
    icon: layers-outline
    desc: 卡片占 2/5
    body: |
      说明占 3/5，读起来更舒服——一段话每行太长或太短都会累。
  - title: 也可以单行覆盖
    icon: refresh
    desc: 这一行反过来
    row_ratio: 3 2
    body: |
      单张卡写 `row_ratio` 会盖掉块上的值；`reverse: true` 还能把两边对调。
```

!!! tip "卡片比说明高的时候"
    两栏默认**垂直居中**。想让它们顶对齐就写 `align: start`——
    和 `hero`、`cta` 是同一个开关。

## 能不能把区块嵌套起来？

**不能。** 围栏必须写在顶层，而且区块的正文是用「**不含本插件**」的 Markdown
实例渲染的，所以正文里再写一个 `homepage-*` 围栏只会**原样显示成代码块**：

````markdown
```homepage-split
---
左边

===

```homepage-cards          ← 不会渲染，会被当成示例代码显示
cards:
  - title: A
```
```
````

这是刻意的：区块正文由子渲染器处理，如果允许嵌套，一个正文里再放正文就会
无限递归下去（`converter.py` 里把本插件按包名排除掉，注释是
*"so a fragment can never recurse"*）。

**要「一边卡片、一边正文」，用 `layout: rows`**——它就是为这件事准备的，
而且比嵌套多一个好处：两边的宽度由你控制。上面那一节就是它。
`split` 则适合**两边都是正文**的场合（比如「短栏目录 + 长栏正文」）。

## 单张卡片的颜色

卡片可以**自己**指定底色和光色，不跟主题走：

| 键 | 说明 |
| --- | --- |
| `bg` | 底色，浅色与深色都用它。别名 `surface` `background_color` |
| `bg_dark` | 只在深色模式覆盖 `bg` |
| `glow` | 光照（描边、光晕、强调色）。别名 `accent` `color` |
| `glow_dark` | 只在深色模式覆盖 `glow` |

```homepage-cards
columns: 3
title: 单张卡片的颜色
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

值是任意合法 CSS 颜色（`#4f6bed`、`rgb(...)`、`oklch(...)`、`rebeccapurple`）。
写错会在构建时报警并忽略该条。

## 细节

- **`span: 2` 是「占两列」而不是「宽两倍」**：它跨两条轨道，所以和相邻卡的间距
  仍然是一个 `gap`。窄屏上跨列会被取消，否则会挤成一列半。
- **`icon` 只在没有 `title` 时才会被读成图片的替代文本。** 卡片图标就贴在标题旁边，
  给它一个和标题一样的替代文本，屏幕阅读器会把标题念两遍。所以默认是装饰性的，
  要写就用自己的 `alt:`。
- **空位**：`-` 或 `- blank` 占位置但不画东西，卡片宽度不变。见[全部区块](index.md)。
- `layout: rows` 和 `span` 互斥，跨列在一栏一卡里没有意义。
