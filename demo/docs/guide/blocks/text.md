# text

一段正文，但可以变成面板、可以放大、可以分栏、可以带头像、可以折叠。

```homepage-text
title: 标题是可选的
---
大多数字段都可以直接写正文，不需要任何区块——真的需要特殊排版时再用这个块。

`text` 的价值在于它给一段普通正文加上**面板、标题、分栏、折叠**这几种外壳。
```

## 属性

| 属性 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| （正文） | Markdown | 必填 | `---` 以下必须是正文，空的会报错 |
| `panel` | 布尔 | `false` | 加一层面板底。别名 `callout` |
| `lead` | 布尔 | `false` | 放大字号，当导语用 |
| `columns` | 整数 | `1` | 正文分几栏 |
| `icon` | 图标 | — | 左侧一个标记（图标名或图片） |
| `collapsible` | 布尔 | `false` | 折起来，点击展开 |
| `summary` | 文本 | `展开` | 折叠时那行标题。别名 `title` |

`title` / `subtitle` / `eyebrow` 也都能用（就是块上方的通用标题区）。

## 变体

```homepage-text
panel: true
title: panel true
---
加了一层面板底和描边。适合把注意事项和正文分开。

面板里仍然可以放任何 Markdown：列表、`代码`、链接。
```

```homepage-text
lead: true
title: lead true
---
这是一段导语，字号比正文大一点，适合放在一段很长的正文前面。
```

```homepage-text
columns: 2
title: columns 2
---
正文会分成两栏。

分栏用 CSS 的多列，所以是自动平衡高度的——左边写多长都不会让右边空一块。

窄屏幕上会自动变回一栏。
```

```homepage-text
icon: lightbulb-outline
panel: true
title: icon 让一段话变成一个提示
---
左侧的标记可以是图标名，也可以是指向图片的路径。它在窄屏会自动叠到上方。
```

```homepage-text
collapsible: true
summary: 点开看细节
title: collapsible true
---
折叠块用的是原生 `<details>`，所以不依赖 JavaScript，
键盘和屏幕阅读器都能正常操作。

`summary` 不写时默认是「展开」。
```

## 组合

几种开关可以叠加，顺序是：**折叠外壳 → 图标 → 正文**。

```homepage-text
panel: true
icon: shield-check-outline
collapsible: true
summary: 渲染安全（点开）
title: 面板 + 图标 + 折叠
---
进入属性的值一律转义；进入 `style` 的值经过白名单校验；`href` / `src`
拒绝 `javascript:`、`data:` 之类的协议。

`<script>` 在正文里也不会被执行，因为正文走的是站点自己的 Markdown 扩展。
```

## 细节

- **正文是必需的。** 一个空的 `text` 块会报错——它存在的意义就是装正文，
  空的说明作者写错了围栏。
- `panel` 的面板是**内容容器**，所以它和卡片不同，刻意没有投影。
  Material 自己的 admonition 也是平的，两者放在一起才不会一深一浅。
- `columns` 只影响正文，不影响块上方的标题区。
- `lead` 和 `panel` 可以同时用；`lead` 只改字号，不动底色。
