# 语法

一页说清「围栏怎么写、属性怎么填、正文放哪里」。

## 一个区块的构成

````markdown
```homepage-cards          ← 信息字符串：homepage-<区块名>
columns: 3                ┐
title: 标题               │ 属性：标准 YAML 映射
cards:                    │
  - 一个 | 条目           ┘
---                       ← 分隔线（可选）
正文用 Markdown 写。       ← 正文（可选）
```
````

三段的规则是**确定的，不靠猜**：

| 情况 | 结果 |
| --- | --- |
| 围栏里有一行**只有** `---` | 它上面是属性，下面是正文 |
| 没有 `---`，且**第一段**全是 `键: 值` 的样子 | 整段都是属性，没有正文 |
| 没有 `---`，第一段像普通段落 | 整段都是正文，没有属性 |

需要正文里出现水平分割线时用 `***`，不要用 `---`。

!!! note "属性可以为空"
    `---` 上面什么都没有也可以，正文照常渲染。只有正文的区块很常见，
    比如 [`text`](blocks/text.md) 和 [`split`](blocks/split.md)。

## 正文用站点自己的扩展

正文（以及引用内容、卡片右栏等）用的是**页面自己的 `markdown_extensions`**，
所以写作体验和页面正文完全一样：admonition、内容标签页、脚注、代码高亮、
属性列表都能用。

```homepage-text
panel: true
title: 正文里什么都能写
---
!!! note "引用块"
    `admonition`、`pymdownx.details`、`pymdownx.tabbed` 都不需要额外适配。

=== "标签页 A"

    第一个标签页。

=== "标签页 B"

    第二个标签页，`alternate_style` 也没问题。

行内代码 `like this`、[链接](../index.md)、表格、脚注，都一样。
```

渲染正文时只排除两个扩展：

| 被排除 | 原因 |
| --- | --- |
| `toc` | 会给卡片标题加永久链接锚点，还会留下一个页面级目录 |
| `meta` | 会把正文开头的 `键: 值` 段落当成 front matter 吃掉 |

!!! warning "区块不能放在内容标签页里"
    围栏必须从**行首 0–3 个空格**开始，也就是「顶层围栏」。

    内容标签页要求里面的内容缩进 4 格，所以这样的写法**不会被识别**：

    ````text
    === "标签页"

        ```homepage-cards
        ```
    ````

    按 Markdown 的规则，缩进 4 格就是**缩进代码块**，围栏会被当成示例代码
    原样显示，而不渲染成区块。

    想让几种变体并列展示，用**小标题**（`###`）分节，每个变体一个区块——
    这样它们还能出现在页面目录里。

    区块**正文里**写 `===` 是完全可以的（正文由 `pymdownx.tabbed` 正常处理），
    只是围栏本身要顶格。

## 属性就是 YAML

属性是标准的 YAML 映射，所以按 YAML 的规矩来：

```yaml
title: 普通写法
columns: 3
tags: [标签一, 标签二]        # 行内列表
cards:
  - title: 展开写
    desc: 多行更清楚
```

几条会踩到的：

| 想写 | 要写成 | 为什么 |
| --- | --- | --- |
| 值里有 `: ` | `title: '外观：outlined'` | 冒号加空格会被读成嵌套映射 |
| 值以反引号开头 | `desc: '\`code\`'` | 有些 YAML 解析器会当成保留字符 |
| 布尔 | `true` / `false` | 也接受 `yes` / `no` / `1` / `0` / `on` / `off` |
| 比例 | `ratio: 4/3` | **不要写 `4:3`**，YAML 会读成六十进制数 243 |

!!! danger "`4:3` 不是 `4:3`"
    YAML 会把不带引号的 `4:3` 读成**六十进制数** `4×60+3 = 243`，而 243 是一个
    完全合法的 CSS 比例。于是卡片会高到 243 倍宽，而且没有任何报错。
    插件现在会识别这个区间、在构建时报警并回退到默认值。
    **比例一律写斜杠：`4/3`**，或者给值加引号。同类问题还有标题——
    `title: 4:3` 会显示成 `243`。

## 竖线简写

列表条目**在只有纯文本时**可以用 `|` 一行写完，省掉一堆键名：

```yaml
cards:
  - 标题 | 链接 | 描述 | 图标名
```

字段顺序是**共享的常量**，不随区块变。两套顺序：

| 用于 | 顺序 |
| --- | --- |
| 链接类：`cards` `features` `steps` `links` `logos` | `标题 \| 链接 \| 描述 \| 图标` |
| 按钮类：`hero` / `cta` 的 `actions` | `文字 \| 链接 \| 样式 \| 图标` |
| 其他：`stats` `highlights` 等 | 见各自页面 |

!!! warning "简写只在「一整项都是纯文本」时生效"
    `- 标题 | 链接` 是简写；`- title: 标题 | 链接` 是**一个映射**，
    YAML 会把 `标题 | 链接` 当成 `title` 的值。两行只差几个字符。

## 空位

所有可以重复的列表都允许留空：

```yaml
cards:
  - 第一张
  -             # 空
  - 第三张
```

| 写法 | 含义 |
| --- | --- |
| `-` | 空位 |
| `- {}` | 空位 |
| `- empty` / `- blank` / `- gap` / `- spacer` | 空位（大小写随意） |
| `- empty \| /guide/` | **不是**空位——带分隔符就是一条真条目，标题叫 empty |

**尺寸按列数算，不按条数算**：4 列里只放 3 张卡，卡片宽度仍然是四列的宽度。
空位不占行、不可聚焦、对屏幕阅读器隐藏，只是占住自己的那一格。

一个列表**全是**空位会报错——那不是「留空」，是写错了。

## 通用属性

16 个区块全都认识下面这些属性。

| 属性 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `theme` | 关键词 | `indigo` | 色相，见下 |
| `class` | 类名 | — | 追加自定义类。别名 `classes` |
| `id` | 字符串 | — | 页面内锚点。别名 `anchor` |
| `width` | 关键词 | 整栏 | `content` 限制阅读宽度并居中 / `wide` |
| `align` | 关键词 | `start` | `start` `center` `end` `justify` |
| `reveal` | 关键词 | `auto` | 滚动进入的动画，见下 |
| `tilt` | 数字 / `false` | `6` | 卡片倾斜强度 |
| `background` | 关键词 | — | `tint` / `surface` / `accent`，给整块加浅底 |
| `pattern` | 关键词 | 见下 | `aurora` `grid` `dots` `rays` `none` |
| `gradient` | 布尔 | `false` | 标题用渐变文字 |
| `gap` | 长度 | `0.9em` | 栅格间距 |
| `columns` | 整数 | 自动 | 列数 |
| `min_cols` | 长度 | `13em` | 没写 `columns` 时单格的最小宽度 |
| `ratio` | 比例 | 各区块自带 | 图片的默认比例 |

### `theme`

14 个色相：`indigo` `blue` `cyan` `teal` `green` `lime` `amber` `orange`
`deep-orange` `pink` `purple` `deep-purple` `blue-grey` `slate`。

**只声明一个色相，其余颜色全部推导出来**：强调色、浅底、描边、光晕、投影
都从这一个值算，所以浅色和深色两种模式下都有稳定的对比度，不需要分别调。

```homepage-cards
title: theme 只决定一个色相
columns: 4
cards:
  - title: indigo
    icon: palette-outline
  - title: teal
    icon: palette-outline
    theme: teal
  - title: amber
    icon: palette-outline
    theme: amber
  - title: pink
    icon: palette-outline
    theme: pink
```

### `columns` 与 `min_cols`

`columns: 3` 的含义是**「三列」**，不是「最多三列」：

- 容器放得下 → 就是三列，而且卡片按三列的宽度算。
- 放不下（窄屏）→ 自动减少列，不需要写媒体查询。
- 一列最窄到 `8.5em`（硬底线）就不再减了。

不写 `columns` 时，格子凭自己的舒适宽度（`min_cols`，默认 `13em`）铺满一行。

```homepage-cards
columns: 4
title: 'columns 4，只有 3 张卡'
subtitle: 第 4 个位置是空的，但卡片宽度仍然是四列的宽度。
cards:
  - title: 一
    icon: layers-outline
  - title: 二
    icon: view-gallery-outline
  - title: 三
    icon: shape-outline
  -
```

```homepage-cards
columns: 3
title: 'columns 3，同样 3 张卡'
subtitle: 对比一下：卡片明显更宽。列数是尺寸，不是上限。
cards:
  - title: 一
    icon: layers-outline
  - title: 二
    icon: view-gallery-outline
  - title: 三
    icon: shape-outline
```

### `reveal`

滚动进入视口时的动画：`fade` `up` `down` `left` `right` `zoom` `flip`，
或者 `false` 关掉。

默认值是**插件选项**的 `reveal`（演示站点是 `auto`）：

| 取值 | 含义 |
| --- | --- |
| `auto` | **列表类区块**（`cards` `features` `stats` `steps` `links` `logos` `testimonials`）依次错峰出现，其余区块静止 |
| `false` / `off` | 全部静止 |
| 具体值 | 全部用这一种动画 |

错峰的间隔是 55ms，**最多累计到第 8 项**——二十张卡片不会让最后一张等一秒。

单个区块写 `reveal:` 会覆盖插件选项。**`reveal: false` 是最常用的一个**：
把某个区块从错峰里摘出去。

### `tilt`

卡片（`cards`）的 3D 倾斜强度，默认取插件选项的 `tilt_strength`（演示站点是 `6`）：

```yaml
tilt: 12      # 更明显
tilt: false   # 这一块不要倾斜
tilt: 0       # 同上
```

### `background`

给整块加一层底，把它和上下内容分开：

| 取值 | 效果 |
| --- | --- |
| `tint` | 最浅的一层强调色 |
| `surface` | 主题自己的表面色 |
| `accent` | 较重的强调色底（正文会自动换成对比色） |

```homepage-text
background: tint
title: 'background: tint'
---
整块加了一层最浅的强调色底。
```

### `pattern`

装饰底纹，画在内容背后：

| 取值 | 效果 |
| --- | --- |
| `aurora` | 极光式的柔和色块 |
| `grid` | 网格 |
| `dots` | 点阵 |
| `rays` | 放射线 |
| `none` | 什么都没有 |

**`hero` 和 `cta` 默认是 `aurora`**（它们是「一条横幅」），其余区块默认 `none`。

### `width` 与 `align`

`width: content` 把内容限制在阅读宽度内并居中——正文类的区块用它更舒服。
`align: center` 会连栅格项的交叉轴一起居中（只写 `text-align` 的话，
标题居中了、图标还在左边）。

```homepage-text
width: content
align: center
title: width content + align center
---
适合一段想让人一口气读完的话。
```

## 诊断

写错不会静默失败：

| 情况 | 结果 |
| --- | --- |
| 属性不是合法 YAML | 警告 + 页面上的错误标记，写明行号和 YAML 的具体毛病 |
| 区块名不认识 | 警告 + 错误标记，列出所有可用区块 |
| 缺少必填项（比如 cards 没有 `cards:`） | 警告 + 错误标记 |
| `theme` / `icon` 写错 | 警告，并列出所有可用取值 |
| 比例写成了 `4:3` | 警告，回退到默认比例 |
| 卡片颜色不合法 | 警告，忽略该条颜色 |

错误标记是一个虚线框，**出现在出错的准确位置**，写明区块类型和源文件行号——
一个被默默删掉的区块是首页最糟糕的失败方式。

`strict: true`（[插件选项](../reference/options.md)）会让这些警告直接**失败构建**，
适合装在 CI 里。

## 下一步

- [全部区块](blocks/index.md) —— 一个区块一页，含全部属性
- [场景配方](recipes.md) —— 「我想做这样一个页面」
