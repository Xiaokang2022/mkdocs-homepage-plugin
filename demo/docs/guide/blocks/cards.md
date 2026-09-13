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
