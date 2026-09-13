# testimonials

用户评价。默认是卡片样式，也可以做成纯引用或极简排版。

```homepage-testimonials
columns: 2
testimonials:
  - quote: |
      写法就是文档的一部分，改文案不用先去找模板文件在哪。
    name: 林一
    role: 文档维护者
    avatar: ../../assets/avatar-1.svg
    link: https://example.com/
  - quote: |
      颜色从一个色相推导，深色模式基本不用单独调。
    name: 赵二
    role: 前端工程师
    avatar: ../../assets/avatar-2.svg
    theme: cyan
```

## 属性

| 属性 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `testimonials` | 列表 | 必填 | 条目列表。别名 `items` `quotes` |
| `style` | 关键词 | `cards` | `cards` / `quote` / `plain` |
| `rating` | 布尔 | `false` | 顶部加五颗星 |
| `columns` | 整数 | 自动 | 列数 |
| `min_cols` | 长度 | `13em` | 单条最小宽度 |

### `style`

| 取值 | 外观 |
| --- | --- |
| `cards` | 卡片 + 一个大引号 |
| `quote` | 只有大引号 + 左侧竖线，没有卡片框 |
| `plain` | 连引号都没有，纯排版 |

```homepage-testimonials
columns: 2
style: quote
rating: true
testimonials:
  - quote: 左边一根竖线，没有卡片框。
    name: 引用样式
    role: style quote
  - quote: rating 打开就有五颗星。
    name: 带评分
    role: rating true
```

## 单条字段

| 字段 | 说明 |
| --- | --- |
| `quote` | **必填**，引用内容，**用完整的 Markdown 渲染**（可以放列表、链接、强调）。别名 `text` `desc` |
| `name` | 署名。别名 `title` `author` |
| `role` | 职位 / 身份。别名 `desc` `position` |
| `avatar` | 头像图片。别名 `image` `img` `photo` |
| `link` | 给署名加链接。别名 `url` `href` |
| `theme` | 这一条的色相 |

`|` 简写按 **`引用 | 姓名 | 职位 | 头像`** 的顺序填：

```homepage-testimonials
columns: 3
title: 竖线简写
testimonials:
  - 一行写完的引用 | 姓名 | 职位 | ../../assets/avatar-3.svg
  - 没写头像就用姓名首字 | 王三
  - 很短的引用 | 孙四 | 只到职位
```

## 引用里可以写 Markdown

`quote` 是**块级**渲染，不是行内文本：

```homepage-testimonials
columns: 1
testimonials:
  - quote: |
      可以写列表：

      - 第一条
      - 第二条

      也可以写 `代码`、[链接](../index.md) 和 **强调**。
    name: 完整的 Markdown
    role: quote 用块级渲染
    avatar: ../../assets/avatar-1.svg
```

## 细节

- **没有头像时用姓名首字兜底**，所以一张只有姓名和引用的卡片也不会空一块。
- `rating` 是**块级**开关，五颗星是装饰性的（`aria-hidden`），不会被读出来。
- `style: plain` 会连大引号一起去掉——如果只想换配色，用 `theme` 而不是换 `style`。
- 空位：`- blank` 可以在一排里留一个空档。
