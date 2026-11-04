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
        self._build_debug(area)
        self.refresh_theme()

    def _build_appearance(self, area: tk.Misc) -> None:
        """外观模式：主题分段按钮 + 底色（毛玻璃）开关 + 一行说明。"""
        box = Card(area, title="外观模式")
        box.pack(fill="x")

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))

        FieldLabel(row, "主题", width=64).pack(side="left")

        self.theme = Segmented(row, ["浅色", "深色"], width=200)
        self.theme.pack(side="left", padx=(4, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 14))

        FieldLabel(row, "底色", width=64).pack(side="left")

        self.backdrop = Segmented(row, ["不透明", "毛玻璃"], width=200)
        self.backdrop.pack(side="left", padx=(4, 0))

    def _build_glass(self, area: tk.Misc) -> None:
        """毛玻璃微调：DWM 的每一种手段单独一个控件，改完立即重挂。"""
        box = Card(area, title="毛玻璃微调")
        box.pack(fill="x", pady=(12, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(14, 8))
        FieldLabel(row, "合成方式", width=64).pack(side="left")
        self.glass_kind = Segmented(
            row, ["Accent", "Acrylic", "系统", "Mica"], width=250
        )
        self.glass_kind.pack(side="left", padx=(4, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        FieldLabel(row, "属性号", width=64).pack(side="left")
        self.glass_wca = Segmented(row, ["30", "19"], width=120)
        self.glass_wca.pack(side="left", padx=(4, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        FieldLabel(row, "Accent 状态", width=64).pack(side="left")
        self.glass_state = Segmented(
            row, ["0 关", "2 透明", "3 模糊", "4 亚克力"], width=300
        )
        self.glass_state.pack(side="left", padx=(4, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        FieldLabel(row, "系统背板", width=64).pack(side="left")
        self.glass_backdrop = Segmented(
            row, ["不设", "1 无", "2 Mica", "3 亚克力", "4 标签"], width=360
        )
        self.glass_backdrop.pack(side="left", padx=(4, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        FieldLabel(row, "窗口圆角", width=64).pack(side="left")
        self.glass_corners = Segmented(
            row, ["默认", "不圆", "圆", "小圆"], width=280
        )
        self.glass_corners.pack(side="left", padx=(4, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        FieldLabel(row, "边框色", width=64).pack(side="left")
        self.glass_border = Segmented(row, ["默认", "无", "黑", "白"], width=280)
        self.glass_border.pack(side="left", padx=(4, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        FieldLabel(row, "标题栏色", width=64).pack(side="left")
        self.glass_caption = Segmented(row, ["玻璃", "黑", "白"], width=210)
        self.glass_caption.pack(side="left", padx=(4, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        FieldLabel(row, "压暗", width=64).pack(side="left")
        self.glass_alpha = Slider(row, from_=0, to=255, width=180)
        self.glass_alpha.pack(side="left", padx=(4, 8))
        self.glass_alpha_value = FieldLabel(row, "0", width=36)
        self.glass_alpha_value.pack(side="left")

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        FieldLabel(row, "整体透明度", width=64).pack(side="left")
        self.glass_opacity = Slider(row, from_=10, to=100, width=180)
        self.glass_opacity.pack(side="left", padx=(4, 8))
        self.glass_opacity_value = FieldLabel(row, "100%", width=44)
        self.glass_opacity_value.pack(side="left")

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        FieldLabel(row, "底色", width=64).pack(side="left")
        self.glass_color = Segmented(row, ["黑", "暖黑", "深灰", "白"], width=270)
        self.glass_color.pack(side="left", padx=(4, 0))

        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 8))
        FieldLabel(row, "透明色", width=64).pack(side="left")
        self.glass_veil = Segmented(row, ["纯黑", "近黑", "深灰", "暖黑"], width=260)
        self.glass_veil.pack(side="left", padx=(4, 0))

        self.glass_frame = self._glass_switch(box, "补边框", "frame")
        self.glass_extend = self._glass_switch(box, "延伸客户区", "extend")
        self.glass_titlebar = self._glass_switch(box, "标题栏玻璃", "titlebar")
        self.glass_dark = self._glass_switch(box, "深色标题栏", "dark", last=True)

        HintLabel(
            box,
            "Accent / Acrylic 吃 tint；系统 / Mica 的亮度由 DWM 决定，压暗和底色不生效。"
            "整体透明度低于 100% 时窗口变成 layered，DWM 会把玻璃摘掉。",
        ).pack(anchor="w", padx=16, pady=(0, 14))

    def _glass_switch(self, box: tk.Misc, label: str, key: str, *, last: bool = False) -> Switch:
        """一行「标签 + 开关」，开关回调按 ``key`` 回写 ``set_glass_options``。"""
        row = Frame(box)
        row.pack(fill="x", padx=16, pady=(0, 14) if last else (0, 8))
        FieldLabel(row, label, width=64).pack(side="left")
        switch = Switch(row, command=lambda k=key: self._on_glass_switch(k))
        switch.pack(side="left", padx=(4, 0))
        return switch

    def _build_debug(self, area: tk.Misc) -> None:
        """窗口调试：DWM 的 37（去 1px 边框）、3（关过渡动画）、9（读真实边界）。"""
        box = Card(area, title="窗口调试（DWM）")
        box.pack(fill="x", pady=(12, 0))

        self._debug_labels: dict[str, FieldLabel] = {}
        self.debug_border = self._debug_switch(box, "去边框", "border")
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
        """一行「标签 + 开关」，开关回调按 ``key`` 交给 ``set_window_debug``。"""
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
        self.theme.set("深色" if is_dark() else "浅色")
        self.backdrop.set(
            "毛玻璃" if theme.current_backdrop() == "acrylic" else "不透明"
        )
        self.refresh_glass()
        self.refresh_debug()

    def refresh_glass(self) -> None:
        """把 App 上当前的毛玻璃参数回填到控件。"""
        app = getattr(self, "app", None)
        options = app.glass_options() if app is not None else {}
        if not options:
            return
        self.glass_kind.set(
            {"accent": "Accent", "acrylic": "Acrylic", "system": "系统", "mica": "Mica"}.get(
                options["kind"], "Accent"
            )
        )
        self.glass_alpha.set(options["alpha"])
        self.glass_alpha_value.configure(text=str(options["alpha"]))
        opacity = int(round(float(options.get("opacity", 1.0)) * 100))
        self.glass_opacity.set(opacity)
        self.glass_opacity_value.configure(text=f"{opacity}%")
        veil = str(options.get("veil", "#000000")).upper()
        self.glass_veil.set(
            {"#000000": "纯黑", "#050505": "近黑", "#101010": "深灰", "#181A20": "暖黑"}.get(
                veil, "纯黑"
            )
        )
        self.glass_wca.set(str(options.get("wca", 30)))
        self.glass_state.set(
            {0: "0 关", 2: "2 透明", 3: "3 模糊", 4: "4 亚克力"}.get(
                options.get("state", 3), "3 模糊"
            )
        )
        self.glass_backdrop.set(
            {0: "不设", 1: "1 无", 2: "2 Mica", 3: "3 亚克力", 4: "4 标签"}.get(
                options.get("backdrop", 0), "不设"
            )
        )
        self.glass_corners.set(
            {0: "默认", 1: "不圆", 2: "圆", 3: "小圆"}.get(
                options.get("corners", 0), "默认"
            )
        )
        border = options.get("border")
        self.glass_border.set(
            "默认"
            if border is None
            else {0xFFFFFFFE: "无", 0x000000: "黑", 0xFFFFFF: "白"}.get(border, "默认")
        )
        caption = options.get("caption")
        self.glass_caption.set(
            "玻璃"
            if caption is None
            else {0x000000: "黑", 0xFFFFFF: "白"}.get(caption, "玻璃")
        )
        self.glass_color.set(
            {
                "#000000": "黑",
                "#181A20": "暖黑",
                "#2A2D33": "深灰",
                "#FFFFFF": "白",
            }.get(options["color"], "暖黑")
        )
        for key in ("frame", "extend", "titlebar", "dark"):
            switch = getattr(self, f"glass_{key}")
            if options[key]:
                switch.select()
            else:
                switch.deselect()

    def refresh_debug(self) -> None:
        """把 App 上当前的窗口调试项回填到两个开关。"""
        app = getattr(self, "app", None)
        if app is None:
            return
        options = app.window_debug()
        for key, switch in (
            ("hide_frame_border", self.debug_border),
            ("disable_transitions", self.debug_transitions),
        ):
            if options.get(key):
                switch.select()
            else:
                switch.deselect()
        # 37 在 Win10 / 旧版 Win11 上不存在：把说明换成「不支持」，免得拨了没反应。
        if options.get("frame_border_supported") is False:
            self.debug_border.deselect()
            self.debug_hint.configure(
                text="当前系统不支持「去边框」（DWM 27/37 未生效），这个开关无效；"
                "动画（3）和边界（9）正常。"
            )
        else:
            self.debug_hint.configure(
                text="边框：37，Win11 22H2+ 才生效，0 去掉那条 1px 线；动画：3，关掉窗口"
                "出现 / 重建时的过渡；边界：9，含阴影的真实屏幕矩形，和 winfo_rootx 那套"
                "（客户区）对比。"
            )


class SettingsPage(SettingsPageUI):
    """事件类：构造时自动调用 bind_events()。"""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.bind_events()

    def bind_events(self) -> None:
        """必须实现：注册按钮和事件。"""
        self.theme.configure(command=self.on_theme)
        self.backdrop.configure(command=self.on_backdrop)
        self.glass_kind.configure(command=self.on_glass_kind)
        self.glass_wca.configure(command=self.on_glass_wca)
        self.glass_state.configure(command=self.on_glass_state)
        self.glass_backdrop.configure(command=self.on_glass_backdrop)
        self.glass_corners.configure(command=self.on_glass_corners)
        self.glass_border.configure(command=self.on_glass_border)
        self.glass_caption.configure(command=self.on_glass_caption)
        self.glass_alpha.configure(command=self.on_glass_alpha)
        self.glass_opacity.configure(command=self.on_glass_opacity)
        self.glass_color.configure(command=self.on_glass_color)
        self.glass_veil.configure(command=self.on_glass_veil)

    def on_theme(self, value: str) -> None:
        """切换浅色 / 深色；有 SidebarNav 时只重建当前页。"""
        self.app.set_appearance_mode(value)

    def on_backdrop(self, value: str) -> None:
        """切换普通底色 / 系统毛玻璃；会重建当前页。"""
        app = self.app
        app.set_backdrop("acrylic" if value == "毛玻璃" else "none")

    def on_glass_kind(self, value: str) -> None:
        """换一种 DWM 合成方式：Accent 模糊 / Acrylic / 系统背板 / Mica。"""
        kinds = {"Accent": "accent", "Acrylic": "acrylic", "系统": "system", "Mica": "mica"}
        self._set_glass(kind=kinds.get(value, "accent"))

    def on_glass_alpha(self, value: float) -> None:
        """拖动压暗滑块：0 最透、255 最黑。"""
        alpha = int(round(float(value)))
        self.glass_alpha_value.configure(text=str(alpha))
        self._set_glass(alpha=alpha)

    def on_glass_opacity(self, value: float) -> None:
        """拖动整体透明度：10%–100%，换算成 Tk 的 ``-alpha``。"""
        percent = int(round(float(value)))
        self.glass_opacity_value.configure(text=f"{percent}%")
        self._set_glass(opacity=percent / 100)

    def on_glass_wca(self, value: str) -> None:
        """切换 ``SetWindowCompositionAttribute`` 的属性号（30 是原来的值）。"""
        self._set_glass(wca=int(value))

    def on_glass_state(self, value: str) -> None:
        """换 AccentState：0 关 / 2 透明渐变 / 3 模糊 / 4 亚克力。"""
        states = {"0 关": 0, "2 透明": 2, "3 模糊": 3, "4 亚克力": 4}
        self._set_glass(state=states.get(value, 3))

    def on_glass_backdrop(self, value: str) -> None:
        """直接写 ``DWMWA_SYSTEMBACKDROP_TYPE``（38）。"""
        kinds = {"不设": 0, "1 无": 1, "2 Mica": 2, "3 亚克力": 3, "4 标签": 4}
        self._set_glass(backdrop=kinds.get(value, 0))

    def on_glass_corners(self, value: str) -> None:
        """写 ``DWMWA_WINDOW_CORNER_PREFERENCE``（33）。"""
        values = {"默认": 0, "不圆": 1, "圆": 2, "小圆": 3}
        self._set_glass(corners=values.get(value, 0))

    def on_glass_border(self, value: str) -> None:
        """写 ``DWMWA_BORDER_COLOR``（34）。"""
        values = {"默认": None, "无": 0xFFFFFFFE, "黑": 0x000000, "白": 0xFFFFFF}
        self._set_glass(border=values.get(value))

    def on_glass_caption(self, value: str) -> None:
        """写 ``DWMWA_CAPTION_COLOR``（35）；「玻璃」表示交还给 DWM。"""
        values = {"玻璃": None, "黑": 0x000000, "白": 0xFFFFFF}
        self._set_glass(caption=values.get(value))

    def on_glass_color(self, value: str) -> None:
        """换 tint 底色；「白」配高「压暗」就是白色毛玻璃。"""
        colors = {
            "黑": "#000000",
            "暖黑": "#181A20",
            "深灰": "#2A2D33",
            "白": "#FFFFFF",
        }
        self._set_glass(color=colors.get(value, "#181A20"))

    def on_glass_veil(self, value: str) -> None:
        """换「透明键色」：只有纯黑会被 DWM 当成全透明。"""
        veils = {"纯黑": "#000000", "近黑": "#050505", "深灰": "#101010", "暖黑": "#181A20"}
        self._set_glass(veil=veils.get(value, "#000000"))

    def _on_glass_switch(self, key: str) -> None:
        """某个开关被拨动：读它的新状态回写。"""
        switch = getattr(self, f"glass_{key}")
        self._set_glass(**{key: bool(switch.get())})

    def _on_debug_switch(self, key: str) -> None:
        """窗口调试开关：去 1px 边框 / 关过渡动画，改完立即生效。"""
        switch = getattr(self, f"debug_{key}")
        value = bool(switch.get())
        if key == "border":
            self.app.set_window_debug(hide_frame_border=value)
        else:
            self.app.set_window_debug(disable_transitions=value)

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

    def _set_glass(self, **kwargs) -> None:
        """把改动交给 App 立即重挂一次玻璃。"""
        app = getattr(self, "app", None)
        if app is not None:
            app.set_glass_options(**kwargs)
