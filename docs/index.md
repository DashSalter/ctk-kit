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
