# hero

页面最上面那一屏。左边文字（eyebrow / 标题 / 副标题 / 正文 / 按钮 / 小字 / 要点），
右边一张图。**只有文字也能用**——没有 `image` 时它会自动变成单栏居中版式。

```homepage-hero
eyebrow: 快速开始
title: 用 Markdown 写首页
subtitle: 围栏里放 YAML 属性，`---` 以下是正文，和页面正文一样的扩展。
image: ../../assets/hero.svg
actions:
  - 读指南 | ../index.md | primary
  - 看全部区块 | index.md
highlights:
  - 16 | 区块类型
  - 95 | 内置图标
  - 0 | 前端依赖
```

## 属性

| 属性 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `eyebrow` | 文本 | — | 标题上方的小标签，支持行内 Markdown。别名 `kicker` `overline` |
| `title` | 文本 | — | 主标题，**默认是 `h1`** |
| `subtitle` | 文本 | — | 标题下方的说明。别名 `lead` `description` |
| `level` | 整数 | `1` | 标题层级，限制在 1–6 |
| `image` | 路径 | — | 右侧配图。别名 `img` `background_image` |
| `ratio` | 比例 | `16/10` | 配图宽高比 |
| `mirror` | 布尔 | `false` | 图与文字左右对调。别名 `reverse` |
| `frame` | 关键词 | — | 图的画框。别名 `image_frame` `art_frame` |
| `shadow` | 布尔 | **`true`** | 图加投影 |
| `glow` | 布尔 | `false` | 图加光晕 |
| `actions` | 列表 | — | 按钮，见下 |
| `highlights` | 列表 | — | 那行小数字，见下 |
| `note` | 文本 | — | 按钮下方的小字。别名 `fineprint` `footnote` |
| `pattern` | 关键词 | `aurora` | 见[通用属性](../syntax.md) |

正文（`---` 以下）会渲染成标题块下方的引导段，用**站点自己的 Markdown 扩展**。

## 按钮：`actions`

一行最多四项，用 `|` 分开：

```yaml
actions:
  - 文字 | 链接 | 样式 | 图标名或图片路径
```

| 位置 | 字段 | 说明 |
| --- | --- | --- |
| 1 | `text` | 按钮文字（别名 `title` `label`） |
| 2 | `link` | 链接（别名 `url` `href`）；**省略就变成一个不可点的 `span`** |
| 3 | `style` | `primary` / `solid` / `filled` 会变成实心主按钮（别名 `variant`）；其余一律是描边按钮 |
| 4 | `icon` | 图标名，或指向图片的路径 |

```homepage-hero
title: 只有按钮，没有图
subtitle: 没有 image 时自动变成单栏居中版式。
actions:
  - 主按钮 | ../index.md | primary | rocket-launch-outline
  - 次按钮 | index.md | | text-box-outline
  - 不可点的标签
note: 按钮下方这行小字用 note 写。
```

## 要点：`highlights`

标题下方那排「16 区块 · 95 图标 · 0 依赖」：

```yaml
highlights:
  - 16 | 区块类型 | layers-outline
```

| 位置 | 字段 | 说明 |
| --- | --- | --- |
| 1 | `value` | 大一点的那行（别名 `text` `title`） |
| 2 | `label` | 小一点的那行（别名 `desc`） |
| 3 | `icon` | 图标名或图片路径；**不写就没有图标** |

```homepage-hero
title: 图在左边
mirror: true
subtitle: mirror（或 reverse）把图和文字换边。
image: ../../assets/shot-1.svg
ratio: 4/3
highlights:
  - 4:3 | 换了个比例
  - 左图 | mirror true
```

## 细节

- **没有 `image` 就是单栏居中**，不需要额外开关；`mirror` 在那种情况下没有作用。
- **`shadow` 在这里默认是开的**（其他区块默认是关的）——首屏那张图如果和背景贴平，
  整块会显得扁。写 `shadow: false` 关掉。
- 配图**不会**被灯箱接管：首屏的图通常自己就是主角，点开会打断阅读。
  需要可点，就显式写 `link:`。
- `ratio` 和 `highlights` 会一起决定首屏高度，两个都改时留意手机上会不会太高。
- hero 默认带 `aurora` 底纹（它是「一条横幅」而不是「一块内嵌内容」）。
  `pattern: none` 关掉。
