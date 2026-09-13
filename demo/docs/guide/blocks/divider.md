# divider

分隔线。五种样式，用来在不同的内容群之间换口气。

## 属性

| 属性 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `style` | 关键词 | `line` | `line` / `space` / `dots` / `wave` / `gradient`。别名 `variant` |
| `text` | 文本 | — | 线中间放一个标签。别名 `label` `title` |
| `size` | 长度 | `2.5em` | **只在 `style: space` 时有用** |

## 五种样式

### line

一条细线。

```homepage-divider
style: line
```

### dots

一排点。

```homepage-divider
style: dots
```

### wave

一条波浪线。

```homepage-divider
style: wave
```

### gradient

两端淡出的渐变线。

```homepage-divider
style: gradient
```

### space

什么都不画，只是撑开 `size` 那么高的空白。

```homepage-divider
style: space
size: 4em
```

## 带标签

`text` 会在线的中间放一个标签，两侧的线自动让开：

```homepage-divider
style: line
text: 下一节
```

```homepage-divider
style: dots
text: 或者用点
```

```homepage-divider
style: gradient
text: 渐变也可以
```

## 细节

- 它是 `<div role="separator">`，所以屏幕阅读器能认出这是一条分隔。
- `size` 只在 `space` 时生效；写别的样式时 `size` 会被忽略（不是报错）。
- 三个标签属性 `text` / `label` / `title` 完全等价。
