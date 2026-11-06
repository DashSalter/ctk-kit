# ctk-kit

> 基于 CustomTkinter 的 Python 桌面 UI 组件库：自绘控件、运行时换色、Windows 毛玻璃。

![按钮页](assets/buttons.png)

ctk-kit 不是又一层 ttk 样式表，而是一套**自己做控件**的组件库：按钮、输入框、下拉、分段选择、开关、勾选、单选、滑块、表格、时间选择、图片查看、通知、右键菜单……都按同一套设计令牌绘制，换色、换圆角、换间距只改令牌。

## 为什么不用原生 Tkinter / ttk

| 问题 | 原生 Tkinter | ctk-kit |
| --- | --- | --- |
| 控件外观 | 系统原生样式，改不动 | 全部自绘，圆角、悬停、禁用态统一 |
| 换主题 | 逐控件 `configure` | `theming.apply_palette()` 全窗实时生效 |
| 深色模式 | 自己给每个控件传两套颜色 | 令牌只有一套，控件按令牌取色 |
| 窗口质感 | 方角、白底 | Windows 11 毛玻璃 / Mica / Acrylic |

## 安装

```bash
pip install ctk-kit
```

依赖只有 `customtkinter` 与 `Pillow`；毛玻璃部分依赖 Windows 11 的 DWM，其他平台自动退化成纯色底。

## 最小示例

```python
import ctk_kit as ctk

app = ctk.App("我的工具", size=(960, 600))

ctk.PrimaryButton(app, "保存", command=lambda: print("saved")).pack(padx=24, pady=16)
ctk.SecondaryButton(app, "取消", command=app.destroy).pack(padx=24)

app.mainloop()
```

## 切换主题

主题用 `set_theme()` 换，颜色可以单独改：

```python
app.set_theme("dark")                        # frosted / dark / acrylic / mica
app.set_theme("acrylic", color="#20222a")    # 顺便指定底色
app.set_theme_color("#2b2b3a")               # 只改底色，主题不变
```

| 主题 | 效果 | 默认底色 |
|---|---|---|
| `mica` | 黑灰，只糊壁纸（默认） | `#1A1A1A` |
| `frosted` | 毛玻璃：透出桌面，带模糊 | `#181A20` |
| `dark` | 深空：纯深色实底，不透桌面 | `#1A1A1A` |
| `acrylic` | 黑色偏蓝，Win10 亚克力 | `#1A1A1A` |

窗口默认就是 `mica`；主题名不区分大小写，中文别名「毛玻璃」「深空」也可以。
`app.get_theme()` / `app.get_theme_color()` 读当前值；名字写错会抛 `ValueError`。

## 窗口外观

`set_theme` 之外，每一项也都有单独的方法，全部返回 `App`，可以连写：

```python
app.set_window_corners(2).set_border_color("#3b3e4a").set_opacity(1.0)
```

| 方法 | 作用 | 取值 |
|---|---|---|
| `set_glass_kind(kind)` | DWM 合成方式 | `accent` / `acrylic` / `system` / `mica` |
| `set_glass_state(state)` | AccentState | `0` 关 / `2` 透明 / `3` 模糊 / `4` 亚克力 |
| `set_system_backdrop(value)` | 系统背板类型 | `0` 不设 / `1` 无 / `2` Mica / `3` 亚克力 / `4` 标签 |
| `set_tint("#RRGGBB")` | 玻璃 tint 底色 | 颜色 |
| `set_tint_alpha(0–255)` | tint 压暗程度 | 越高越黑 |
| `set_window_corners(value)` | 窗口圆角 | `0` 默认 / `1` 不圆 / `2` 圆 / `3` 小圆 |
| `set_border_color(color)` | 窗口边框 | `"#RRGGBB"`；`None` = 不要边框 |
| `set_caption_color(color)` | 标题栏颜色 | `"#RRGGBB"`；`None` = 交还 DWM（玻璃能糊上去） |
| `set_opacity(0.1–1.0)` | 整体透明度 | 低于 1 会变 layered，玻璃失效 |
| `set_veil(color)` | 透明键色 | 一般保持 `#000000` |
| `set_extend(bool)` | 客户区延伸到整个窗口 | `True` / `False` |
| `set_titlebar_glass(bool)` | 标题栏是否交还 DWM | `True` / `False` |
| `set_glass_dark(bool)` | 标题栏是否用深色 | `True` / `False` |
| `set_wca(value)` | 合成属性号 | 默认 `19` |
| `show_titlebar_icon(bool)` | 显示 / 隐藏标题栏图标 | `True` / `False` |
| `show_titlebar_title(bool)` | 显示 / 隐藏标题文字 | `True` / `False` |
| `hide_frame_border(bool)` | 去掉 1px 系统边框 | Win11 22H2+ |
| `set_transitions(bool)` | 窗口过渡动画 | `False` 关掉 |

读当前状态用 `app.glass_options()`、`app.titlebar_items()`、`app.window_debug()`；
原来那种一次传多个关键字的 `app.set_glass_options(kind=..., alpha=...)` 也还能用。

## 文档约定

- 每个组件页按 **构造函数 → 参数表 → 方法表 → 示例** 组织；
- 参数表里的「默认」一列，写的是 ctk-kit 覆盖后的值，不是 CustomTkinter 的原始默认值；
- 所有示例都可以直接复制运行，窗口用 `ctk.App` 建。

## 开始阅读

- [按钮](components/buttons.md)

## 项目地址

- GitHub：<https://github.com/DashSalter/ctk-kit>
- Gitee：<https://gitee.com/kuangjianke/ctk-kit>
- PyPI：<https://pypi.org/project/ctk-kit/>
