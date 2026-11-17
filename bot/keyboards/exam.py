from aiogram.utils.keyboard import InlineKeyboardBuilder


def keyboard(rows):
    b = InlineKeyboardBuilder()
    for row in rows:
        for text, data in row:
            b.button(text=text, callback_data=data)
    b.adjust(*[len(row) for row in rows])
    return b.as_markup()


def menu():
    return keyboard(
        [
            [("Ochiq testlar", "list:0")],
            [("Test kodini kiritish", "code")],
            [("Testni davom ettirish", "resume")],
            [("Natijalarim", "results"), ("Reyting", "ranking")],
            [("Profilim", "profile")],
        ]
    )


def question_keyboard(a, q):
    token = a.id.hex
    rows = [[("ABCD"[i], f"a:{token}:{q.position}:{i}:{a.revision}") for i in range(4)]]
    if a.navigation == "free":
        row = []
        if a.cursor > 0:
            row.append(("← Oldingi", f"n:{token}:{a.cursor - 1}:{a.revision}"))
        if a.cursor + 1 < a.questions.count():
            row.append(("Keyingi →", f"n:{token}:{a.cursor + 1}:{a.revision}"))
        if row:
            rows.append(row)
    rows.append([("Testni yakunlash", f"f:{token}")])
    return keyboard(rows)
