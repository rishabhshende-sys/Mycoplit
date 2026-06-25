def click(x: int, y: int) -> None:
    import pyautogui
    pyautogui.click(x, y)


def type_text(text: str) -> None:
    import pyautogui
    pyautogui.write(text, interval=0.02)


def press_key(key: str) -> None:
    import pyautogui
    pyautogui.press(key)


def hotkey(keys: list[str]) -> None:
    import pyautogui
    pyautogui.hotkey(*keys)


def scroll(amount: int) -> None:
    import pyautogui
    pyautogui.scroll(amount)
