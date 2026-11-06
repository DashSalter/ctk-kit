import tkinter as tk

from ctk_kit import (
    Card,
    FieldLabel,
    Frame,
    get_appearance_mode,
    HintLabel,
    is_dark,
    PageBase,
    PageHeader,
    Scrollable,
    SecondaryButton,
    Segmented,
    Slider,
    Switch,
    theme,
    theming,
)


class SettingsPageUI(PageBase):

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)

        self.header = PageHeader(self, "设置")

        # 底部回显条先于滚动区 pack：内容再多也不会被挤掉
        self.feedback = HintLabel(self, "提示:切换主题模式只重建当前页，其余页切过去时再建")
        self.feedback.pack(side="bottom", fill="x", pady=(8, 0))

        area = Scrollable(self)
        area.pack(fill="both", expand=True, pady=(14, 0))

        self._build_appearance(area)
        self._build_glass(area)
        self._build_titlebar(area)
        self._build_debug(area)
        self.refresh_theme()
        # App 的背景窗口是延迟创建的（启动后 ~40ms），构造函数里读到的还是
        # None。等一拍再回填一次，界面才和真实的底色对齐。
        self.after(260, self.refresh_background)

    def _build_appearance(self, area: tk.Misc) -> None:
        """外观模式：主题三项 + 毛玻璃时的背景窗口设置。"""
        box = Card(area, title="外观模式")
        box.pack(fill="x")

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))

        FieldLabel(row, "主题", width=64).pack(side="left")

        self.theme = Segmented(
            row,
            ["毛玻璃", "深空", "Acrylic", "Mica"],
            width=380,
        )
        self.theme.pack(side="left", padx=(4, 0))

        self.bg_box = box
        self.bg_rows: list[tk.Frame] = []

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        FieldLabel(row, "背景颜色", width=110).pack(side="left")
        self.bg_color = Segmented(
            row,
            ["黑", "白", "红", "橙", "黄", "绿", "青", "蓝", "紫"],
            width=630,
        )
        self.bg_color.pack(side="left", padx=(4, 0))
        self.bg_rows.append(row)

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 14))
        FieldLabel(row, "背景透明度", width=110).pack(side="left")
        self.bg_alpha = Slider(row, from_=0, to=255, width=180)
        self.bg_alpha.pack(side="left", padx=(4, 8))
        self.bg_alpha_value = FieldLabel(row, "56", width=36)
        self.bg_alpha_value.pack(side="left")
        HintLabel(row, "0 全透，255 最实").pack(side="left", padx=(10, 0))
        self.bg_rows.append(row)

    def _build_glass(self, area: tk.Misc) -> None:
        """毛玻璃微调：DWM 的每一种手段单独一个控件，改完立即重挂。"""
        box = Card(area, title="窗口Debug")
        box.pack(fill="x", pady=(12, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))
        FieldLabel(row, "窗口圆角", width=64).pack(side="left")
        self.glass_corners = Segmented(
            row, ["默认", "不圆", "圆", "小圆"], width=280
        )
        self.glass_corners.pack(side="left", padx=(4, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        FieldLabel(row, "边框色", width=64).pack(side="left")
        self.glass_border = Segmented(row, ["灰", "无", "黑", "白"], width=280)
        self.glass_border.pack(side="left", padx=(4, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        FieldLabel(row, "标题栏色", width=64).pack(side="left")
        self.glass_caption = Segmented(row, ["玻璃", "黑", "白"], width=210)
        self.glass_caption.pack(side="left", padx=(4, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        FieldLabel(row, "整体透明度", width=64).pack(side="left")
        self.glass_opacity = Slider(row, from_=10, to=100, width=180)
        self.glass_opacity.pack(side="left", padx=(4, 8))
        self.glass_opacity_value = FieldLabel(row, "100%", width=44)
        self.glass_opacity_value.pack(side="left")

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        FieldLabel(row, "透明色", width=64).pack(side="left")
        self.glass_veil = Segmented(row, ["纯黑", "近黑", "深灰", "暖黑"], width=260)
        self.glass_veil.pack(side="left", padx=(4, 0))

        self.glass_extend = self._glass_switch(
            box, "延伸客户区", "extend", last=True
        )

        HintLabel(
            box,
            "Accent / Acrylic 吃 tint；系统 / Mica 的亮度由 DWM 决定，tint 不生效。"
            "整体透明度低于 100% 时窗口变成 layered，DWM 会把玻璃摘掉。",
        ).pack(anchor="w", padx=16, pady=(0, 14))

    def _glass_switch(self, box: tk.Misc, label: str, key: str, *, last: bool = False) -> Switch:
        """一行「标签 + 开关」，开关回调按 ``key`` 走对应的专用方法。"""
        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 14) if last else (0, 8))
        FieldLabel(row, label, width=64).pack(side="left")
        switch = Switch(row, command=lambda k=key: self._on_glass_switch(k))
        switch.pack(side="left", padx=(4, 0))
        return switch

    def _build_titlebar(self, area: tk.Misc) -> None:
        """标题栏：临时隐藏左上角的图标和标题文字。"""
        box = Card(area, title="标题栏")
        box.pack(fill="x", pady=(12, 0))

        self.titlebar_icon = self._titlebar_switch(box, "显示图标", "icon")
        self.titlebar_title = self._titlebar_switch(box, "显示标题", "title", last=True)

        HintLabel(
            box,
            "只改系统标题栏：图标区留空、标题文字清空；任务栏图标不受影响，Tk 的窗口标题"
            "不变，拨回开关立即恢复。",
        ).pack(anchor="w", padx=16, pady=(0, 14))

    def _titlebar_switch(
        self, box: tk.Misc, label: str, key: str, *, last: bool = False
    ) -> Switch:
        """一行「标签 + 开关」，开关回调按 ``key`` 交给标题栏的两个专用方法。"""
        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 14) if last else (0, 8))
        FieldLabel(row, label, width=64).pack(side="left")
        switch = Switch(row, command=lambda k=key: self._on_titlebar_switch(k))
        switch.pack(side="left", padx=(4, 0))
        return switch

    def _build_debug(self, area: tk.Misc) -> None:
        """窗口调试：DWM 的 3（关过渡动画）、9（读真实边界）。"""
        box = Card(area, title="窗口调试（DWM）")
        box.pack(fill="x", pady=(12, 0))

        self._debug_labels: dict[str, FieldLabel] = {}
        self.debug_transitions = self._debug_switch(box, "关过渡动画", "transitions")

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        FieldLabel(row, "真实边界", width=64).pack(side="left")
        self.debug_read = SecondaryButton(
            row, "读取", self.on_debug_bounds, width=76
        )
        self.debug_read.pack(side="left", padx=(4, 8))
        self.debug_bounds = FieldLabel(row, "点「读取」看 DWM 与 Tk 的差值", width=430)
        self.debug_bounds.pack(side="left")

        self.debug_hint = HintLabel(
            box,
            "边框：37，Win11 22H2+ 才生效，0 去掉那条 1px 线；动画：3，关掉窗口出现 / "
            "重建时的过渡；边界：9，含阴影的真实屏幕矩形，和 winfo_rootx 那套（客户区）对比。",
        )
        self.debug_hint.pack(anchor="w", padx=16, pady=(0, 14))

    def _debug_switch(
        self, box: tk.Misc, label: str, key: str, *, last: bool = False
    ) -> Switch:
        """一行「标签 + 开关」，开关回调按 ``key`` 交给窗口调试的专用方法。"""
        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 14) if last else (0, 8))
        label_widget = FieldLabel(row, label, width=64)
        label_widget.pack(side="left")
        self._debug_labels[key] = label_widget
        switch = Switch(row, command=lambda k=key: self._on_debug_switch(k))
        switch.pack(side="left", padx=(4, 0))
        return switch

    def refresh_theme(self) -> None:
        """按当前外观刷新标题说明和分段选中项。"""
        self.header.info.configure(text=f"当前：{get_appearance_mode()}")
        if theme.current_backdrop() == "acrylic":
            app = getattr(self, "app", None)
            options = app.glass_options() if app is not None else {}
            kind = options.get("kind", "")
            if kind in ("acrylic", "mica"):
                self.theme.set({"acrylic": "Acrylic", "mica": "Mica"}[kind])
            elif options.get("backdrop", 0) == 1:
                self.theme.set("深空")
            else:
                self.theme.set("毛玻璃")
        else:
            # 主题里只剩玻璃系；非玻璃状态下不硬选某一项，保留上次的选择。
            pass
        self.refresh_background()
        self.refresh_glass()
        self.refresh_titlebar()
        self.refresh_debug()

    def refresh_glass(self) -> None:
        """把 App 上当前的毛玻璃参数回填到控件。"""
        app = getattr(self, "app", None)
        options = app.glass_options() if app is not None else {}
        if not options:
            return
        opacity = int(round(float(options.get("opacity", 1.0)) * 100))
        self.glass_opacity.set(opacity)
        self.glass_opacity_value.configure(text=f"{opacity}%")
        veil = str(options.get("veil", "#000000")).upper()
        self.glass_veil.set(
            {"#000000": "纯黑", "#050505": "近黑", "#101010": "深灰", "#181A20": "暖黑"}.get(
                veil, "纯黑"
            )
        )
        self.glass_corners.set(
            {0: "默认", 1: "不圆", 2: "圆", 3: "小圆"}.get(
                options.get("corners", 0), "默认"
            )
        )
        border = options.get("border")
        self.glass_border.set(
            {0x808080: "灰", 0xFFFFFFFE: "无", 0x000000: "黑", 0xFFFFFF: "白"}.get(
                border, "无"
            )
        )
        caption = options.get("caption")
        self.glass_caption.set(
            "玻璃"
            if caption is None
            else {0x000000: "黑", 0xFFFFFF: "白"}.get(caption, "玻璃")
        )
        for key in ("extend",):
            switch = getattr(self, f"glass_{key}")
            if options[key]:
                switch.select()
            else:
                switch.deselect()

    def refresh_titlebar(self) -> None:
        """把 App 当前的图标 / 标题显隐状态回填到两个开关。"""
        app = getattr(self, "app", None)
        if app is None:
            return
        items = app.titlebar_items()
        for key, switch in (
            ("icon", self.titlebar_icon),
            ("title", self.titlebar_title),
        ):
            if items.get(key):
                switch.select()
            else:
                switch.deselect()

    def refresh_debug(self) -> None:
        """把 App 上当前的窗口调试项回填到两个开关。"""
        app = getattr(self, "app", None)
        if app is None:
            return
        options = app.window_debug()
        for key, switch in (("disable_transitions", self.debug_transitions),):
            if options.get(key):
                switch.select()
            else:
                switch.deselect()
        self.debug_hint.configure(
            text="动画：3，关掉窗口出现 / 重建时的过渡；边界：9，含阴影的真实屏幕矩形，"
            "和 winfo_rootx 那套（客户区）对比。"
        )


class SettingsPage(SettingsPageUI):
    """事件类：构造时自动调用 bind_events()。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.bind_events()

    def bind_events(self) -> None:
        """必须实现：注册按钮和事件。"""
        self.theme.configure(command=self.on_theme)
        self.bg_color.configure(command=self.on_bg_color)
        self.bg_alpha.configure(command=self.on_bg_alpha)
        self.glass_corners.configure(command=self.on_glass_corners)
        self.glass_border.configure(command=self.on_glass_border)
        self.glass_caption.configure(command=self.on_glass_caption)
        self.glass_opacity.configure(command=self.on_glass_opacity)
        self.glass_veil.configure(command=self.on_glass_veil)

    def on_theme(self, value: str) -> None:
        """切换毛玻璃 / 深空 / Acrylic / Mica；有 SidebarNav 时只重建当前页。"""
        app = self.app
        # 毛玻璃：自定义颜色整体暗 20%；其它主题：恢复原色并把背景、整体
        # 透明度都拉满（少一点透光，贴近系统原生窗口）。
        if value == "毛玻璃":
            theming.set_darken(0.75, root=app)
        else:
            theming.set_darken(1.0, root=app)
            self._full_opacity()
        # Acrylic / Mica 是深色版的玻璃主题：深色外观 + 中性深色 tint，
        # 不再沿用默认 #181A20 的蓝调。
        deep_kinds = {"Acrylic": "acrylic", "Mica": "mica"}
        if value in deep_kinds:
            kind = deep_kinds[value]
            if app.glass_options().get("kind") == kind:
                return
            # 只切合成方式和 tint，不碰 set_appearance_mode / set_backdrop，
            # 这两个会重建外壳和当前页。
            app.set_glass_kind(kind).set_tint("#1A1A1A")
            return
        if value == "深空":
            # 深色 + 系统背板「1 无」：DWM 不再画背板/模糊，窗口就是纯深的实底。
            wanted_mode, wanted_backdrop = "dark", "acrylic"
            app.set_glass_kind("accent").set_system_backdrop(1).set_tint("#1A1A1A")
        elif value == "毛玻璃":
            wanted_mode, wanted_backdrop = "dark", "acrylic"
            # 从 Acrylic / Mica 切回来时把 tint 和合成方式还原成默认，
            # 否则玻璃还带着上一种主题的中性深色。
            app.set_glass_kind("accent").set_tint("#181A20")
        else:
            return
        # 已经是这个状态就不要再走一遍：set_backdrop / set_appearance_mode
        # 都会重建当前页，连点同一个会白闪一下。
        if (
            theme.current_backdrop() == wanted_backdrop
            and str(get_appearance_mode()).lower() == wanted_mode
        ):
            return
        if value in ("毛玻璃", "深空"):
            app.set_appearance_mode(wanted_mode)
            app.set_backdrop(wanted_backdrop)
        else:
            app.set_backdrop(wanted_backdrop)
            app.set_appearance_mode(wanted_mode)
        # 不在这里 refresh：set_backdrop 会重建当前页，这个实例马上就要被丢掉，
        # 再碰它的控件只会拿到 "invalid command name"。

    def _full_opacity(self) -> None:
        """把窗口整体透明度和背景层都拉满（不透明）。"""
        app = self.app
        app.set_opacity(1.0)
        layer = getattr(app, "frost_layer", None)
        if layer is None:
            return
        app.set_frost_backdrop(
            getattr(layer, "color", "#181A20"),
            alpha=255,
            glass=bool(getattr(layer, "glass", False)),
            spread=int(getattr(layer, "spread", 0)),
        )

    # ------------------------------------------------------------------ 背景窗口
    def refresh_background(self) -> None:
        """把「背景窗口」那几行同步到 App 的当前状态。

        背景窗口在毛玻璃模式下总是开启（不再有「启用」开关），所以这里只
        负责：毛玻璃时显示这几行并回填当前值，其它模式整块收起。
        """
        app = getattr(self, "app", None)
        if app is None or not self.winfo_exists():
            return
        acrylic = theme.current_backdrop() == "acrylic"
        for row in getattr(self, "bg_rows", []):
            if acrylic:
                row.pack(fill="x", padx=16, pady=(0, 8))
            else:
                row.pack_forget()
        layer = getattr(app, "frost_layer", None)
        # 回填时 set() 会触发 command，不挡住就会把界面的默认值反推回 App，
        # 把启动时刚恢复的持久化颜色覆盖掉。
        self._syncing_bg = True
        try:
            if layer is not None:
                color = str(getattr(layer, "color", "#FFFFFF")).upper()
                for name, value in self._bg_colors().items():
                    if value.upper() == color:
                        self.bg_color.set(name)
                        break
                alpha = int(getattr(layer, "alpha", 56))
                self.bg_alpha.set(alpha)
                self.bg_alpha_value.configure(text=str(alpha))
                self._bg_spread = int(getattr(layer, "spread", 0))
            else:
                # 没开的时候给一个跟当前外观搭的默认值：深色配黑、浅色配白。
                self.bg_color.set("黑" if is_dark() else "白")
                self.bg_alpha.set(56)
                self.bg_alpha_value.configure(text="56")
                self._bg_spread = 0
        finally:
            self._syncing_bg = False
        self._set_bg_controls(acrylic)

    def _bg_colors(self) -> dict:
        """底层窗口的九种底色：黑、白 + 七个彩色。"""
        return {
            "黑": "#000000",
            "白": "#FFFFFF",
            "红": "#E5484D",
            "橙": "#F76B15",
            "黄": "#F5C542",
            "绿": "#30A46C",
            "青": "#17A6BD",
            "蓝": "#2F6FED",
            "紫": "#8E4EC6",
        }

    def _set_bg_controls(self, enabled: bool) -> None:
        self.bg_color.set_enabled(enabled)
        self.bg_alpha.configure(state="normal" if enabled else "disabled")

    def _bg_request(self) -> tuple[str, bool]:
        """读当前选择，返回 ``(颜色, 是否用毛玻璃)``。

        毛玻璃那格已经去掉：切到毛玻璃会带 WS_THICKFRAME，底层窗口的
        位置和尺寸都会跟着变，问题太多，这里固定走纯色。
        """
        return self._bg_colors().get(self.bg_color.get(), "#FFFFFF"), False

    def _push_bg(self) -> None:
        """把当前颜色 + 透明度推给 App，并写进配置文件。"""
        if getattr(self, "_syncing_bg", False):
            return
        app = self.app
        color, glass = self._bg_request()
        alpha = int(self.bg_alpha.get())
        spread = int(getattr(self, "_bg_spread", 0))
        # 第一次进来时这一层可能还没建（App 的自动创建是延迟的），
        # set_frost_backdrop 自己会补建，所以这里不要求 frost_active。
        app.set_frost_backdrop(color, alpha=alpha, glass=glass, spread=spread)
        store = getattr(app, "state_store", None)
        if store is not None:
            store.write_frost(color, alpha, spread)

    def on_bg_color(self, _value: str) -> None:
        self._push_bg()

    def on_bg_alpha(self, value: float) -> None:
        alpha = int(round(value))
        self.bg_alpha_value.configure(text=str(alpha))
        self._push_bg()

    def on_bg_spread(self, value: float) -> None:
        self._bg_spread = int(round(value))
        self._push_bg()

    def on_glass_kind(self, value: str) -> None:
        """换一种 DWM 合成方式：Accent 模糊 / Acrylic / 系统背板 / Mica。"""
        kinds = {"Accent": "accent", "Acrylic": "acrylic", "系统": "system", "Mica": "mica"}
        self.app.set_glass_kind(kinds.get(value, "accent"))

    def on_glass_alpha(self, value: float) -> None:
        """拖动压暗滑块：0 最透、255 最黑。"""
        alpha = int(round(float(value)))
        self.app.set_tint_alpha(alpha)

    def on_glass_opacity(self, value: float) -> None:
        """拖动整体透明度：10%–100%，换算成窗口的 ``-alpha``。"""
        percent = int(round(float(value)))
        self.glass_opacity_value.configure(text=f"{percent}%")
        self.app.set_opacity(percent / 100)
        # 核心会把背景透明度压到不超过整体透明度，这里同步一下显示。
        self.refresh_background()

    def on_glass_wca(self, value: str) -> None:
        """切换 ``SetWindowCompositionAttribute`` 的属性号（19 是默认值）。"""
        self.app.set_wca(int(value))

    def on_glass_state(self, value: str) -> None:
        """换 AccentState：0 关 / 2 透明渐变 / 3 模糊 / 4 亚克力。"""
        states = {"0 关": 0, "2 透明": 2, "3 模糊": 3, "4 亚克力": 4}
        self.app.set_glass_state(states.get(value, 3))

    def on_glass_backdrop(self, value: str) -> None:
        """直接写 ``DWMWA_SYSTEMBACKDROP_TYPE``（38）。"""
        kinds = {"不设": 0, "1 无": 1, "2 Mica": 2, "3 亚克力": 3, "4 标签": 4}
        self.app.set_system_backdrop(kinds.get(value, 0))

    def on_glass_corners(self, value: str) -> None:
        """写 ``DWMWA_WINDOW_CORNER_PREFERENCE``（33）。"""
        values = {"默认": 0, "不圆": 1, "圆": 2, "小圆": 3}
        self.app.set_window_corners(values.get(value, 0))

    def on_glass_border(self, value: str) -> None:
        """写 ``DWMWA_BORDER_COLOR``（34）；「无」表示不要边框。"""
        values = {"灰": "#808080", "无": None, "黑": "#000000", "白": "#FFFFFF"}
        self.app.set_border_color(values.get(value))

    def on_glass_caption(self, value: str) -> None:
        """写 ``DWMWA_CAPTION_COLOR``（35）；「玻璃」表示交还给 DWM。"""
        values = {"玻璃": None, "黑": "#000000", "白": "#FFFFFF"}
        self.app.set_caption_color(values.get(value))

    def on_glass_color(self, value: str) -> None:
        """换 tint 底色；「白」配高「压暗」就是白色毛玻璃。"""
        colors = {
            "黑": "#000000",
            "暖黑": "#181A20",
            "深灰": "#2A2D33",
            "白": "#FFFFFF",
        }
        self.app.set_tint(colors.get(value, "#181A20"))

    def on_glass_veil(self, value: str) -> None:
        """换「透明键色」：只有纯黑会被 DWM 当成全透明。"""
        veils = {"纯黑": "#000000", "近黑": "#050505", "深灰": "#101010", "暖黑": "#181A20"}
        self.app.set_veil(veils.get(value, "#000000"))

    def _on_glass_switch(self, key: str) -> None:
        """某个开关被拨动：读它的新状态写回去。"""
        switch = getattr(self, f"glass_{key}")
        if key == "extend":
            self.app.set_extend(bool(switch.get()))

    def _on_titlebar_switch(self, key: str) -> None:
        """标题栏开关：隐藏 / 显示图标、标题文字，改完立即生效。"""
        switch = getattr(self, f"titlebar_{key}")
        value = bool(switch.get())
        if key == "icon":
            self.app.show_titlebar_icon(value)
        else:
            self.app.show_titlebar_title(value)

    def _on_debug_switch(self, key: str) -> None:
        """窗口调试开关：去 1px 边框 / 关过渡动画，改完立即生效。"""
        switch = getattr(self, f"debug_{key}")
        value = bool(switch.get())
        if key == "border":
            self.app.hide_frame_border(value)
        else:
            self.app.set_transitions(not value)

    def on_debug_bounds(self) -> None:
        """读 DWM 的真实边界（含阴影），和 Tk 的客户区坐标并排显示。"""
        app = self.app
        bounds = app.frame_bounds()
        if bounds is None:
            self.debug_bounds.configure(text="读不到：需要 Windows + DWM")
            return
        left, top, right, bottom = bounds
        x, y = app.winfo_rootx(), app.winfo_rooty()
        w, h = app.winfo_width(), app.winfo_height()
        self.debug_bounds.configure(
            text=f"DWM {left},{top} {right - left}×{bottom - top}"
            f"    Tk {x},{y} {w}×{h}"
        )
