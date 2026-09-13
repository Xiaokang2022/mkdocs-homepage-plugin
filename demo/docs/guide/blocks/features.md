# features

密集的小功能点：一个图标、一行标题、一句说明。和 [`cards`](cards.md) 的区别是
**它没有卡片框**——靠间距分组，一排可以放很多个，适合「六条特性」这种清单。

```homepage-features
columns: 3
features:
  - title: 纯 Markdown
    icon: text-box-outline
    desc: 围栏代码块就是一块内容，改文案不用碰 HTML。
  - title: 一个色相推全部
    icon: palette-outline
    desc: 强调色、浅底、描边、投影全从一个 hue 算出来。
    theme: cyan
  - title: 零前端依赖
    icon: lightning-bolt-outline
    desc: 没有图标字体、没有框架，一个样式表一个脚本。
  - title: 图标位也能放图片
    icon: ../../assets/mark-orbit.svg
    desc: icon 写图片路径就变成圆形图片，保留原色。
  - title: 可点
    icon: arrow-up-right
    desc: 写了 link 整块变成链接。
    link: ../syntax.md
  - title: 留空位
    icon: shape-outline
    desc: 空位占位置但不画东西。
```

## 属性

| 属性 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `features` | 列表 | 必填 | 条目列表。别名 `items` |
| `icon_style` | 关键词 | `soft` | 图标气泡的形状。别名 `style` |
| `columns` | 整数 | 自动 | 列数 |
| `min_cols` | 长度 | `13em` | 没写 `columns` 时单个条目的最小宽度 |

### `icon_style`

| 取值 | 外观 |
| --- | --- |
| `plain` | 没有气泡，图标直接露出 |
| `soft` | 浅色圆角底（默认） |
| `circle` | 圆形浅底 |
| `square` | 方形浅底 |
| `solid` | 实心强调色底，图标反白 |

```homepage-features
columns: 2
title: 竖线简写
features:
  - 标题 | ../syntax.md | 描述 | text-box-outline
  - 只有标题
  - 标题 | ../index.md
```

## 五种图标气泡

`icon_style` 是**块级属性**，一个块只能用一种。

### soft（默认）

```homepage-features
columns: 3
icon_style: soft
features:
  - title: 浅色圆角底
    icon: shape-outline
    desc: 最不打扰的一种
  - title: 跟随色相
    icon: palette-outline
    desc: 底色调成浅色的强调色
    theme: teal
  - title: 深色模式自动调
    icon: simple/docker
    desc: 不用自己管
```

### circle

```homepage-features
columns: 3
icon_style: circle
features:
  - title: 正圆
    icon: shape-outline
    desc: 圆形浅底
  - title: 适合品牌标
    icon: simple/github
    desc: 圆底和品牌标很搭
  - title: 也可以放图片
    icon: ../../assets/mark-orbit.svg
    desc: 图片会让出气泡
```

### square

```homepage-features
columns: 3
icon_style: square
features:
  - title: 圆角方底
    icon: shape-outline
    desc: 比 circle 硬一点
  - title: 适合几何图标
    icon: view-dashboard-outline
    desc: 和方形的字形更配
  - title: 排版上也更整齐
    icon: layers-outline
    desc: 一排看起来更像格子
```

### solid

```homepage-features
columns: 3
icon_style: solid
features:
  - title: 实心强调色
    icon: shape-outline
    desc: 图标反白，最显眼
  - title: 换色相
    icon: fire
    desc: 整块跟着变
    theme: orange
  - title: 适合最重要的三条
    icon: rocket-launch-outline
    desc: 太多了会吵
```

### plain

```homepage-features
columns: 3
icon_style: plain
features:
  - title: 没有气泡
    icon: shape-outline
    desc: 图标直接露出来
  - title: 最安静
    icon: minus
    desc: 靠间距而不是形状分组
  - title: 也适合放 logo
    icon: simple/python
    desc: 不需要底色衬托
```

## 单条字段

| 字段 | 说明 |
| --- | --- |
| `title` | 标题。别名 `heading` |
| `desc` | 说明。别名 `description` `text` |
| `icon` | 图标名或图片路径；**不写就没有图标** |
| `link` | 整条变成链接。别名 `url` `href` |
| `theme` | 这一条的色相 |
| `class` | 追加自定义类 |

`|` 简写按 **`标题 | 链接 | 描述 | 图标`** 的顺序填：

```homepage-features
columns: 2
title: 竖线简写
features:
  - 标题 | ../syntax.md | 描述 | text-box-outline
  - 只有标题
  - 标题 | ../index.md
```

## 细节

- **`icon_style` 写在块上**，是整块的形状；不像卡片那样可以一张一个。
  需要混用就写两个 `features` 块。
- `solid` 在深色模式下会自动调亮底色，保证图标和底色的对比度。
- **`columns: 5` 在窄屏会自动变少列**——不用写媒体查询。
- 空位：`- blank` 占位置但不画东西。
