# gallery

多张图。三种模式：横向滚动、分页、网格。也可以直接用一个 Markdown 图片列表当正文。

```homepage-gallery
title: 'mode: scroll（默认）'
subtitle: 横向滚动，带上一张/下一张按钮和圆点。
images:
  - src: ../../assets/shot-1.svg
    caption: 第一张
  - src: ../../assets/shot-2.svg
    caption: 第二张
  - src: ../../assets/shot-3.svg
    caption: 第三张
```

## 属性

| 属性 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `images` | 列表 | 必填* | 图片列表。别名 `items` |
| `mode` | 关键词 | `scroll` | `scroll` / `paged` / `grid`。别名 `layout` |
| `per_view` | 数字 | 自动 | 一屏放几张。别名 `per_page` |
| `ratio` | 比例 | `16/9` | 单张图的比例 |
| `columns` | 整数 | 自动 | **只在 `mode: grid` 时有用** |
| `min_cols` | 长度 | `13em` | 同上 |

\* 也可以不写 `images`，改用正文里的 Markdown 图片，见下。

## 三种模式

### scroll（默认）

```homepage-gallery
mode: scroll
per_view: 2
images:
  - src: ../../assets/shot-1.svg
    caption: per_view 2
  - src: ../../assets/shot-2.svg
    caption: 一屏两张
  - src: ../../assets/shot-3.svg
    caption: 可以横向滚
  - src: ../../assets/shot-1.svg
    caption: 也可以拖
```

### paged

```homepage-gallery
mode: paged
per_view: 3
images:
  - src: ../../assets/shot-1.svg
    caption: 分页 1
  - src: ../../assets/shot-2.svg
    caption: 分页 2
  - src: ../../assets/shot-3.svg
    caption: 分页 3
  - src: ../../assets/shot-1.svg
    caption: 第二页 1
  - src: ../../assets/shot-2.svg
    caption: 第二页 2
  - src: ../../assets/shot-3.svg
    caption: 第二页 3
```

### grid

```homepage-gallery
mode: grid
columns: 3
images:
  - src: ../../assets/shot-1.svg
    caption: 网格 1
  - src: ../../assets/shot-2.svg
    caption: 网格 2
  - src: ../../assets/shot-3.svg
    caption: 网格 3
  - src: ../../assets/shot-1.svg
    caption: 网格 4
  - src: ../../assets/shot-2.svg
    caption: 网格 5
  - src: ../../assets/shot-3.svg
    caption: 网格 6
```

## 单条字段

| 字段 | 说明 |
| --- | --- |
| `src` | 图片路径。别名 `image` `path` |
| `caption` | 图下方说明 |
| `alt` | 替代文本 |

```yaml
images:
  - src: assets/a.svg
    caption: 说明
    alt: 替代文本
  - assets/b.svg | 也可以简写 | 替代文本
```

## 用正文里的 Markdown 图片

不写 `images:` 时，画廊会从正文里**把图片捡出来**。这样做的好处是：图可以用
站点自己的 Markdown 写法（`![alt](src "title")`、外链、包裹在链接里），
而画廊负责把它们排成一条可滚动的轨道。

```homepage-gallery
mode: paged
per_view: 2
title: 正文里的 Markdown 图片
---
![第一张](../../assets/shot-1.svg "从 title 变成 caption")

[![第二张](../../assets/shot-2.svg "图片套了链接")](https://example.com/)
```

## 细节

- **`per_view` 不写时由 CSS 按容器宽度决定**，写了就是硬性的一屏几张。
  手机上即使写了 `per_view: 3` 也会退化成能放下的数量。
- **`mode: grid` 才认 `columns`**；滚动和分页是「轨道」，一屏几张由 `per_view`
  决定，`columns` 在那里没有意义。
- **空位**：`- blank` 在滚动模式下是一个空档，在分页模式下**会算作一页**——
  这是刻意的，否则页码会错位。
- 画廊本身可以获得焦点（`tabindex="0"`），所以键盘可以直接左右滚动。
- 开启灯箱时，点击任意一张会放大并可左右切换。
