from aiogram.utils.keyboard import InlineKeyboardBuilder


def keyboard(rows):
    rows = [row for row in rows if row]
    b = InlineKeyboardBuilder()
    for row in rows:
        for item in row:
            text, data, *style = item
            b.button(text=text, callback_data=data, style=style[0] if style else None)
    b.adjust(*[len(row) for row in rows])
    return b.as_markup()


def menu():
    return keyboard(
        [
            [("📝 Test tanlash", "list:0", "primary")],
            [("🔑 Kod bilan kirish", "code"), ("▶️ Davom ettirish", "resume")],
            [("📊 Natijalarim", "results"), ("🏆 Reyting", "ranking")],
            [("👤 Profilim", "profile")],
        ]
    )


def back_menu():
    return keyboard([[("‹ Bosh menyu", "menu")]])


def question_keyboard(a, q, count=None, selected=None):
    token = a.id.hex
    rows = [
        [
            (
                ("✓ " if selected == i else "") + "ABCD"[i],
                f"a:{token}:{q.position}:{i}:{a.revision}",
                "primary" if selected == i else None,
            )
            for i in range(4)
        ]
    ]
    if a.navigation == "free":
        count = a.questions.count() if count is None else count
        row = []
        if a.cursor > 0:
            row.append(("← Oldingi", f"n:{token}:{a.cursor - 1}:{a.revision}"))
        if a.cursor + 1 < count:
            row.append(("Keyingi →", f"n:{token}:{a.cursor + 1}:{a.revision}"))
        if row:
            rows.append(row)
    rows.append([("Testni yakunlash", f"f:{token}", "danger")])
    return keyboard(rows)
