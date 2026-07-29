import pytest

from src.canvas import Canvas, UIElement


class TestCanvas:
    def test_render(self):
        c = Canvas()
        c.render([c.text("hello")])
        actions = c.get_actions()
        assert len(actions) == 1
        assert actions[0].type == "render"

    def test_append(self):
        c = Canvas()
        c.append(c.button("Click", "action"))
        actions = c.get_actions()
        assert len(actions) == 1
        assert actions[0].elements[0].type == "button"

    def test_clear(self):
        c = Canvas()
        c.render([c.text("hello")])
        c.clear()
        assert len(c._elements) == 0

    def test_builders(self):
        c = Canvas()
        btn = c.button("Go", "/go")
        assert btn.type == "button"
        txt = c.text("hello")
        assert txt.type == "text"
        frm = c.form([{"name": "email", "type": "text"}], "/submit")
        assert frm.type == "form"
        tbl = c.table(["Col1"], [["val"]])
        assert tbl.type == "table"
