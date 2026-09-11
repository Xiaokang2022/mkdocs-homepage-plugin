# 语法速查

## 一个区块的构成

````text
```homepage-<类型>          ← 信息字符串：决定这是哪种区块
<属性>                       ← 可选，一段 YAML 映射
---                          ← 可选分隔线：单独一行、顶格
<正文>                       ← 可选，用站点自己的扩展渲染的 Markdown
```
````

分割规则只有两条：

1. **正文里出现单独一行的 `---`，它上面全是属性，下面全是正文。**
   正文里如果确实需要一条水平线，用 `***`。
2. 没有分隔线时，整段**要么**是属性**要么**是正文：如果第一段里每一行都是
   `键: 值`（以及它们缩进的续行），就当成属性；否则整段都是正文。

写作时优先用第 1 条——它不需要任何猜测。

## 属性

属性是标准 YAML，所以列表、嵌套、多行字符串都可用：

```homepage-cards
columns: 2
cards:
  - title: 对象写法
    icon: file-document-outline
    desc: 字段写全，选项一目了然
    link: /guide/
    theme: cyan
    tags: [推荐, 可读]
  - title: 简写写法
    icon: lightning-bolt-outline
    desc: "用竖线分隔：标题 | 链接 | 描述 | 图标"
    theme: amber
```

同一个字段往往有多个别名，选你顺手的写，例如 `desc` / `description` / `text`、
`src` / `image` / `img` / `path`、`title` / `heading`。

!!! tip "值得记住的几个简写"

    - **列表项**：`标题 | 链接 | 描述 | 图标`，用竖线分隔，缺失的字段留空即可。
    - **卡片页脚**：`link_text` 默认是「查看」。
    - **外部链接**：以 `http://` / `https://` 开头的链接自动 `target="_blank"` 并带
      `rel="noopener"`；想强制当前窗口打开就写 `external: false`。

## 正文

正文区使用**站点自己启用的 `markdown_extensions`** 渲染，所以这里能用的东西和页面
正文完全一样：

```homepage-text
panel: true
---
!!! note "引用块"
    `admonition`、`pymdownx.details`、`pymdownx.tabbed` 都不需要额外适配。

=== "标签页 A"

    第一个标签页。

=== "标签页 B"

    第二个标签页，`alternate_style` 也没问题。

行内代码 `like this`、[链接](../index.md)、表格、脚注，都一样。
```

渲染正文时只会排除两个扩展：

| 被排除 | 原因 |
| --- | --- |
| `toc` | 会给卡片标题加永久链接锚点，还会留下一个页面级目录 |
| `meta` | 会把正文开头的 `键: 值` 段落当成 front matter 吃掉 |

## 通用属性

每种区块都认识下面这些属性：

| 属性 | 取值 | 说明 |
| --- | --- | --- |
| `theme` | `indigo` `blue` `cyan` `teal` `green` `lime` `amber` `orange` `deep-orange` `pink` `purple` `deep-purple` `blue-grey` `slate` | 只决定一个色相，其余颜色由它推导 |
| `class` | 类名 | 追加自定义类 |
| `id` / `anchor` | 字符串 | 页面内锚点 |
| `width` | `content` / `wide` | `content` 限制阅读宽度并居中，默认为整栏 |
| `align` | `start` `center` `end` `justify` | 对齐方式；`center` 会把栅格项的交叉轴一并居中 |
| `reveal` | `up` `down` `left` `right` `zoom` `fade` / `false` | 滚动进入时的动画；列表类区块默认依次错峰出现 |
| `tilt` | 数字 / `false` | 卡片倾斜强度（默认 6） |
| `background` | `tint` `surface` `accent` | 给整块加一层浅底 |
| `pattern` | `aurora` `grid` `dots` `rays` / `none` | 块背后的装饰底纹；`hero` 与 `cta` 默认 `aurora`，其余默认无 |
| `gradient` | 布尔 | 标题使用渐变文字 |
| `gap` | 长度 | 栅格间距 |
| `columns` | 整数 | **最多**几列；放不下时自动减列，不需要写媒体查询 |
| `min_cols` | 长度 | 单个栅格项的最小宽度，默认 `13em` |

`title` / `subtitle` / `eyebrow` 在大多数区块里都可用，支持行内 Markdown。

## 诊断

写错了不会静默失败：

- 属性不是合法 YAML、类型名不存在、缺少必填项 → 构建时输出警告，并在页面上留下
  一个虚线框的错误标记，写明出错的区块类型与行号。
- `strict: true` 时改为直接让构建失败，适合装在 CI 里。
- 未知的 `theme`、未知的 `icon` 同样会给出警告，并列出所有可用取值。
