"""All functions."""

import random

import numpy as np

# Матрица проверки H (3x7)
H = np.array(
    [
        [1, 0, 1, 0, 1, 0, 1],
        [0, 1, 1, 0, 0, 1, 1],
        [0, 0, 0, 1, 1, 1, 1],
    ]
)

# Матрица кодирования G (7x4)
G = np.array(
    [
        [1, 1, 0, 1],
        [1, 0, 1, 1],
        [1, 0, 0, 0],
        [0, 1, 1, 1],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1],
    ]
)


def encode(data: list[int]) -> list[int]:
    """Кодирование кода Хэмминга (7,4)."""
    if len(data) != 4:
        raise ValueError('Должно быть ровно 4 бита данных')

    data_vector = np.array(data)
    encoded_vector = np.dot(G, data_vector) % 2
    return encoded_vector.tolist()


def decode(encoded: list[int]) -> list[int]:
    """Декодирование и исправление ошибки."""
    if len(encoded) != 7:
        raise ValueError(
            'Закодированные данные должны содержать ровно 7 битов'
        )

    encoded_vector = np.array(encoded).reshape(7, 1)
    syndrome = np.dot(H, encoded_vector) % 2

    # Синдром H * r^T (mod 2)
    s = syndrome.flatten().tolist()
    # syndrome = s[0]*4 + s[1]*2 + s[2]*1 (если H транспонирована)
    # Текущий порядок в H соответствует: s[2]*4 + s[1]*2 + s[0]*1
    error_pos = s[0] * 1 + s[1] * 2 + s[2] * 4

    corrected = encoded.copy()
    if error_pos != 0:
        # print(f'Обнаружена ошибка в позиции: {error_pos}')
        corrected[error_pos - 1] ^= 1

    # Извлекаем информационные биты (позиции 3, 5, 6, 7 -> индексы 2, 4, 5, 6)
    decoded = [corrected[2], corrected[4], corrected[5], corrected[6]]
    return decoded


def introduce_packet_loss(blocks: list[list[int]]):
    """
    Симулирует потерю 2 из 7 пакетов (строк/элементов).

    Потерянные пакеты заменяются на None.
    """
    if len(blocks) != 7:
        raise ValueError('Требуется ровно 7 блоков для симуляции потерь.')

    lost_indices = random.sample(range(7), 2)
    lost_indices.sort()

    # Создаем копию списка, заменяя утерянные элементы на None
    lost_blocks = blocks[:]
    for index in lost_indices:
        lost_blocks[index] = None

    print(
        f'Симуляция потерь: Утеряны пакеты с индексами (0-6): {lost_indices}'
    )
    return lost_blocks, lost_indices


def decode_with_erasures(
    encoded_with_erasures: list, erasures: list[int]
) -> list[int]:
    """Восстановление до двух стираний в коде Хэмминга (7,4)."""
    # Заменяем None на 0 для вычисления синдрома (стирания считаются нулями)
    encoded = np.array(
        [0 if x is None else x for x in encoded_with_erasures], dtype=float
    )

    known_positions = [i for i in range(7) if i not in erasures]
    unknown_positions = erasures

    if len(unknown_positions) > 2:
        # Если более двух стираний, восстановление невозможно.
        return [0, 0, 0, 0]

    # Разделяем матрицу H
    h_known = H[:, known_positions]
    h_unknown = H[:, unknown_positions]
    # Синдром для неизвестных битов
    known_bits = encoded[known_positions]
    syndrome = (-np.dot(h_known, known_bits) % 2).reshape(3, 1)

    # Решаем систему H_unknown * x = syndrome (mod 2)
    best_solution = None

    # Перебор всех 2^k комбинаций для k стираний
    for guess in np.ndindex(*(2,) * len(unknown_positions)):
        trial = np.array(guess).reshape(len(unknown_positions), 1)
        if np.array_equal(np.dot(h_unknown, trial) % 2, syndrome % 2):
            best_solution = trial.flatten()
            break

    if best_solution is not None:
        recovered = encoded.copy()
        for i, val in zip(unknown_positions, best_solution):
            recovered[i] = int(val)
    else:
        # Если решение не найдено (маловероятно при <=2 стираниях в (7,4))
        recovered = encoded.copy()

    # Извлекаем информационные биты (позиции 3, 5, 6, 7 -> индексы 2, 4, 5, 6)
    decoded = [
        int(recovered[2]),
        int(recovered[4]),
        int(recovered[5]),
        int(recovered[6]),
    ]
    return decoded


if __name__ == '__main__':
    # 1. Исходные данные
    original_data = [0, 1, 0, 1]
    print(f'Исходные данные: {original_data}')

    # 2. Кодирование
    encoded = encode(original_data)
    print(f'Закодировано (7 бит): {encoded}')

    # --- Сценарий А: Ошибка бита (Flip) ---
    print('\n--- Сценарий 1: Бит перевернулся ---')
    corrupted = encoded.copy()
    corrupted[2] ^= 1  # Инвертируем бит по индексу 2
    print(f'Испорчено:     {corrupted}')
    decoded = decode(corrupted)
    print(f'Восстановлено: {decoded}')

    # --- Сценарий Б: Потеря пакетов (Erasure) ---
    print('\n--- Сценарий 2: Потеря пакетов ---')
    # Симулируем потерю
    erased_blocks, lost_indices = introduce_packet_loss(encoded)
    print(f'С потерями:    {erased_blocks}')

    # Восстанавливаем
    recovered = decode_with_erasures(erased_blocks, lost_indices)
    print(f'Восстановлено: {recovered}')
