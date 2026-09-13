# logos

「他们都在用」那一排。默认是横向一行，也可以排成网格，或者做成无缝走马灯。

```homepage-logos
title: 'style: row（默认）'
caption: 品牌标来自内置的 Simple Icons 集合。
logos:
  - simple/github | GitHub | https://github.com/
  - simple/python | Python | https://www.python.org/
  - simple/docker | Docker | https://www.docker.com/
  - simple/kubernetes | Kubernetes | https://kubernetes.io/
  - simple/rust | Rust | https://www.rust-lang.org/
```

## 属性

| 属性 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `logos` | 列表 | 必填 | 条目列表。别名 `items` `brands` |
| `style` | 关键词 | `row` | `row` / `grid` / `marquee` |
| `colored` | 布尔 | `false` | 图标改用强调色 |
| `caption` | 文本 | — | 上方的一句说明。别名 `note` `text` |
| `size` | 长度 | — | 单个标记的大小，如 `2.4em` |

### `style`

| 取值 | 外观 |
| --- | --- |
| `row` | 横向一行，自动换行 |
| `grid` | 等宽网格，每格居中 |
| `marquee` | 无缝走马灯，鼠标移上去会停 |

```homepage-logos
style: marquee
caption: 'style: marquee —— 无缝滚动，鼠标移上去暂停。'
logos:
  - simple/github | GitHub
  - simple/python | Python
  - simple/docker | Docker
  - simple/kubernetes | Kubernetes
  - simple/rust | Rust
  - simple/go | Go
  - simple/redis | Redis
  - simple/postgresql | PostgreSQL
  - simple/nginx | NGINX
  - simple/react | React
  - simple/svelte | Svelte
  - simple/fastapi | FastAPI
```

```homepage-logos
style: grid
columns: 4
title: 'style: grid + columns 4'
logos:
  - simple/materialdesign | Material
  - simple/markdown | Markdown
  - simple/pypi | PyPI
  - simple/netlify | Netlify
  - simple/vercel | Vercel
  - simple/cloudflare | Cloudflare
  - ../../assets/mark-orbit.svg | 自己的图片
  - simple/sqlite | SQLite
```

## 单条字段

`|` 简写按 **`图标 | 名称 | 链接 | 补充`** 的顺序填：

| 位置 | 字段 | 说明 |
| --- | --- | --- |
| 1 | `icon` | 图标名，**或指向图片的路径**（别名 `image` `img` `src`） |
| 2 | `name` | 品牌名，显示在标记右侧（别名 `title` `text`） |
| 3 | `link` | 链接（别名 `url` `href`） |
| 4 | `desc` | 预留的补充字段 |

```homepage-logos
title: 三种写法
logos:
  - simple/github | 图标名 | https://github.com/
  - ../../assets/mark-orbit.svg | 直接写图片路径
  - name: 用映射写
    image: ../../assets/mark-orbit.svg
    link: https://example.com/
```

## `colored`

默认标记是**低调灰**（配色里最不抢眼的那一档），鼠标移上去才变成强调色——
一排彩色 logo 比正文还吵。`colored: true` 让它一直是强调色。

```homepage-logos
colored: true
caption: colored true —— 标记一直是强调色。
logos:
  - simple/github | GitHub
  - simple/python | Python
  - simple/docker | Docker
  - simple/rust | Rust
```

```homepage-logos
colored: false
caption: colored false（默认）—— 低调灰，鼠标移上去才亮。
logos:
  - simple/github | GitHub
  - simple/python | Python
  - simple/docker | Docker
  - simple/rust | Rust
```

## 细节

- **`colored` 只管我们自己着色的图标标记。** 作者提供的品牌图有自己的颜色，
  这个开关不会去动它——把一张彩色 logo 改成单色是件很意外的事。
- **图片会被裁成圆形，所以请用正方形图片**（非正方形会居中裁切）。
- **走马灯是无缝的**，而且间隙算在周期内。如果你自己改 CSS，注意别给轨道加 `gap`。
- 走马灯里的图片用 `eager` 加载：图片本来就即将滚进视野，用 `lazy` 会让它在
  滚动中途才「啪」地出现。行和网格仍然用 `lazy`。
- 走马灯会**复制一份内容**来实现循环，副本对屏幕阅读器和 Tab 键隐藏——
  键盘用户不需要把每个品牌走两遍。
- 空位：`- blank` 在走马灯里也是空档，而且**两份副本都会留**，
  否则两个周期的间距会不一致、循环时会抖一下。
