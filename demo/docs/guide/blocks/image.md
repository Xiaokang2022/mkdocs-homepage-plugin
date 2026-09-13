# image

一张图，可以配说明、可以点开放大、可以浮动在正文旁边。

```homepage-image
src: ../../assets/shot-1.svg
alt: 一张示意图
caption: 默认：整栏宽、圆角、可点开放大。
```

## 属性

| 属性 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `src` | 路径 | 必填 | 图片。别名 `image` `img` `url` `path` |
| `alt` | 文本 | — | 替代文本。别名 `text` |
| `caption` | 文本 | — | 图下方说明，支持行内 Markdown。别名 `desc` `description` |
| `link` | 链接 | — | 点击图片去哪里。别名 `href` |
| `zoom` | 布尔 | 跟随灯箱选项 | `false` 关掉「点开放大」 |
| `ratio` | 比例 | 图片自身 | 强制宽高比 |
| `frame` | 关键词 | — | 画框，见下 |
| `shadow` | 布尔 | `false` | 加投影 |
| `glow` | 布尔 | `false` | 加光晕 |
| `float` | 关键词 | — | `left` / `right`，让图浮到正文旁边。别名 `side` |
| `float_width` | 长度 | `18em` | 浮动图的宽度。别名 `width_px` |
| `max_width` | 长度 | — | 整块的最大宽度，比如 `32em` |

另外 `width: content` 会把图限制在阅读宽度内并居中。

`---` 以下可以写正文，会渲染成图下方的说明段落：

```homepage-image
src: ../../assets/shot-3.svg
caption: 图下方可以再写一段正文
width: content
---
`---` 以下的 Markdown 会渲染在图片下方，用站点自己的扩展——
所以这里可以放列表、链接、`代码`，或者一个 admonition：

!!! note "提示"
    说明区是一个 `.md-home__prose` 容器，排版和页面正文一致。
```

## 画框：`frame`

`frame` 可以写多个（用空格或逗号分开）：

| 取值 | 效果 |
| --- | --- |
| `browser` | 顶部一条浏览器窗口的假装饰栏。别名 `window` `screenshot` |
| `shadow` | 投影 |
| `glow` | 强调色光晕 |

```homepage-image
src: ../../assets/shot-2.svg
caption: frame browser shadow
frame: browser shadow
```

```homepage-image
src: ../../assets/shot-2.svg
caption: frame glow
frame: glow
```

`shadow: true` / `glow: true` 是同一件事的简写：

```homepage-image
src: ../../assets/shot-1.svg
caption: shadow true（等价于 frame shadow）
shadow: true
max_width: 24em
```

## 浮动：`float`

把图浮到文字旁边。**浮动只对后面紧跟的正文有效**，所以浮动图通常后面接一段
普通的 Markdown 正文，而不是接另一个区块。

```homepage-image
src: ../../assets/mark-orbit.svg
float: left
float_width: 9em
alt: 一个圆形标记
```

这是一段普通正文，用来演示 `float: left` 的效果。图片浮动到左边，文字会自动
绕开它排版，宽度由 `float_width` 控制（这里写了 `9em`，默认是 `18em`）。
浮动适合「作者头像 + 简介」「一张小图标 + 一段说明」这类排法：图不大，
但占着一块版面，让文字形成一个自然的缺口。

觉得太宽就调 `float_width`；不需要浮动就在属性里去掉 `float`。

## 细节

- **`ratio` 缺省时用图片自己的比例**，所以大多数情况下不用写。写了的用途是
  让一页里几张图高度一致，或者给还没到位的图先占好位置。
- **`shadow` 在 `image` 块里默认是关的**，和 [`hero`](hero.md)、
  [`showcase`](showcase.md) 相反——一张独立的图通常已经在自己的留白里，
  再加投影会显得飘。
- **`zoom` 默认跟随插件的 `lightbox` 选项。** 写了 `link:` 时点击是导航，
  不会同时开灯箱。
- 浮动图和 `width: content` 同时写会互相打架（一个要窄、一个要居中），
  选一个。
