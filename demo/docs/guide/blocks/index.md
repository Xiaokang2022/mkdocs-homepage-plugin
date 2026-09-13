# 全部区块

`homepage` 一共 **16 个区块**。每个区块是一段围栏代码块，围栏里放 YAML 属性，
`---` 以下是正文（用页面自己的 Markdown 扩展渲染）。

这份参考一个区块一页，每页都写清：**能填哪些属性、每个属性的类型与默认值、
几种常用写法、以及一眼看去不会注意到的细节**。所有示例都是真的在渲染，不是截图。

```homepage-links
style: cards
columns: 4
links:
  - hero | hero.md | 首屏：标题、图、动作、要点 | view-dashboard-outline
  - cards | cards.md | 卡片墙，支持一卡一栏与单卡配色 | layers-outline
  - showcase | showcase.md | 图文交替的叙事行 | movie-open-outline
  - features | features.md | 无边框特性网格 | shape-outline
  - testimonials | testimonials.md | 引用 / 评价 | format-quote-open
  - logos | logos.md | 品牌墙与无缝走马灯 | simple/github
  - image | image.md | 单张图片，可浮动 | image-outline
  - gallery | gallery.md | 滚动 / 分页 / 网格画册 | view-gallery-outline
  - split | split.md | 多栏图文 | simple/readthedocs
  - text | text.md | 正文段落、面板、折叠 | text-box-outline
  - stats | stats.md | 数字，滚动到可见时计数 | speedometer
  - steps | steps.md | 步骤与时间线 | timeline-outline
  - links | links.md | 链接列表、胶囊、按钮、卡片 | link-variant
  - cta | cta.md | 收尾的行动号召 | rocket-launch-outline
  - anim | anim.md | 动画容器 | auto-fix
  - divider | divider.md | 分隔线 | minus
```

## 区块名可以用别名写

围栏的信息字符串以 `homepage` 开头，后半段是区块名。名字很宽松：**大小写、
连字符、下划线、空格都会被忽略**，而且每个区块都有一串常用别名，
写错一点也能猜到你想干什么。

```markdown
homepage-cards      homepage-card        homepage-grid      homepage-tiles
```

<table>
<tr><th>规范名</th><th>别名</th></tr>
<tr><td><code>hero</code></td><td><code>banner</code> <code>cover</code></td></tr>
<tr><td><code>cards</code></td><td><code>card</code> <code>grid</code> <code>tiles</code></td></tr>
<tr><td><code>showcase</code></td><td><code>sections</code> <code>rows</code> <code>alternating</code> <code>spotlight</code></td></tr>
<tr><td><code>features</code></td><td><code>feature</code> <code>highlights</code></td></tr>
<tr><td><code>testimonials</code></td><td><code>testimonial</code> <code>quotes</code> <code>reviews</code> <code>users</code></td></tr>
<tr><td><code>logos</code></td><td><code>logo</code> <code>brands</code> <code>clients</code> <code>trust</code> <code>sponsors</code></td></tr>
<tr><td><code>image</code></td><td><code>img</code> <code>figure</code> <code>picture</code></td></tr>
<tr><td><code>gallery</code></td><td><code>carousel</code> <code>slider</code> <code>strip</code></td></tr>
<tr><td><code>split</code></td><td><code>columns</code> <code>cols</code> <code>side</code></td></tr>
<tr><td><code>text</code></td><td><code>prose</code> <code>paragraph</code> <code>note</code></td></tr>
<tr><td><code>stats</code></td><td><code>numbers</code> <code>metrics</code> <code>counters</code></td></tr>
<tr><td><code>steps</code></td><td><code>timeline</code></td></tr>
<tr><td><code>links</code></td><td><code>link</code> <code>quicklinks</code> <code>shortcuts</code></td></tr>
<tr><td><code>cta</code></td><td><code>callout</code> <code>promo</code> <code>insiders</code> <code>sponsor</code></td></tr>
<tr><td><code>anim</code></td><td><code>animate</code> <code>animation</code> <code>motion</code></td></tr>
<tr><td><code>divider</code></td><td><code>hr</code> <code>rule</code> <code>space</code> <code>spacer</code></td></tr>
</table>

## 每个区块都认识的属性

这些是**通用属性**，16 个区块全都支持。完整解释见[语法](../syntax.md)：
`theme`、`class`、`id`、`width`、`align`、`reveal`、`tilt`、`background`、
`pattern`、`gradient`、`gap`、`columns`、`min_cols`、`ratio`。

## 每个可重复的列表都能留空

`cards`、`features`、`stats`、`steps`、`links`、`testimonials`、`logos`、
`showcase`、`gallery` 都是「一串条目」。任何一个位置都可以是空的：

```yaml
cards:
  - 第一张
  -             # 空位，占位置但不画东西
  - 第三张
```

四种写法等价：`-`、`- {}`、`- empty`、`- blank`（还有 `gap` / `spacer`）。
**列数不变**：4 列里只放 3 张卡，卡片宽度仍然是四列的宽度。

## 该用哪个区块？

| 你想做的事 | 用哪个 |
| --- | --- |
| 页面最上面那一屏 | [`hero`](hero.md) |
| 一排等大的入口 / 功能 | [`cards`](cards.md) |
| **卡片占一边、文字写另一边** | [`cards`](cards.md) 的 `layout: rows` |
| 一串「图 + 说明」交替往下走 | [`showcase`](showcase.md) |
| 密集的小功能点，不要卡片框 | [`features`](features.md) |
| 用户评价 | [`testimonials`](testimonials.md) |
| 「他们都在用」 | [`logos`](logos.md) |
| 一张图，要配说明或浮动在文字边上 | [`image`](image.md) |
| 多张图 | [`gallery`](gallery.md) |
| 左右两栏不同的内容 | [`split`](split.md) |
| 就是一段正文，但想要点样式 | [`text`](text.md) |
| 几个数字 | [`stats`](stats.md) |
| 有先后顺序的几步 | [`steps`](steps.md) |
| 一堆链接 | [`links`](links.md) |
| 页面最后的「现在就开始」 | [`cta`](cta.md) |
| 一句会动的标语 | [`anim`](anim.md) |
| 换口气 | [`divider`](divider.md) |

组合起来的常见整页结构，见[场景配方](../recipes.md)。
