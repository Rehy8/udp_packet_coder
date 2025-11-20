"""Модуль симуляции передачи пакетов данных."""

import random

import hamming_module as hm
import matplotlib.pyplot as plt
import numpy as np

# --- Константы симуляции ---
# Общее количество бит в исходной тестовой
#  последовательности (должно быть кратно 4)
TEST_SEQUENCE_LENGTH = 4000
# Количество раз, которое мы повторяем симуляцию для усреднения
NUM_TRIALS = 10
# Диапазон вероятностей потери пакета для тестирования
PROBABILITY_RANGE = np.linspace(0.0, 1.0, 21)


def simulate_transmission(data_sequence, p_loss):
    """
    Симулирует кодирование, чередование, потерю пакетов и декодирование.

    Args:
        data_sequence (list[int]): Исходные данные (биты).
        p_loss (float): Вероятность потери одного UDP пакета (стирание).

    Returns:
        tuple: (общее_кол-во_исходных_бит, кол-во_восстановленных_бит)

    """
    # 1. Кодирование и Чередование (Клиентская часть)
    blocks = []
    for i in range(0, len(data_sequence), 4):
        blocks.append(hm.encode(data_sequence[i : i + 4]))  # noqa: E203

    interleaved_packets = [[] for _ in range(7)]
    for block in blocks:
        for i in range(7):
            interleaved_packets[i].append(block[i])

    # 2. Симуляция потерь (Серверная часть)
    interleaved_data_with_loss = []
    erasure_indices = []
    lost_packet_count = 0

    for packet_index, packet in enumerate(interleaved_packets):
        # Случайно решаем, потерян ли пакет (стирание)
        if random.random() < p_loss:
            interleaved_data_with_loss.append(None)  # Симуляция потери
            erasure_indices.append(packet_index)
            lost_packet_count += 1
        else:
            interleaved_data_with_loss.append(packet)  # Пакет принят

    # 3. Дечередование и Восстановление
    num_blocks = len(blocks)
    decoded_sequence = []
    recovered_bits = 0

    if num_blocks == 0:
        return 0, 0

    encoded_blocks_with_erasures = [[] for _ in range(num_blocks)]

    # Дечередование
    for block_index in range(num_blocks):
        for packet_index in range(7):
            packet = interleaved_data_with_loss[packet_index]
            if packet is None:
                encoded_blocks_with_erasures[block_index].append(None)
            else:
                encoded_blocks_with_erasures[block_index].append(
                    packet[block_index]
                )

    # Декодирование с восстановлением стираний
    for i, block_with_erasures in enumerate(encoded_blocks_with_erasures):
        decoded_block = hm.decode_with_erasures(
            block_with_erasures, erasure_indices
        )
        decoded_sequence.extend(decoded_block)

        # Считаем, сколько битов было восстановлено правильно
        if decoded_block == data_sequence[i * 4 : i * 4 + 4]:  # noqa: E203
            recovered_bits += 4

    return len(data_sequence), recovered_bits


def run_simulation():
    """Проводит симуляцию и строит график."""
    print(
        f'Запуск симуляции. Длина данных: {TEST_SEQUENCE_LENGTH} бит. '
        f'Повторений: {NUM_TRIALS}'
    )

    # Генерируем тестовую последовательность (случайные биты)
    data_sequence = [random.randint(0, 1) for _ in range(TEST_SEQUENCE_LENGTH)]

    results_restored_bits = []

    for p_loss in PROBABILITY_RANGE:
        total_restored_percent = 0

        # Повторяем симуляцию несколько раз для усреднения
        for _ in range(NUM_TRIALS):
            total_bits, restored_bits = simulate_transmission(
                data_sequence, p_loss
            )
            if total_bits > 0:
                total_restored_percent += (restored_bits / total_bits) * 100

        avg_restored_percent = total_restored_percent / NUM_TRIALS
        results_restored_bits.append(avg_restored_percent)
        print(
            f'Вероятность потери пакета: {p_loss * 100:.1f}%. '
            f'Средний процент восстановления: {avg_restored_percent:.2f}%'
        )

    # Построение графика
    plt.figure(figsize=(10, 6))
    plt.plot(
        PROBABILITY_RANGE * 100,
        results_restored_bits,
        marker='o',
        linestyle='-',
        color='b',
    )
    plt.title(
        'Зависимость % восстановления данных от % потери пакетов', fontsize=16
    )
    plt.xlabel('% Потери UDP-пакетов (P_loss)', fontsize=14)
    plt.ylabel('% Успешное восстановленние', fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.axhline(y=100, color='g', linestyle='-')
    plt.axvline(
        x=2 / 7 * 100,
        color='r',
        linestyle='--',
        label=f'Теоретический предел восстановления (2/7={2 / 7 * 100:.1f}%)',
    )
    plt.legend()
    plt.show()


if __name__ == '__main__':
    run_simulation()
