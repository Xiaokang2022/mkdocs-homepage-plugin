# 插件选项

```yaml
plugins:
  - homepage:
      assets: true                 # 挂载样式表与脚本
      assets_dir: assets           # 它们在站点里的目录
      tilt: true                   # 卡片倾斜
      tilt_strength: 6             # 倾斜强度（度）
      reveal: auto                 # 滚动进入动画的默认值
      lightbox: true               # 点击图片放大
      count: true                  # 数字滚动累加
      markdown_extension: true     # 自动注册 Markdown 扩展
      strict: false                # 区块写错时直接让构建失败
      css_vars:                    # 注入到 :root 的自定义属性
        --md-home-radius: 0.9em
```

## 全部选项

| 选项 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `assets` | 布尔 | `true` | 是否把 `homepage.css` / `homepage.js` 挂到站点上。关掉的话要自己引 |
| `assets_dir` | 字符串 | `assets` | 这两个文件在站点里的子目录。带 `/`、`..` 的值会被规范化掉 |
| `tilt` | 布尔 | `true` | 卡片是否响应鼠标做 3D 倾斜 |
| `tilt_strength` | 数字 | `6` | 倾斜角度的上限（度）。`0` 等于关掉 |
| `reveal` | 关键词 | `auto` | 滚动进入动画的默认值，见下 |
| `lightbox` | 布尔 | `true` | 点击图片是否放大 |
| `count` | 布尔 | `true` | 数字是否从 0 数上去 |
| `markdown_extension` | 布尔 | `true` | 是否自动注册 Markdown 扩展 |
| `strict` | 布尔 | `false` | `true` 时，区块里的任何警告都直接让构建失败 |
| `css_vars` | 映射 | `{}` | 注入到 `:root` 的自定义属性 |

### `reveal`

| 取值 | 含义 |
| --- | --- |
| `auto` | 只有**列表类**区块（`cards` `features` `stats` `steps` `links` `logos` `testimonials`）依次错峰出现 |
| `off` | 全部静止 |
| `up` `down` `left` `right` `zoom` `fade` | 所有区块都用这一种动画 |

单个区块写 `reveal:` 会覆盖它。

### `strict`

演示站点没开——首页上出现一个虚线错误框，比让整站构建失败更容易发现。
**CI 里应该打开**：`strict: true` 会让「缺少必填项」「theme 写错」这类问题
直接失败，而不是在页面上留一个框。

### `markdown_extension`

正常情况下不用管：插件会自己把 `homepage` 扩展注册进 `markdown_extensions`，
所以 `mkdocs.yml` 里只需要写插件名。只有当你**手动**注册了扩展（想控制优先级）
时才需要关掉它，否则会注册两次。

## CSS 变量

只改变量即可，不必重写选择器。它们都声明在 `:root`，所以 `css_vars` 注入真的生效
（如果声明在 `.md-home` 上，元素自身的声明会赢过继承来的值，注入就没用了）。

```yaml
plugins:
  - homepage:
      css_vars:
        --md-home-radius: 0.9em
        --md-home-gap: 1.1em
```

### 尺寸与圆角

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `--md-home-hue` | `231` | 默认色相（indigo）。改这个等于改所有没有 `theme` 的区块 |
| `--md-home-radius` | `0.6em` | 面板圆角 |
| `--md-home-radius-sm` | `0.35em` | 小圆角：图标底、图片 |
| `--md-home-pad` | `1.2em` | 面板内边距 |

### 栅格

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `--md-home-gap` | `0.9em` | 栅格间距 |
| `--md-home-min` | `13em` | **没写 `columns` 时**单个格子的最小宽度 |
| `--md-home-min-narrow` | `8.5em` | **写了 `columns` 时**的硬底线 |

两个最小宽度是两件事，见[设计约定](index.md)。

### 间距阶梯

| 变量 | 默认 | 用在哪 |
| --- | --- | --- |
| `--md-home-space-1` | `0.4em` | 标题和它自己的描述 |
| `--md-home-space-2` | `0.6em` | 关系很紧的两项 |
| `--md-home-space-3` | `0.9em` | 一个面内部的两组之间；也就是栅格间距 |
| `--md-home-space-4` | `1.2em` | 一块的两部分之间 |
| `--md-home-space-5` | `1.6em` | 区块的标题区，和它的内容之间 |
| `--md-home-space-6` | `2.5em` | 区块与区块之间 |

**这是一条阶梯，不是一个数值集合。** 整套调间距时改这几个变量，
而不是去改某个选择器——否则就会出现两个「看起来一样」的面板对不齐。

### 其他

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `--md-home-ease` | `cubic-bezier(.2,.7,.3,1)` | 所有过渡的缓动函数 |
| `--md-home-icon-size` | `1em` | 图标尺寸，各位置的默认值由组件覆盖 |
| `--md-home-marquee-gap` | — | 走马灯里每个条目两侧的间距 |
| `--md-home-logo-size` | — | 品牌墙标记的大小（也可以写区块的 `size:`） |

## 主题是怎么推导的

只有一个入口：`--md-home-hue`。

```
--md-home-hue
   ├─→ --md-home-accent         强调色
   ├─→ --md-home-tint           浅底（强调色混进主题背景色）
   ├─→ --md-home-line           描边
   ├─→ --md-home-glow           光晕
   └─→ 投影 / 按下态 / 气泡描边
```

区块写 `theme: teal` 时，它只做一件事：**在那一块上重设 `--md-home-hue`**。
所以整块的所有派生颜色会一起变，而且浅色和深色两种方案都不用单独调。

唯一的例外是[单张卡片自己指定颜色](../guide/blocks/cards.md)——那是留给
「品牌色必须精确」的场合的，需要你自己保证对比度。
