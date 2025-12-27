
from datetime import date
from decimal import Decimal
from typing import Optional
import sys

from expense_tracker import ExpenseTracker

BANNER = """
==============================================
        Personal Expense Tracker (CLI)
==============================================
"""

MENU = """
What would you like to do?
  1) Add expense
  2) View expenses
  3) Track budget (set/view)
  4) Save expenses
  5) Exit
Choose an option (1-5): """

def prompt(input_text: str) -> str:
    """
    Prompts the user for input and handles potential exceptions.

    Args:
        input_text (str): The text to be displayed to the user.

    Returns:
        str: The user's input.

    Raises:
        TypeError: If input_text is not a string.
    """
    if not isinstance(input_text, str):
        raise TypeError("Input must be a string.")

    try:
        return input(input_text)
    except EOFError:
        print("\nEOF detected. Exiting...")
        sys.exit(0)
    except KeyboardInterrupt:
        print("\nKeyboard interrupt detected. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

def choose_month(default_month: str | None = None) -> str:
    """
    Prompts the user for a month in the format YYYY-MM, 
    with the option to accept a default month if provided.

    Args:
        default_month (str | None): The default month to be used if the user does not provide one.

    Returns:
        str: The chosen month in the format YYYY-MM.
    """
    if default_month is None:
        from datetime import date
        default_month = date.today().strftime("%Y-%m")
    val = prompt(f"Enter month (YYYY-MM) [{default_month}]: ") or default_month
    try:
        year, mon = val.split("-")
        assert len(year) == 4 and len(mon) == 2
        int(year); int(mon)
    except Exception:
        print("Invalid month format. Please use YYYY-MM (e.g., 2025-01).")
        return choose_month(default_month)
    return val

def add_expense_flow(tracker: ExpenseTracker) -> None:
    """
    Adds a new expense to the tracker.

    Args:
        tracker (ExpenseTracker): The expense tracker instance.

    Returns:
        None
    """
    print("\nAdd a new expense:")

    # Get date from user
    while True:
        date_input: str = prompt("  Date (YYYY-MM-DD): ")
        try:
            expense_date: datetime.date = tracker.parse_date(date_input)
            break
        except Exception:
            print("  Invalid date. Use YYYY-MM-DD (e.g., 2025-01-15).")

    # Get category from user
    print("  Category suggestions:", ", ".join(tracker.default_categories))
    expense_category: str = prompt("  Category: ") or "Miscellaneous"

    # Get amount from user
    while True:
        amount_input: str = prompt("  Amount (numbers only): ")
        try:
            expense_amount: Decimal = tracker.parse_amount(amount_input)
            break
        except Exception as error:
            print(f"  {error}. Try again.")

    # Get description from user
    while True:
        expense_description: str = prompt("  Description: ")
        if expense_description.strip():
            break
        print("  Description cannot be empty.")

    # Add expense to tracker
    expense: Expense = tracker.add_expense(expense_date, expense_category, expense_amount, expense_description)

    # Print confirmation message
    print(f"\n  Added: {expense.date} - {expense.category} - {tracker.fmt_money(expense.amount)} - {expense.description}")

def view_expenses_flow(tracker: ExpenseTracker) -> None:
    """
    Displays expenses based on the provided filter.

    Args:
        tracker (ExpenseTracker): The ExpenseTracker instance.

    Returns:
        None
    """
    print("\nView expenses:")
    mode: str = prompt("  Filter by (a)ll, (m)onth, or (c)ategory? [a/m/c]: ").strip().lower() or 'a'
    month: str | None = None; category: str | None = None
    if mode == 'm':
        month = choose_month()
    elif mode == 'c':
        category = prompt("  Enter category: ")
    items: list[Expense] = tracker.list_expenses(month_key=month, category=category)
    if not items:
        print("  No expenses found for the selected filter.")
        return
    print("\n  #  Date        Category        Amount        Description")
    print("  -- ----------- -------------- ------------- ------------------------------")
    for i, e in enumerate(items, start=1):
        amt: str = tracker.fmt_money(e.amount)
        desc: str = (e.description[:28] + '...') if len(e.description) > 30 else e.description
        print(f"  {i:2} {e.date}  {e.category:14} {amt:13} {desc}")
    total: Decimal = tracker.total_expenses(month_key=month)
    scope: str = f"month {month}" if month else (f"category '{category}'" if category else "all")
    print(f"\n  Total for {scope}: {tracker.fmt_money(total)}")

def track_budget_flow(tracker: ExpenseTracker) -> None:
    """
    Tracks the budget for a given month.

    Args:
        tracker (ExpenseTracker): The ExpenseTracker instance.

    Returns:
        None
    """
    print("\nTrack budget:")
    month: str = choose_month()
    action: str = prompt("  (v)iew status or (s)et budget? [v/s]: ").strip().lower() or 'v'
    if action == 's':
        while True:
            amt_str: str = prompt("  Enter monthly budget amount: ")
            try:
                amt: Decimal = tracker.parse_amount(amt_str)
                tracker.set_budget(month, amt)
                print(f"  Budget for {month} set to {tracker.fmt_money(amt)}")
                break
            except Exception as ex:
                print(f"  {ex}. Try again.")
    status: Dict[str, Union[str, Decimal]] = tracker.budget_status(month)
    total: Decimal = Decimal(status['total'])
    if status['budget'] == 'not_set':
        print(f"  No budget set for {month}. Total spent so far: {tracker.fmt_money(total)}")
        return
    budget: Decimal = Decimal(status['budget'])
    remaining: Decimal = Decimal(status['remaining'])
    if status['status'] == 'exceeded_budget':
        print(f"  You have exceeded your budget for {month} by {tracker.fmt_money(-remaining)}.")
    else:
        print(f"  You are within budget for {month}. Remaining: {tracker.fmt_money(remaining)}.")

def save_flow(tracker: ExpenseTracker) -> None:
    """
    Saves expenses and budgets to their respective files.

    Args:
        tracker (ExpenseTracker): The ExpenseTracker instance.

    Returns:
        None
    """
    tracker.save()
    print("  Expenses and budgets saved.")


def main() -> None:
    """
    The main entry point of the application.

    This function initializes the expense tracker, loads previous expenses and budgets,
    and enters a loop to handle user input.

    Returns:
        None
    """
    print(BANNER)
    tracker: ExpenseTracker = ExpenseTracker()
    exp_count: int
    bud_count: int
    exp_count, bud_count = tracker.load()
    print(f"Loaded {exp_count} previous expenses and {bud_count} budgets from disk.")
    while True:
        choice: str = prompt(MENU).strip()
        options: dict[str, callable[[ExpenseTracker], None]] = {
            '1': add_expense_flow,
            '2': view_expenses_flow,
            '3': track_budget_flow,
            '4': save_flow,
            '5': lambda t: (save_flow(t), print("Bye!"))
        }
        if choice in options:
            options[choice](tracker)
            if choice == '5':
                break
        else:
            print("  Invalid option. Please choose 1-5.")

if __name__ == "__main__":
    main()
