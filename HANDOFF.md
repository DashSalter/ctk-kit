# ctk-kit 交接（2026-11-04）

## 项目

`F:\ctk-ui-kit` —— Python + CustomTkinter 的 UI 库 ctk-kit 0.9.2，示例入口
`examples/basics/window.py`（`DemoApp`，左侧导航切页）。

当前分支 `main`，最后一次提交 `9b3a595`「0.9.2：Dialog 改 Canvas 自绘，浮层毛玻璃」。
工作区有一批**未提交**改动（见文末清单）。

## 本轮做完的：系统 acrylic（Win11 玻璃）

### 新增 `ctk_kit/win32.py`（纯 ctypes，不依赖 pywinstyles）

- `enable_acrylic(window, *, tint=None, dark=True) -> bool`
- `acrylic_window(window, *, tint=None, corners=True, focus=True) -> bool`
  —— 刷黑底 + 补 `WS_THICKFRAME` + `SetWindowPos(FRAMECHANGED)` + accent +
  `ExtendFrameIntoClientArea` + DWM 圆角 + `DwmFlush` + 原样 `SetWindowPos` 重合成 + `focus_force`
- `set_widget_opacity(widget, value, color=None) -> bool`（只对 `CTkFrame` 这类子 HWND 有效，
  对 `tk.Canvas` 无效）
- 关键常量（**抄错就完全不生效**）：
  - `WCA_ACCENT_POLICY = 30`（不是 19）
  - `ACCENT_ENABLE_BLURBEHIND = 3`（`4` 在 Win11 已失效）
  - `DWMWA_WINDOW_CORNER_PREFERENCE = 33`、`DWMWCP_ROUND = 2`
  - `tint` 非 None 时**不要**设 `DWMWA_SYSTEMBACKDROP_TYPE(38)`，否则系统背板覆盖 tint，窗口变亮

### 接进组件

- `Popover(..., acrylic=False, acrylic_tint=0xCC201A18)`
  —— `show()` 里 acrylic 时窗口与卡片纯黑、不建 `_backdrop`、跳过 `_apply_backdrop()` 与
  `_round_corners()`，显示后调 `acrylic_window()`；`_start_refresh()` 提前返回
- `Dialog(..., backdrop="acrylic")`
  —— `_build_acrylic()`：黑窗口 + 黑 veil（`CTkFrame`）+ `tk.Label` 图标 + 透明 `CTkLabel` 文字 +
  原生 `CTkButton`；`_apply_backdrop()` / `_start_refresh()` 在 acrylic 下直接返回
- `alert` / `confirm` / `prompt` 加 `**kwargs` 透传，可直接 `confirm(..., backdrop="acrylic")`

### 示例

- 「组件」页：`extras_page.py` 的「系统玻璃」按钮 → `Popover(acrylic=True)`
- 「弹窗」页：`dialog_page.py` 的「系统玻璃」按钮 → `_show_acrylic()` → `confirm(..., backdrop="acrylic")`

### 可跑 demo

- `acrylic_demo.py` —— 彩条背景 + 滑块调浓淡 + 勾选去标题栏
- `acrylic_dialog_demo.py` —— 完整弹窗（用户确认这个效果没问题）
- `tests/dev/py-window-styles-main/` 是 pywinstyles 1.8 源码（**没有 pip 安装**）

## 已经验证过的结论（别重复踩）

1. **Win11 系统 acrylic 只在窗口激活时模糊**，失焦会变成纯灰。这是 DWM 行为，没有公开 API 关掉。
   模态浮层（`grab_set`）能保持激活，所以能用；Toast 不抢焦点，所以不适合。
2. `overrideredirect(True)` 的窗口是 `WS_POPUP`，必须补 `WS_THICKFRAME` + `SetWindowPos(SWP_FRAMECHANGED)`，
   DWM 才会把它当玻璃窗口；不必加回标题栏。
3. 只要窗口设过 `attributes("-alpha", ...)`，它就会变成 layered，**系统玻璃被摘掉**。
   Dialog 原来的淡入动画正是因此变灰，现在 acrylic 模式下不做动画、不碰 `-alpha`。
4. 只 `update_idletasks()` 不够，必须 `update()` 让窗口真正映射，玻璃才挂得上。
5. `set_widget_opacity(veil, x)` 会把玻璃一起稀释成灰，**不要对 veil 用**。
6. veil 必须是**纯黑**；非黑时 `CTkFrame` 会画自己的实色块，在玻璃上形成横条。
7. `tk.Canvas` 即使标成 layered 也不参与 DWM 合成 —— 所以 canvas 版 Dialog 套不了 acrylic。
8. **GDI 抓不到 acrylic 窗口的内容**：`ImageGrab.grab()` 和 `PrintWindow(PW_RENDERFULLCONTENT)`
   抓出来都是全黑，因为内容由 DWM 直接合成。视觉只能靠肉眼验收，不要浪费时间写截图脚本。
9. `WS_THICKFRAME` 带来的客户区收缩只在 **Tk 的宽度方向**需要补偿（见上面第 1 条），
   高度方向 Tk 自己算对了；`client_frame_inset()` 用 `AdjustWindowRectEx` 探针拿差值，
   125% 缩放下返回 `(16, 16)`。
10. Win11 会给 `WS_THICKFRAME` 窗口画 1px 边框，用 `DWMWA_BORDER_COLOR(34) =
    DWMWA_COLOR_NONE` 去掉；不关掉的话，窗口获得焦点的瞬间会闪一条浅色横线。

## 已解决（2026-11-05）

### 1. `Dialog(backdrop="acrylic")` 首次打开按钮被压 —— 已修

**根因跟布局时序无关，是客户区被系统边框吃掉了。** `acrylic_window()` 给
`overrideredirect` 的窗口补 `WS_THICKFRAME` 之后，系统多出一圈可缩放边框，客户区比
外框小一圈（125% 缩放下横竖各 16px）。Tk 的 `geometry()` 仍按「外框 = 客户区」算，而
且实测 Tk 只在高度方向补了这圈边框：

```
client_w = round(W * scaling) - 16
client_h = round(H * scaling)
outer_h  = client_h + 16
```

所以外框一直是对的 (490×252)，被吃掉的是客户区 (474×236)；纵向 `pack` 的按钮排在最后，
就被裁成「只露一截」。拖动窗口后系统重算非客户区，看起来就恢复了——和 Tk 的布局时机
没有关系。

**修法**（`ctk_kit/dialog.py` 的 `_apply_geometry()`）：

1. acrylic 时先用 `client_frame_inset()`（`AdjustWindowRectEx` 探针，125% 下得 16）把
   **宽度**加上差值，再交给 `scaled_geometry()`——让 Tk 自己算出正确的客户区；高度不用
   补，Tk 已经补过了。
2. 传 `settle=True` 时，`update_idletasks()` 之后再用 `set_client_rect()` 按客户区尺寸
   `SetWindowPos` 兜底，消掉 ±1px 的取整误差（`_place_over()` 走这条）。
3. 拖动跟手的 `_reposition()` 传 `settle=False`，省掉每帧的空闲等待。

**关键坑**：必须按「目标客户区」倒推，不能按外框硬撑。也**不能**先按外框设好再
`SetWindowPos` 撑大——那会在窗口已经可见时缩一帧，露出玻璃边闪一下。

### 2. 打开瞬间底部闪一条白条 —— 已修

两个来源一起处理：

- Win11 会给带 `WS_THICKFRAME` 的窗口画一圈 1px 系统边框，窗口拿到焦点时亮成浅色，
  横贯窗宽。`enable_acrylic()` 里用 `DWMWA_BORDER_COLOR(34) = DWMWA_COLOR_NONE`
  (`0xFFFFFFFE`) 关掉（22H2 之前不支持这个属性，调用失败静默，无副作用）。
- `_build_acrylic()` 的 veil 原来 `padx=1, pady=1`，那一圈露出来的是玻璃；改成铺满客户区。
- `_refresh_acrylic()` 不再调 `_place_over()`：窗口已经可见时重设 `geometry` 会让 Tk
  整个重排一帧，改成只 `set_client_rect()` 按原尺寸校正。

**验证**：8ms 间隔采样整个打开过程，客户区从头到尾都是 `(490, 250)` 不变，按钮
`110x43`；用户实测白条消失。

### 3. 首次打开先亮一帧（待观察）

tint 要等 DWM 重新合成才生效。已加 `DwmFlush` + 原样 `SetWindowPos`，另有
`after(60)` 二次挂玻璃兜底。这次没有专门复核，如果仍然明显，从这里接着查。

## 工作区状态

全部改动已提交，提交 `71c659d`「0.9.2：系统亚克力弹窗与浮层，时间日期页」，
工作区干净。

本地验证用的东西都在 `tests/`（已加入 `.gitignore`，不提交）：

```
tests/screenshots/   手工截图
tests/demos/         acrylic_demo.py、acrylic_dialog_demo.py
tests/dev/           pywinstyles 1.8 源码（只作参考，没有 pip 安装）
```

`compileall ctk_kit examples` 与 `import ctk_kit` 冒烟通过；DemoApp 切页由人眼验收。
