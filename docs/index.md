# ctk-kit

> 一套自己做控件的 Python 桌面 UI 组件库：统一设计令牌、运行时换色、Windows 11 毛玻璃，
> 以及一套为「几十个页面也不卡」设计的页面体系。

![按钮页](assets/guide-buttons.png){ loading=lazy }

## 它解决什么

用 Tkinter 写工具的人大多卡在同一处：**界面能跑，但拿不出手**。

原生 `ttk` 的按钮是系统画的，圆角、悬停、禁用态都改不动；深色模式要自己给每个控件
传两套颜色；窗口是白底方角；页面一多，切页就整窗白一下。

ctk-kit 的做法是**不用 ttk，所有控件自己用 Canvas 画**，颜色、圆角、间距全部来自一套
设计令牌。于是「换个配色」不是挨个 `configure`，而是改一次令牌、全窗即时生效；
「加个页面」也不是复制粘贴，而是丢一个页面类进去，框架负责构建、调度与回收。

## 特色

### 一套令牌，全部自绘

按钮、输入框、下拉、分段、开关、勾选、单选、滑块、表格、日期时间、图片、通知、右键菜单……
用的是同一份 `tokens`。改一处 `COLOR_ACTIVE`，所有控件同时变，连不可见页面也会在切回来时
自动追平，不需要重启。

### 换色只重画看得见的那一页

`theming.apply_palette()` 改色时，会跳过当前没有显示的页面，只重画屏幕上这一页，并把这次
改动的「旧色 → 新色」记进一张累计表；下次切到某个落后页面时，再按累计表补画一次。

示例程序 18 个页面、3000+ 控件实测：

| 场景 | 改色耗时 |
| --- | --- |
| 整棵树全刷 | 约 740 ms |
| 只刷可见页 + 切页补刷 | 约 134 ms |

### 首次切页不再整窗冻结

页面不是一次性建完的。每页只先出页头和第一张卡，剩下的按 12 ms 时间片分帧建；
建完之前界面可以正常点、正常滚。相邻页会在空闲时按顺序预建，所以第二次进去通常是**直接显示**。

示例程序里最重的一页（512 个控件）：

| | 切过去到能看见 |
| --- | --- |
| 改前 | 1.7 s 全窗冻结 |
| 现在 | 首帧 190–440 ms，其余在后台分帧补齐 |

### 拖动窗口时先丢掉看不见的页面

窗口一改尺寸，所有挂着布局的页面都要跟着重排，页面越多越卡。ctk-kit 在拖拽边框开始时
就把非当前页从布局里摘掉（内容直接销毁，省内存），松手后再按需重建。拖完之后切回那些页面
是**重新构建**，不是从缓存读——这是刻意的取舍：宁可慢一次，也不要拖拽时卡。

### 关闭窗口不再等两秒

`destroy()` 不再让 tkinter 逐个调用 3000 多个控件的 Python `destroy()`，而是先藏窗口、
再让 Tcl 一次性拆整棵树。示例程序全建 3185 个控件时，关闭耗时从约 2.5 s 降到 **0.36 s**。

### Windows 11 的窗口质感

Mica、亚克力、毛玻璃、纯色深底四种外观，标题栏可以交还给 DWM 让玻璃糊上去；
窗口圆角、边框色、标题栏图标与文字的显隐都能单独关。非 Windows 平台自动退化成纯色底，
不会报错。

### 只读是一等公民

输入框、搜索框、路径框、步进器、下拉、日期、时间、多行文本都支持 `readonly=`，
只读时**键盘输入被拒、下拉点不开、浏览按钮置灰**，但 `set_value()` 这类程序写入仍然有效。
需要临时写一次？`with entry.unlocked():` 就够。

## 为什么不用原生 Tkinter / ttk

| 问题 | 原生 Tkinter | ctk-kit |
| --- | --- | --- |
| 控件外观 | 系统原生样式，改不动 | 全部自绘，圆角 / 悬停 / 禁用态统一 |
| 换主题 | 逐控件 `configure` | 改令牌，全窗实时生效 |
| 深色模式 | 每个控件传两套颜色 | 令牌只有一套，控件按令牌取色 |
| 窗口质感 | 方角、白底 | Mica / 亚克力 / 毛玻璃 |
| 页面切换 | 自己销毁重建，会白一下 | 分帧构建 + 预建 + 不冻结 |
| 组件数量 | 要自己攒 | 40+ 个开箱即用 |

## 安装

```bash
pip install ctk-kit
```

依赖只有 `customtkinter` 与 `Pillow`；毛玻璃相关能力依赖 Windows 11 的 DWM，
其他平台自动降级。

## 最小示例

```python
import ctk_kit as ctk

app = ctk.App("我的工具", size=(960, 600))

ctk.PrimaryButton(app, "保存", command=lambda: print("saved")).pack(padx=24, pady=16)
ctk.SecondaryButton(app, "取消", command=app.destroy).pack(padx=24)

app.mainloop()
```

## 三种常见外观

```python
app.set_theme("mica")       # 黑灰，只把壁纸糊进标题栏（默认）
app.set_theme("frosted")    # 毛玻璃：透出桌面并模糊
app.set_theme("acrylic")    # 亚克力：黑里偏蓝
```

主题名不区分大小写，`dark` / `深空` 也认；`app.get_theme()` 读当前值。

## 文档

每个组件的构造参数、常用方法和可运行示例都在组件页里；参数表中的「默认值」写的是
ctk-kit 覆盖后的值，不是 CustomTkinter 的原始默认值。

- [按钮](components/buttons.md) · [输入](components/inputs.md) · [下拉选择](components/dropdowns.md)
- [选择控件](components/choices.md) · [日期时间](components/datetime.md) · [对话框](components/dialogs.md)
- [表格与列表](components/table.md) · [导航](components/navigation.md) · [媒体与颜色](components/media.md)
- [反馈](components/feedback.md) · [文件](components/files.md) · [杂项](components/misc.md)
- [布局](components/layout.md) · [窗口](components/app.md) · [页面体系](components/pages.md)

## 项目地址

- GitHub：<https://github.com/DashSalter/ctk-kit>
- Gitee：<https://gitee.com/kuangjianke/ctk-kit>
- PyPI：<https://pypi.org/project/ctk-kit/>
