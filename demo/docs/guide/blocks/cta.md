# cta

收尾的行动号召：居中、可带装饰底纹，视觉上比正文重、比首屏轻。

```homepage-cta
title: 现在就可以写第一块内容
subtitle: 装好插件，在任意页面写一个围栏代码块。
actions:
  - 开始使用 | ../index.md | primary | rocket-launch-outline
  - 看全部区块 | index.md
note: 不需要任何主题覆盖文件。
```

## 属性

| 属性 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `title` | 文本 | — | 标题（默认 `h2`）。别名 `heading` |
| `eyebrow` | 文本 | — | 标题上方的小标签 |
| `subtitle` | 文本 | — | 标题下方说明。别名 `lead` `description` |
| `actions` | 列表 | — | 按钮，字段顺序和 [`hero`](hero.md) 一样 |
| `note` | 文本 | — | 按钮下方小字。别名 `fineprint` `footnote` |
| `image` | 路径 | — | 右侧配图。别名 `img` |
| `ratio` | 比例 | `1/1` | 配图比例 |
| `pattern` | 关键词 | `aurora` | 底纹，见[通用属性](../syntax.md) |
| `gradient` | 布尔 | `false` | 标题用渐变文字 |

正文（`---` 以下）会渲染成标题下方的说明段。

## 底纹

`hero` 和 `cta` 默认带 `aurora` 底纹——它们是「一条横幅」而不是「一块内容」，
需要一点氛围。写 `pattern: none` 关掉。

### aurora（默认）

```homepage-cta
title: pattern aurora
subtitle: 默认的极光底纹。
actions:
  - 主要动作 | ../index.md | primary
```

### grid

```homepage-cta
pattern: grid
title: pattern grid
subtitle: 网格底纹。
actions:
  - 主要动作 | ../index.md | primary
```

### dots

```homepage-cta
pattern: dots
title: pattern dots
subtitle: 点阵底纹。
actions:
  - 主要动作 | ../index.md | primary
```

### rays

```homepage-cta
pattern: rays
title: pattern rays
subtitle: 放射线底纹。
actions:
  - 主要动作 | ../index.md | primary
```

### none

```homepage-cta
pattern: none
title: pattern none
subtitle: 什么都没有。
actions:
  - 主要动作 | ../index.md | primary
```

## 渐变标题

```homepage-cta
gradient: true
title: 渐变文字的标题
subtitle: gradient true —— 标题用强调色到主色的渐变。
actions:
  - 开始使用 | ../index.md | primary
```

## 带配图

写了 `image` 就变成「图 + 文」两栏：

```homepage-cta
gradient: true
pattern: rays
title: 带上配图
image: ../../assets/hero.svg
ratio: 1/1
actions:
  - 开始使用 | ../index.md | primary
  - 看参考 | ../../reference/index.md
note: 配图默认是 1/1 的方形，用 ratio 改。
```

## 细节

- **默认居中**。写 `align: start` 就靠左——那样会去掉居中版式，变成普通左对齐。
- **底纹默认开**（和 `hero` 一样），因为它是横幅；其余区块默认没有底纹。
- 不要在一页里放多个 `cta`，它是「最后一句」。
- `gradient` 只影响标题，不影响正文和小字。
