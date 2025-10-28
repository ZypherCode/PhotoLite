import math
def find(width, height):
    common_divisor = math.gcd(width, height)

    # Упрощаем дробь
    ratio_width = width // common_divisor
    ratio_height = height // common_divisor

    return f"{ratio_width}:{ratio_height}"

print(find(1920, 1080))