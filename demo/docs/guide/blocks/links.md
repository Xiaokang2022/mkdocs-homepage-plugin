# links

一堆链接。四种外观，从最密的列表到最大的按钮。

```homepage-links
style: list
title: 'style: list（默认）'
links:
  - 指南 | ../index.md | 从零开始 | book-open-page-variant-outline
  - 语法 | ../syntax.md | 属性与正文的分工 | text-box-outline
  - 设计约定 | ../../reference/index.md | 为什么长这样 | palette-outline
```

## 属性

| 属性 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `links` | 列表 | 必填 | 条目列表。别名 `items` |
| `style` | 关键词 | `list` | `list` / `chips` / `buttons` / `cards` |
| `columns` | 整数 | 自动 | 列数（`chips` / `buttons` / `cards` 都是栅格） |
| `min_cols` | 长度 | `13em` | 单条最小宽度 |

### 四种 `style`

#### list

```homepage-links
style: list
links:
  - 一行一条 | ../index.md | 右侧一个箭头 | arrow-right
  - 描述在标题下方 | ../syntax.md | 信息量最大的一种 | text-box-outline
  - 没有描述也可以 | ../recipes.md
```

#### chips

```homepage-links
style: chips
columns: 3
links:
  - 胶囊 | ../index.md | | layers-outline
  - 紧凑 | ../syntax.md | | text-box-outline
  - 适合标签云 | ../recipes.md | | shape-outline
  - 没有描述 | ../../reference/index.md
  - simple/github | https://github.com/
```

#### buttons

```homepage-links
style: buttons
columns: 3
links:
  - 按钮 | ../index.md | 主入口 | rocket-launch-outline
  - 次要入口 | ../syntax.md | | text-box-outline
  - 第三个 | ../recipes.md | | book-open-page-variant-outline
```

#### cards

```homepage-links
style: cards
columns: 2
links:
  - 卡片式 | ../index.md | 图标 + 标题 + 描述 + 箭头 | layers-outline
  - 也可以换色 | ../syntax.md | 每一条自己的 theme | text-box-outline
  - 三 | ../recipes.md | 描述 | palette-outline
  - 四 | ../../reference/index.md | 描述 | puzzle-outline
```

## 单条字段

`|` 简写按 **`文字 | 链接 | 描述 | 图标`** 的顺序填：

| 位置 | 字段 | 说明 |
| --- | --- | --- |
| 1 | `text` | 文字（别名 `title` `label`） |
| 2 | `link` | 链接（别名 `url` `href`）；**省略就变成不可点的 `span`** |
| 3 | `desc` | 描述（别名 `description` `subtitle`） |
| 4 | `icon` | 图标名或图片路径 |

## 空位

4 列只放 3 条时，最后那个位置留空——**尺寸仍然按 4 列算**：

```homepage-links
style: cards
columns: 4
title: 4 列里的 3 条
links:
  - 一 | ../index.md | 描述 | layers-outline
  - 二 | ../syntax.md | 描述 | text-box-outline
  - 三 | ../recipes.md | 描述 | shape-outline
  -
```

## 细节

- **`list` 和 `cards` 会在右侧加一个箭头**，因为这两种样式「点进去」的暗示
  最强；`chips` 和 `buttons` 不加，它们本身就是可点的形状。
- 描述在 `chips` 里会被忽略——胶囊靠不住两行文字。
- 没有 `link` 的条目会渲染成 `span`（不是 `<a>`），所以它不会出现在 Tab 顺序里，
  也不会被读成链接。
- [`cards`](cards.md) 区块和这里 `style: cards` 的区别：卡片区有封面图、标签、
  页脚、`span`、整卡比例；`links` 的卡片是「一条可点的链接」长成了卡片的样子。
