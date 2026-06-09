from __future__ import annotations

import shlex
from dataclasses import dataclass

from cafe_order_kiosk.models import OrderStatus
from cafe_order_kiosk.kiosk_store import KioskStore
from cafe_order_kiosk.utils import format_money

# 다국어 지원을 위한 번역 사전 정의
TRANSLATIONS = {
    "ko": {
        "title": "카페 주문 키오스크",
        "welcome_hint": "명령어 목록은 '도움말'을 입력하세요. 가격은 원 단위 정수입니다.",
        "unknown_cmd": "알 수 없는 명령입니다. '도움말'을 입력하세요.",
        "exit": "종료합니다.",
        "prompt": "kiosk> ",
        "help_title": "명령어:",
        "help_menu": "\t메뉴 (menu)",
        "help_order_new": "\t주문 생성 [메모] (order new [note])",
        "help_order_select": "\t주문 선택 <주문_id> (order select <order_id>)",
        "help_order_add": "\t주문 추가 <메뉴_id> <수량> [옵션] (order add <menu_id> <qty> [options])",
        "help_order_remove": "\t주문 삭제 <라인번호> (order remove <line_index>)",
        "help_order_show": "\t주문 조회 (order show)",
        "help_order_cancel": "\t주문 취소 (order cancel)",
        "help_orders_list": "\t주문목록 목록 [진행중|결제완료|취소] (orders list [open|paid|canceled])",
        "help_pay": "\t결제 <방법> [금액] (pay <method> [amount])",
        "help_lang": "\t언어 <영어|한국어> (lang <en|ko>)",
        "help_help": "\t도움말 (help)",
        "help_exit": "\t종료 (quit/exit)",
        "menu_title": "메뉴:",
        "order_cmd_hint": "주문 명령어: 생성, 선택, 추가, 삭제, 조회, 취소",
        "order_created": "주문 #{}가 생성되었습니다.",
        "order_selected": "주문 #{}를 선택했습니다.",
        "order_not_found": "주문을 찾을 수 없습니다.",
        "no_active_order": "선택된 주문이 없습니다. 먼저 '주문 생성'을 사용하세요.",
        "order_add_usage": "사용법: 주문 추가 <메뉴_id> <수량> [옵션]",
        "item_added": "항목이 추가되었습니다.",
        "item_removed": "항목이 삭제되었습니다.",
        "order_canceled": "주문 #{}가 취소되었습니다.",
        "unknown_order_action": "알 수 없는 주문 명령어입니다.",
        "orders_list_usage": "사용법: 주문목록 목록 [진행중|결제완료|취소]",
        "no_orders": "주문이 없습니다.",
        "pay_usage": "사용법: 결제 <방법> [금액]",
        "pay_success": "주문 #{} 결제 완료 ({}).",
        "order_empty": "  (비어 있음)",
        "total": "합계: ",
        "missing_arg": "필수 값이 없습니다: {}",
        "invalid_arg": "잘못된 값: {}",
        "invalid_status": "잘못된 상태입니다. 진행중, 결제완료, 취소 중에서 선택하세요.",
        "status_open": "진행중",
        "status_paid": "결제완료",
        "status_canceled": "취소",
        "lang_changed": "언어가 한국어로 변경되었습니다."
    },
    "en": {
        "title": "Cafe Order Kiosk",
        "welcome_hint": "Type 'help' for command list. Prices are in KRW.",
        "unknown_cmd": "Unknown command. Type 'help'.",
        "exit": "Exiting.",
        "prompt": "kiosk> ",
        "help_title": "Commands:",
        "help_menu": "\tmenu",
        "help_order_new": "\torder new [note]",
        "help_order_select": "\torder select <order_id>",
        "help_order_add": "\torder add <menu_id> <qty> [options]",
        "help_order_remove": "\torder remove <line_index>",
        "help_order_show": "\torder show",
        "help_order_cancel": "\torder cancel",
        "help_orders_list": "\torders list [open|paid|canceled]",
        "help_pay": "\tpay <method> [amount]",
        "help_lang": "\tlang <en|ko>",
        "help_help": "\thelp",
        "help_exit": "\tquit/exit",
        "menu_title": "Menu:",
        "order_cmd_hint": "Order commands: new, select, add, remove, show, cancel",
        "order_created": "Order #{} has been created.",
        "order_selected": "Selected order #{}.",
        "order_not_found": "Order not found.",
        "no_active_order": "No order selected. Please use 'order new' first.",
        "order_add_usage": "Usage: order add <menu_id> <quantity> [options]",
        "item_added": "Item added successfully.",
        "item_removed": "Item removed successfully.",
        "order_canceled": "Order #{} has been canceled.",
        "unknown_order_action": "Unknown order action.",
        "orders_list_usage": "Usage: orders list [open|paid|canceled]",
        "no_orders": "No orders found.",
        "pay_usage": "Usage: pay <method> [amount]",
        "pay_success": "Order #{} payment complete ({}).",
        "order_empty": "  (Empty)",
        "total": "Total: ",
        "missing_arg": "Missing required argument: {}",
        "invalid_arg": "Invalid argument: {}",
        "invalid_status": "Invalid status. Choose from open, paid, canceled.",
        "status_open": "Open",
        "status_paid": "Paid",
        "status_canceled": "Canceled",
        "lang_changed": "Language has been changed to English."
    }
}


@dataclass
class CLIState:
    current_order_id: int | None = None
    lang: str = "ko"  # 기본 언어 상태를 한국어("ko")로 지정


def run_cli() -> int:
    store = KioskStore.with_default_menu()
    state = CLIState()

    print(TRANSLATIONS[state.lang]["title"])
    print(TRANSLATIONS[state.lang]["welcome_hint"])

    while True:
        try:
            raw = input(TRANSLATIONS[state.lang]["prompt"]).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not raw:
            continue

        tokens = shlex.split(raw)
        command, args = tokens[0], tokens[1:]

        if command in {"종료", "끝", "quit", "exit"}:
            break
        elif command in {"도움말", "help"}:
            print_help(state.lang)
        elif command in {"메뉴", "menu"}:
            handle_menu(store, state.lang)
        elif command in {"주문", "order"}:
            handle_order(store, state, args)
        elif command in {"주문목록", "orders"}:
            handle_orders(store, state, args)
        elif command in {"결제", "pay"}:
            handle_pay(store, state, args)
        elif command in {"언어", "lang", "영어", "한국어", "english", "korean"}:
            # 언어 전환 처리 명령어 
            if command == "영어" or command == "english" or (args and args[0].lower() in {"en", "영어", "english"}):
                state.lang = "en"
            elif command == "한국어" or command == "korean" or (args and args[0].lower() in {"ko", "kr", "한국어", "korean"}):
                state.lang = "ko"
            else:
                # 인자 없이 lang 또는 언어만 입력 시 토글
                state.lang = "en" if state.lang == "ko" else "ko"
            print(TRANSLATIONS[state.lang]["lang_changed"])
        else:
            print(TRANSLATIONS[state.lang]["unknown_cmd"])
            
    print(TRANSLATIONS[state.lang]["exit"])
    return 0


def print_help(lang: str) -> None:
    t = TRANSLATIONS[lang]
    print(t["help_title"])
    print(t["help_menu"])
    print(t["help_order_new"])
    print(t["help_order_select"])
    print(t["help_order_add"])
    print(t["help_order_remove"])
    print(t["help_order_show"])
    print(t["help_order_cancel"])
    print(t["help_orders_list"])
    print(t["help_pay"])
    print(t["help_lang"])
    print(t["help_help"])
    print(t["help_exit"])


def handle_menu(store: KioskStore, lang: str) -> None:
    print(TRANSLATIONS[lang]["menu_title"])
    for item in store.list_menu():
        description = f" - {item.description}" if item.description else ""
        print(
            f"\t{item.id}. {item.name} ({item.category}) - {format_money(item.price)}"
            f"{description}"
        )


def handle_order(store: KioskStore, state: CLIState, args: list[str]) -> None:
    lang = state.lang
    t = TRANSLATIONS[lang]
    if not args:
        print(t["order_cmd_hint"])
        return

    action, tail = args[0], args[1:]

    if action in {"생성", "new"}:
        note = " ".join(tail).strip() if tail else None
        order = store.create_order(note=note)
        state.current_order_id = order.id
        print(t["order_created"].format(order.id))
    elif action in {"선택", "select"}:
        order_id = parse_int_arg(tail, "order_id", lang)
        if order_id is None:
            return
        order = store.get_order(order_id)
        if order is None:
            print(t["order_not_found"])
            return
        state.current_order_id = order.id
        print(t["order_selected"].format(order.id))
    elif action in {"추가", "add"}:
        if state.current_order_id is None:
            print(t["no_active_order"])
            return
        if len(tail) < 2:
            print(t["order_add_usage"])
            return
        menu_id = parse_int_arg(tail[:1], "menu_id", lang)
        quantity = parse_int_arg(tail[1:2], "qty", lang)
        if menu_id is None or quantity is None:
            return

        options_text = " ".join(tail[2:]).strip()
        options = (
            [option.strip() for option in options_text.split(",") if option.strip()]
            if options_text
            else []
        )
        try:
            store.add_item(state.current_order_id, menu_id, quantity, options)
        except ValueError as exc:
            print(str(exc))
            return
        print(t["item_added"])
    elif action in {"삭제", "remove"}:
        if state.current_order_id is None:
            print(t["no_active_order"])
            return
        line_index = parse_int_arg(tail, "line_index", lang)
        if line_index is None:
            return
        try:
            store.remove_item(state.current_order_id, line_index)
        except ValueError as exc:
            print(str(exc))
            return
        print(t["item_removed"])
    elif action in {"조회", "show"}:
        if state.current_order_id is None:
            print(t["no_active_order"])
            return
        order = store.get_order(state.current_order_id)
        if order is None:
            print(t["order_not_found"])
            return
        print_order(order, lang)
    elif action in {"취소", "cancel"}:
        if state.current_order_id is None:
            print(t["no_active_order"])
            return
        try:
            order = store.cancel_order(state.current_order_id)
        except ValueError as exc:
            print(str(exc))
            return
        print(t["order_canceled"].format(order.id))
    else:
        print(t["unknown_order_action"])


def handle_orders(store: KioskStore, state: CLIState, args: list[str]) -> None:
    lang = state.lang
    t = TRANSLATIONS[lang]
    if not args or args[0] not in {"list", "목록"}:
        print(t["orders_list_usage"])
        return

    status = None
    if len(args) > 1:
        status = parse_status(args[1], lang)
        if status is None:
            return

    orders = store.list_orders(status)
    if not orders:
        print(t["no_orders"])
        return

    for order in orders:
        print(
            f"  #{order.id} {format_status(order.status, lang)} - {format_money(order.total)}"
        )


def handle_pay(store: KioskStore, state: CLIState, args: list[str]) -> None:
    lang = state.lang
    t = TRANSLATIONS[lang]
    if state.current_order_id is None:
        print(t["no_active_order"])
        return
    if not args:
        print(t["pay_usage"])
        return

    method = args[0]
    amount = None
    if len(args) > 1:
        amount = parse_int_arg(args[1:2], "amount", lang)
        if amount is None:
            return

    order = store.get_order(state.current_order_id)
    if order is None:
        print(t["order_not_found"])
        return
    if amount is None:
        amount = order.total

    try:
        store.pay_order(order.id, method, amount)
    except ValueError as exc:
        print(str(exc))
        return

    print(t["pay_success"].format(order.id, method))


def print_order(order, lang: str) -> None:
    t = TRANSLATIONS[lang]
    print(f"Order #{order.id} ({format_status(order.status, lang)})")
    if order.note:
        print(f"{'메모' if lang == 'ko' else 'Note'}: {order.note}")
    if not order.items:
        print(t["order_empty"])
        return

    for idx, item in enumerate(order.items, start=1):
        options = f" [{', '.join(item.options)}]" if item.options else ""
        print(
            f"  {idx}. {item.name}{options} x{item.quantity}"
            f" - {format_money(item.line_total)}"
        )
    print(f"{t['total']}{format_money(order.total)}")


def parse_int_arg(args: list[str], name: str, lang: str) -> int | None:
    t = TRANSLATIONS[lang]
    if not args:
        print(t["missing_arg"].format(name))
        return None
    try:
        return int(args[0])
    except ValueError:
        print(t["invalid_arg"].format(name))
        return None


def parse_status(raw: str, lang: str) -> OrderStatus | None:
    normalized = raw.lower()
    status_map = {
        "open": OrderStatus.OPEN,
        "paid": OrderStatus.PAID,
        "canceled": OrderStatus.CANCELED,
        "진행중": OrderStatus.OPEN,
        "결제완료": OrderStatus.PAID,
        "취소": OrderStatus.CANCELED,
    }
    status = status_map.get(normalized)
    if status is None:
        print(TRANSLATIONS[lang]["invalid_status"])
    return status


def format_status(status: OrderStatus, lang: str) -> str:
    t = TRANSLATIONS[lang]
    status_map = {
        OrderStatus.OPEN: t["status_open"],
        OrderStatus.PAID: t["status_paid"],
        OrderStatus.CANCELED: t["status_canceled"],
    }
    return status_map.get(status, status.value)