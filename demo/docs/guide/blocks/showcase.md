# showcase

图文交替的叙事行。每行一个主张配一张图，左右交替，视线自然地向下走。
这是产品页最常用的骨架。

```homepage-showcase
showcase:
  - eyebrow: 第一步
    title: 用 Markdown 写首页
    desc: 语法就是页面本身，改文案不需要看 HTML。
    image: ../../assets/shot-1.svg
    link: ../syntax.md
    features:
      - 一个围栏代码块就是一块内容
      - 属性是标准 YAML
  - title: 风格由主题决定
    desc: 颜色从一个色相推导，浅色与深色都不需要单独调。
    image: ../../assets/shot-2.svg
    theme: cyan
```

## 块级属性

| 属性 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `showcase` | 列表 | 必填 | 行列表。别名 `items` `sections` |
| `alternate` | 布尔 | `true` | 逐行左右交替 |
| `reverse` | 布尔 | `false` | 翻转**整个序列**（第一行的图换到左边） |
| `link_text` | 文本 | `了解更多` | 「了解更多」的默认文案 |
| `ratio` | 比例 | `16/10` | 配图的默认比例 |
| `columns` | — | — | **不用**，一行就是一行 |

## 单行字段

| 字段 | 说明 |
| --- | --- |
| `title` | 标题，渲染成 `h3`。别名 `heading` |
| `eyebrow` | 标题上方的小标签。别名 `kicker` |
| `desc` | 说明文字。别名 `description` `text` |
| `image` | **必填**，配图。别名 `img` `src` `cover` |
| `ratio` | 这一行配图的比例（覆盖块上的） |
| `features` | 要点列表，见下。别名 `bullets` |
| `link` | 「了解更多」的链接。别名 `url` `href` |
| `link_text` | 「了解更多」的文案 |
| `reverse` | 这一行左右对调 |
| `theme` | 这一行的色相 |
| `frame` | 配图的画框 |
| `shadow` | 布尔，默认 **`true`** |
| `glow` | 布尔，默认 `false` |
| `zoom` | 布尔，默认 `false`；`true` 让配图可点开 |

## 要点：`features`

每行一条，`|` 分开：

```yaml
features:
  - 文字 | 补充说明 | 图标名或图片路径
```

第一个位置既有文字时它就是内容（别名 `text` `desc` `title`）。
**不写图标时用 `check-circle-outline`。**

```homepage-showcase
alternate: false
title: 每一行都保持"文左图右"
subtitle: alternate false 关掉交替。
showcase:
  - title: 不交替
    desc: 四行都长这边。
    image: ../../assets/shot-3.svg
    ratio: 21/9
    features:
      - 每行都可以有自己的比例
      - 默认图标是一个对勾 | 用 check-circle-outline | check-circle-outline
      - 也可以换成别的 | 或者图片
  - eyebrow: 第二步
    title: 这一行有 eyebrow
    desc: eyebrow 是标题上方的小标签。
    image: ../../assets/shot-1.svg
    link: ../recipes.md
    link_text: 看场景配方
    features:
      - 用自定义的 link_text 换掉"了解更多"
```

## 翻转整个序列

`reverse: true` 加在**块上**，把第一行的图从右边换到左边，整体镜像。

```homepage-showcase
reverse: true
title: reverse true（整块）
showcase:
  - title: 第一行
    desc: 现在图在左边。
    image: ../../assets/shot-1.svg
  - title: 第二行
    desc: 交替也跟着镜像。
    image: ../../assets/shot-2.svg
```

## 细节

- **`image` 是必填的。** 少一张图会报 `showcase item N needs an image` 并在页面上留下
  错误标记——一行没有图的 showcase 不是 showcase，是一张排版奇怪的卡片。
- `reverse` 有**两个层级**：写在块上翻转整个序列，写在单行上只对调那一行。
  单行的优先。
- 每行自己的 `theme` 只影响那一行，整块也可以有 `theme` 当默认值。
- **空位**：`- blank` 可以在一串行里留一个空档，占位但不画东西。
