# anim

会动的容器。六种效果，都是纯 CSS（除了逐字打字需要一点 JavaScript）。

```homepage-anim
effect: typetext
---
用 Markdown 写首页，写法本身就是文档的一部分。
```

## 属性

| 属性 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `effect` | 关键词 | `float` | 六种效果之一，见下。别名 `type` |
| `duration` | 时长 | 各效果自带 | 一个周期的时间，如 `4s`、`1200ms` |
| `delay` | 时长 | `0s` | 开始前等多久 |
| `text` | 文本 | — | 没有正文时用它放文字 |

正文（`---` 以下）用站点自己的 Markdown 渲染。**正文和 `text` 至少要有一个**，
否则报错。

!!! warning "`effect` 写错会直接报错"
    和其他「写错就回退到默认值」的属性不同，`effect` 拼错会**抛错并在页面上
    留下错误标记**，因为一个「不动」的动画块看起来和「忘了写」完全一样。
    错误信息会列出所有可用取值。

## 六种效果

### float

```homepage-anim
effect: float
duration: 3s
text: 轻轻地上下浮动
```

### pulse

```homepage-anim
effect: pulse
duration: 2s
text: 呼吸式的明暗变化
```

### shimmer

```homepage-anim
effect: shimmer
duration: 2.5s
text: 一道高光扫过去
```

### gradient

```homepage-anim
effect: gradient
duration: 4s
text: 渐变文字缓缓流动
```

### marquee

```homepage-anim
effect: marquee
duration: 12s
text: 无缝横向滚动，鼠标移上去会停
```

### typetext

```homepage-anim
effect: typetext
text: 一个字一个字地打出来
```

## 用 Markdown 正文

`text` 只支持行内 Markdown；需要多行就用正文：

```homepage-anim
effect: gradient
title: 正文用完整的 Markdown
---
**加粗**、`代码`、[链接](../index.md) 都可以。

还可以是多段。
```

## 细节

- **`marquee` 会复制一份内容**来实现无缝循环，副本对屏幕阅读器隐藏，
  所以一段文字不会被念两遍。
- **`typetext` 用 JavaScript 逐字显示**，但文字在 HTML 里是完整的：
  脚本没跑起来时显示的是全文，而不是空白。**鼠标移入会立刻显示完整文本**，
  不让人等。
- 所有效果都遵守 `prefers-reduced-motion`：用户在系统里关掉动效时全部静止。
- `duration` 影响的是**一个周期**：`float` 是浮上去再浮回来，`marquee` 是滚完一趟。
- 想要「滚进视野才淡入」的动画用通用属性 `reveal`，不是这个块。
