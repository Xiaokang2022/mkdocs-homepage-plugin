# steps

有先后顺序的几步。默认竖排带序号和一条连接线，也可以横排。

```homepage-steps
steps:
  - 安装 | ../index.md | 一条命令装好 | download-outline
  - 编写 | ../syntax.md | 围栏里写属性 | text-box-outline
  - 预览 | ../../reference/index.md | 本地实时刷新 | console
```

## 属性

| 属性 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `steps` | 列表 | 必填 | 步骤列表。别名 `items` |
| `direction` | 关键词 | `vertical` | `vertical` / `horizontal` |
| `numbered` | 布尔 | `true` | 自动编号 |

## 单条字段

`|` 简写按 **`标题 | 链接 | 描述 | 图标`** 的顺序填（和其他链接类区块一致）：

| 位置 | 字段 | 说明 |
| --- | --- | --- |
| 1 | `title` | 标题，可加链接。别名 `heading` |
| 2 | `link` | 链接。别名 `url` `href` |
| 3 | `desc` | 描述。别名 `description` `text` |
| 4 | `icon` | 图标名或图片路径——**写了图标就不显示序号** |

```homepage-steps
direction: horizontal
title: direction horizontal
steps:
  - 第一步 | | 横排 | simple/github
  - 第二步 | | 序号让位给图标 | simple/python
  - 第三步 | | 窄屏会自动叠成一列 | simple/docker
```

## 用图标代替序号

只要某一条写了 `icon`，它就用图标当标记；没写的仍然用序号。
所以**混用是可以的**，只是要留意看起来是否整齐：

```homepage-steps
title: 图标代替序号
steps:
  - 写代码 | | 有图标就用图标 | language-python
  - 打包 | | | package-variant-closed
  - 部署 | | 这一条没有图标，所以显示序号 3
```

```homepage-steps
numbered: false
title: numbered false
steps:
  - 没有序号 | | 只剩左侧那条线
  - 适合当时间线用 | | 比如发布历史
  - 第三条 | | |
```

## 细节

- **序号是渲染时数出来的**，而且**空位也算一位**——所以在一串步骤里插一个
  `- blank`，后面的序号会跟着往后挪，视觉顺序和编号始终一致。
- 竖排有一条连接线，横排没有；横排在窄屏会自动叠回竖排。
- `direction` 写别的值会回退到 `vertical`，不会报错。
- 步骤标题可以单独带链接（`link:`），这时只有标题可点，不会整条变链接。
