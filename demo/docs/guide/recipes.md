# 场景配方

具体的「我想做这样一个页面」。每一种都说清楚**为什么这样组合**，
以及哪里容易写错。

## 一、项目首页（最常见）

顺序是：一句话 → 一排入口 → 为什么选它 → 收尾。

```homepage-hero
eyebrow: 一个 MkDocs 插件
title: 项目名
subtitle: 一句话说清它是做什么的，以及为什么值得一试。
image: ../assets/hero.svg
actions:
  - 快速开始 | index.md | primary | rocket-launch-outline
  - GitHub | https://github.com/ | | simple/github
highlights:
  - 16 | 区块类型
  - 95 | 内置图标
  - 0 | 前端依赖
```

```homepage-cards
columns: 3
title: 三条最重要的入口
cards:
  - title: 指南
    icon: book-open-page-variant-outline
    desc: 从安装到写完第一个区块
    link: index.md
  - title: 全部区块
    icon: layers-outline
    desc: 一个区块一页的完整参考
    link: blocks/index.md
  - title: 场景配方
    icon: compass-outline
    desc: 想做一个什么页面，从这里找
    link: recipes.md
```

```homepage-features
columns: 3
title: 为什么选它
icon_style: soft
features:
  - title: 纯 Markdown
    icon: text-box-outline
    desc: 不写 HTML，也不改主题
  - title: 跟随主题
    icon: palette-outline
    desc: 颜色从主题推导，明暗都对
  - title: 零依赖
    icon: lightning-bolt-outline
    desc: 一个样式表、一个脚本
```

**为什么这样组合**：`hero` 负责第一印象，`cards` 三条给出「下一步去哪」，
`features` 用没有卡片框的形式说理由——如果要说的理由超过四条，
用 `features`；只有三条、每条都想让人点进去，用 `cards`。

## 二、产品/功能介绍页

用 `showcase` 串起来，每个能力一段。

```homepage-showcase
title: 三个能力，三段话
showcase:
  - eyebrow: 第一步
    title: 写内容
    desc: 围栏里放 YAML 属性，`---` 以下写 Markdown。
    image: ../assets/shot-1.svg
    features:
      - 属性和正文分工明确
      - 正文用站点自己的扩展
  - title: 调外观
    desc: 只声明一个色相，其余颜色推导出来。
    image: ../assets/shot-2.svg
    theme: cyan
    link: ../reference/index.md
    link_text: 看设计约定
  - title: 发布
    desc: 还是 `mkdocs build`，没有额外步骤。
    image: ../assets/shot-3.svg
```

**为什么用 `showcase` 而不是 `features`**：`features` 是一排并列的短条目，
适合「六条特性」；`showcase` 一行一个主张配一张图，适合**有先后**、
每一条都值得展开讲的叙事。判断方法：能不能给每条配一张图，能就用 `showcase`。

## 三、「他们都在用」+ 数据

```homepage-logos
style: marquee
colored: false
caption: 已经在用
logos:
  - simple/github | GitHub
  - simple/python | Python
  - simple/docker | Docker
  - simple/kubernetes | Kubernetes
  - simple/rust | Rust
  - simple/go | Go
  - simple/redis | Redis
  - simple/nginx | NGINX
```

```homepage-stats
columns: 4
stats:
  - 16 | 区块类型
  - 95 | 内置图标
  - 4.8 | 平均评分 | star-outline
  - 0 | 前端依赖
```

**为什么放在一起**：品牌墙是「别人信」，数字是「有多大」。两者都短，
放在一段正文的两侧正好。

!!! tip "品牌墙的默认色是灰的"
    这是刻意的：一排彩色 logo 比正文还吵。`colored: true` 让它一直是强调色，
    适合品牌标本身就很淡的时候。**图片不受这个开关影响**——作者提供的
    品牌图有自己的配色。

## 四、图文并茂的长文

`split` 分成「短栏 + 长栏」，短栏 `sticky` 跟着滚。

```homepage-split
ratio: 1 2
sticky: true
title: 一个跟着滚的小栏目
---
### 本页内容

- 第一节
- 第二节
- 第三节

===

### 第一节

长文用 `split` 比堆一连串 `text` 好：左边那栏会一直停在视野里，
读者随时知道自己在哪。

### 第二节

右边这一栏是完整的 Markdown 容器，标题层级和页面正文一致。

### 第三节

手机上会自动叠成一栏，`sticky` 自动失效。
```

**为什么 `sticky` 只作用于第一栏**：反过来（长的在左、短的在右）会让短的
先滚走，那就不叫「跟随」了。

## 五、步骤 / 落地页

```homepage-steps
direction: horizontal
title: 三步开始
steps:
  - 安装 | index.md | pip install | download-outline
  - 启用 | syntax.md | 加一行 plugins | tools
  - 写内容 | blocks/index.md | 围栏代码块 | text-box-outline
```

```homepage-cta
gradient: true
pattern: rays
title: 现在就可以写第一块内容
actions:
  - 开始使用 | ../index.md | primary | rocket-launch-outline
  - 全部区块 | blocks/index.md
note: 不需要任何主题覆盖文件。
```

## 六、评价区

```homepage-testimonials
columns: 3
title: 三个人说
style: cards
testimonials:
  - quote: 写法就是文档本身，改文案不用先找模板。
    name: 林一
    role: 文档维护者
    avatar: ../assets/avatar-1.svg
  - quote: 颜色从一个色相推导，深色模式基本不用调。
    name: 赵二
    role: 前端工程师
    avatar: ../assets/avatar-2.svg
    theme: cyan
  - quote: 空位和列数的行为终于是可预期的。
    name: 王三
    role: 设计
    avatar: ../assets/avatar-3.svg
    theme: teal
```

**为什么用 `style: cards` 而不是 `quote`**：三条并排时卡片能给每条一个边界；
一条独占一行时用 `quote`（只有一根竖线）更轻。

## 七、FAQ

用 `text` + `collapsible` 堆成一串。折叠用原生 `<details>`，
不需要 JavaScript。

```homepage-text
collapsible: true
summary: 需要改主题模板吗？
panel: true
---
不需要。所有内容都渲染成 HTML 塞进页面正文，样式由插件自己的样式表提供。
```

```homepage-text
collapsible: true
summary: 能用在非 Material 主题上吗？
panel: true
---
能渲染，但配色和字号是按 mkdocs-material 的变量体系写的，其他主题下
可能不好看。
```

```homepage-text
collapsible: true
summary: 首页必须是一个单独的文件吗？
panel: true
---
不是。任何页面里都可以写这些围栏代码块，首页只是最常用的地方。
```

## 八、一卡一栏的「功能清单」

每条功能都想要一段说明时，用 `cards` + `layout: rows`：
左边是卡片（图标 + 标题），右边是正文。

```homepage-cards
layout: rows
title: 每条功能都配一段说明
cards:
  - title: 图标位可以放图片
    icon: image-outline
    desc: 同一个键
    body: |
      所有画图标的位置，`icon:` 写图片路径就变成**圆形图片**，保留原色。

      用扩展名区分：`icon: rocket-launch-outline` 是字形，
      `icon: assets/logo.svg` 是文件。
  - title: 留空是合法的
    icon: shape-outline
    desc: 空位占位置
    body: |
      任何可重复的列表都能留空，而且**尺寸按列数算**：
      4 列里放 3 张卡，卡片仍然是四列的宽度。
  - title: 不给说明的行
    icon: minus
    desc: 右栏会留空，卡片宽度不变
```

!!! tip "`body` 不写时右栏仍然保留"
    这正是**几行对得齐**的原因。如果右栏在有内容时才出现，
    卡片宽度会在行与行之间跳来跳去。

## 九、页脚前的一句

```homepage-anim
effect: gradient
title: 一句会动的话
---
纯 CSS，不依赖任何框架。
```

```homepage-divider
style: gradient
text: 或者用一条线换口气
```

## 十、深色模式专用配色

默认情况下颜色从 `theme` 推导，两种模式都好看。**只有当设计有硬性要求时**
才给单张卡片指定颜色：

```homepage-cards
columns: 2
title: 单卡配色
cards:
  - title: 只写 bg
    desc: 浅色与深色都换成它
    bg: '#eef1ff'
    glow: '#4f6bed'
  - title: 只写 bg_dark
    desc: 只有深色模式变
    bg_dark: '#161a2b'
    glow_dark: '#8fa4ff'
```

!!! warning "先试 `theme`"
    单卡配色是留给「品牌色必须精确」的场合的，因为它需要你自己保证
    两种模式下的对比度。改色相用 `theme` 就够了，而且是免费的正确。

## 组合时注意什么

| 注意 | 原因 |
| --- | --- |
| **一页只有一个 `hero`** | 它是「第一屏」，第二个就不叫第一屏了 |
| **一页只有一个 `cta`** | 它是「最后一句」 |
| **相邻的区块换一种形状** | 连续三个 `cards` 会变成一堵墙；中间插一个 `features` 或 `divider` |
| **`columns` 不要越写越大** | 4 列在宽屏是上限；5 列以上卡片会太窄放不下标题 |
| **错峰动画一整页是默认开的** | 列表类区块会自动依次出现；如果某块想立刻出现，写 `reveal: false` |
