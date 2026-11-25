"""表格示例：右键任意一行，向上/向下添加、编辑、删除。

``CrudTable`` 已经内置选中、右键菜单、编辑窗和确认框，这里只声明列和数据。
"""

import ctk_kit as ctk

members = [
    ["陈一", "产品", "产品经理", "chenyi@example.com"],
    ["林二", "设计", "交互设计师", "liner@example.com"],
    ["张三", "研发", "后端工程师", "zhangsan@example.com"],
    ["李四", "运营", "内容运营", "lisi@example.com"],
]

app = ctk.App(title="表格示例", size=(900, 640), min_size=(760, 520))

page = ctk.Frame(app)
page.pack(fill="both", expand=True, padx=24, pady=20)

ctk.PageHeader(page, "团队成员")

table = ctk.CrudTable(
    page,
    columns=[
        ("姓名", 130, "w"),
        ("部门", 140, "w"),
        ("角色", 160, "w"),
        ("邮箱", None, "w"),
    ],
    rows=members,
    new_row=["新成员", "", "", ""],
)
table.pack(fill="both", expand=True, pady=(12, 0))

app.mainloop()
