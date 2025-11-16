"""
Dice Rolling Utilities
Supports expressions like "d6+2", "d8+3", "d10+5"
"""
import random
import re


def roll_dice(expression):
    """
    Roll dice based on expression

    Args:
        expression: String like "d6+2", "2d8+3", "d10"

    Returns:
        Integer result of the roll
    """
    if not expression or not isinstance(expression, str):
        return 0

    expression = expression.strip().lower()

    # Parse expression: XdY+Z or dY+Z
    match = re.match(r'(?:(\d+))?d(\d+)(?:([+\-])(\d+))?', expression)
    if not match:
        return 0

    num_dice = int(match.group(1)) if match.group(1) else 1
    die_size = int(match.group(2))
    operator = match.group(3)
    modifier = int(match.group(4)) if match.group(4) else 0

    # Roll the dice
    total = sum(random.randint(1, die_size) for _ in range(num_dice))

    # Apply modifier
    if operator == '+':
        total += modifier
    elif operator == '-':
        total -= modifier

    return max(0, total)  # Never return negative


def test_dice():
    """Test dice rolling"""
    print("Testing dice rolling:")
    for _ in range(5):
        print(f"  d6+2: {roll_dice('d6+2')}")
    for _ in range(5):
        print(f"  d8+3: {roll_dice('d8+3')}")
    for _ in range(5):
        print(f"  2d10+5: {roll_dice('2d10+5')}")


if __name__ == '__main__':
    test_dice()
