
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Dict, Tuple
import csv
import json
import os

RUPEE = '\u20B9'

@dataclass
class Expense:
    date: date
    category: str
    amount: Decimal
    description: str

    @staticmethod
    def from_row(row: Dict[str, str]) -> "Expense":
        if not row:
            raise ValueError("Input row cannot be empty")

        try:
            date_str = row.get("date")
            if not date_str:
                raise ValueError("Missing date")
            d = datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
        except (KeyError, Exception) as e:
            raise ValueError("Invalid date format") from e

        category = row.get("category")
        if not category:
            raise ValueError("Missing category")
        category = category.strip()

        desc = row.get("description")
        if not desc:
            raise ValueError("Missing description")
        desc = desc.strip()

        try:
            amt_str = row.get("amount")
            if not amt_str:
                raise ValueError("Missing amount")
            amt = Decimal(str(amt_str).strip())
        except (InvalidOperation, AttributeError, KeyError) as e:
            raise ValueError("Invalid amount") from e

        if amt <= 0:
            raise ValueError("Amount must be positive")

        return Expense(date=d, category=category, amount=amt, description=desc)

    def to_row(self) -> Dict[str, str]:
        """
        Converts the Expense object to a dictionary with string values.

        Returns:
            Dict[str, str]: A dictionary containing the date, category, amount, and description of the expense.
        """
        return {
            "date": self.date.strftime("%Y-%m-%d"),
            "category": self.category,
            'amount': format(self.amount, 'f'),
            "description": self.description,
        }

class ExpenseTracker:
    def __init__(self, expenses_path: str = "personal_expense_tracker/data/expenses.csv", budget_path: str = "personal_expense_tracker/data/budget.json") -> None:
        """
        Initializes the ExpenseTracker object.

        Args:
            expenses_path (str): The path to the expenses CSV file. Defaults to "personal_expense_tracker/data/expenses.csv".
            budget_path (str): The path to the budget JSON file. Defaults to "personal_expense_tracker/data/budget.json".

        Returns:
            None
        """
        self.expenses_path: str = expenses_path
        self.budget_path: str = budget_path
        self.expenses: list[Expense] = []
        self.budgets: dict[str, Decimal] = {}
        self.default_categories: list[str] = [
            "Food", "Travel", "Groceries", "Rent", "Utilities", "Bills", "Healthcare",
            "Education", "Entertainment", "Shopping", "Personal Care", "Miscellaneous",
        ]
        os.makedirs(os.path.dirname(self.expenses_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.budget_path), exist_ok=True)

    def load(self) -> tuple[int, int]:
        """Loads expenses and budgets from their respective files.

        Returns:
            tuple[int, int]: A tuple containing the number of expenses and budgets loaded.
        """
        exp_count: int = self._load_expenses()
        bud_count: int = self._load_budgets()
        return exp_count, bud_count

    def save(self) -> None:
        """
        Saves expenses and budgets to their respective files.

        Args:
            None

        Returns:
            None
        """
        self._save_expenses()
        self._save_budgets()

    def _load_expenses(self) -> int:
        """
        Loads expenses from a CSV file.

        Returns:
            int: The number of expenses loaded.

        Raises:
            None
        """
        if not os.path.exists(self.expenses_path):
            return 0
        count: int = 0
        with open(self.expenses_path, newline="", encoding="utf-8") as f:
            reader: csv.DictReader[str] = csv.DictReader(f)
            for row in reader:
                try:
                    exp: Expense = Expense.from_row(row)
                    self.expenses.append(exp)
                    count += 1
                except ValueError:
                    continue
        return count

    def _save_expenses(self) -> None:
        """Saves the expenses to a CSV file.

        Args:
            None

        Returns:
            None
        """
        with open(self.expenses_path, "w", newline="", encoding="utf-8") as f:
            fieldnames: list[str] = ["date", "category", "amount", "description"]
            writer: csv.DictWriter[str] = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for exp in self.expenses:
                writer.writerow(exp.to_row())

    def _load_budgets(self) -> int:
        """
        Loads budgets from a JSON file.

        Returns:
            int: The number of budgets loaded.
        """
        if not os.path.exists(self.budget_path):
            return 0
        try:
            with open(self.budget_path, "r", encoding="utf-8") as f:
                raw: Dict[str, Union[int, float]] = json.load(f)
            self.budgets: Dict[str, Decimal] = {k: Decimal(str(v)) for k, v in raw.items()}
            return len(self.budgets)
        except Exception as e:
            self.budgets: Dict[str, Decimal] = {}
            return 0

    def _save_budgets(self) -> None:
        """Saves the budgets to a JSON file.

        Args:
            None

        Returns:
            None
        """
        with open(self.budget_path, "w", encoding="utf-8") as f:
            json.dump({k: format(v, 'f') for k, v in self.budgets.items()}, f, indent=2)

    @staticmethod
    def _month_key(d: datetime.date) -> str:
        """
        Converts a date to a month key string.

        Args:
            d (datetime.date): The date to be converted.

        Returns:
            str: The month key in the format "YYYY-MM".
        """
        return d.strftime("%Y-%m")

    def add_expense(self, d: date, category: str, amount: Decimal, description: str) -> Expense:
        """
        Adds a new expense to the list.

        Args:
            d (date): The date of the expense.
            category (str): The category of the expense.
            amount (Decimal): The amount of the expense.
            description (str): The description of the expense.

        Returns:
            Expense: The newly added expense.
        """
        exp = Expense(date=d, category=category.strip(), amount=amount, description=description.strip())
        self.expenses.append(exp)
        return exp

    def list_expenses(self, month_key: str | None = None, category: str | None = None) -> list[Expense]:
        """
        Retrieves a list of expenses filtered by month and/or category.

        Args:
            month_key (str | None): The key representing the month (YYYY-MM), or None for all months.
            category (str | None): The category to filter by, or None for all categories.

        Returns:
            list[Expense]: A list of expenses that match the specified filters.
        """
        items = self.expenses
        if month_key:
            items = [e for e in items if self._month_key(e.date) == month_key]
        if category:
            items = [e for e in items if e.category.lower() == category.lower()]
        return items

    def total_expenses(self, month_key: str | None = None) -> Decimal:
        """
        Retrieves the total expenses for a given month or for all months.

        Args:
            month_key (str | None): The key representing the month (YYYY-MM), or None for all months.

        Returns:
            Decimal: The total expenses for the specified month or for all months.
        """
        items: List[Expense] = self.list_expenses(month_key=month_key)
        total: Decimal = sum((e.amount for e in items), Decimal('0'))
        return total

    def set_budget(self, month_key: str, amount: Decimal) -> None:
        """
        Sets the budget for a given month.

        Args:
            month_key (str): The key representing the month (YYYY-MM).
            amount (Decimal): The budget amount.

        Returns:
            None

        Raises:
            ValueError: If the budget amount is not positive.
        """
        if amount <= 0:
            raise ValueError("Budget must be positive")
        self.budgets[month_key] = amount

    def get_budget(self, month_key: str) -> Optional[Decimal]:
        """
        Retrieves the budget amount for a given month.

        Args:
            month_key (str): The key representing the month (YYYY-MM).

        Returns:
            Optional[Decimal]: The budget amount for the specified month, or None if no budget is set.
        """
        return self.budgets.get(month_key)

    def budget_status(self, month_key: str) -> Dict[str, Decimal]:
        """
        Retrieves the budget status for a given month.

        Args:
            month_key (str): The key representing the month (YYYY-MM).

        Returns:
            Dict[str, Decimal]: A dictionary containing the budget status information.
        """
        total = self.total_expenses(month_key)
        budget = self.get_budget(month_key)
        if budget is None:
            return {
                "month": month_key,
                "budget": Decimal('nan'),  # Not a number
                "total": total,
                "remaining": Decimal('nan'),  # Not a number
                "status": "no_budget",
            }
        remaining = budget - total
        status = "within_budget" if remaining >= 0 else "exceeded_budget"
        return {
            "month": month_key,
            "budget": budget,
            "total": total,
            "remaining": remaining,
            "status": status,
        }

    @staticmethod
    def parse_date(value: str) -> datetime.date:
        """
        Converts a string to a date object.

        Args:
            value (str): The date string to be parsed, in the format YYYY-MM-DD.

        Returns:
            datetime.date: The parsed date object.
        """
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()

    @staticmethod
    def parse_amount(value: str) -> Decimal:
        """
        Converts a string to a Decimal amount.

        Args:
            value (str): The amount to be parsed.

        Returns:
            Decimal: The parsed amount.

        Raises:
            ValueError: If the amount is not positive.
        """
        amt: Decimal = Decimal(str(value).strip())
        if amt <= 0:
            raise ValueError("Amount must be positive")
        return amt

    @staticmethod
    def fmt_money(value: Decimal) -> str:
        """
        Formats a Decimal value as a string representing money.

        Args:
            value (Decimal): The amount to be formatted.

        Returns:
            str: A string representation of the amount, prefixed with the Rupee symbol and formatted to two decimal places.
        """
        return f'{RUPEE}{format(value, ",.2f")}'
