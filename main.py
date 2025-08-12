# SPDX-FileCopyrightText: 2025 Toyomasa Watarai <toyomasa.watarai@gmail.com>
# SPDX-License-Identifier: Apache-2.0

from microbit import *
from array import array

note_table = array("b", [
    60,
    62, 
    64, 
    65,
    67,
    69,
    71,
    72,
    74,
    76,
    77,
    79
])

drum_table = array("b", [
    35,
    38,
    39,
    40,
    41,
    42,
    43,
    44,
    45,
    46,
    47,
    48
])

# channel
channel_table = array("b", [
    9,
    1,
    2,
    3,
    4,
])

uart.init(baudrate=31250, tx=pin0, rx=None)
for i in range(1, 16):
    uart.write(bytes([0xB0 + i, 0x07, 0x7F]))
uart.write(bytes([0xC1, 1]))
uart.write(bytes([0xC2, 17]))
uart.write(bytes([0xC3, 25]))
uart.write(bytes([0xC4, 33]))
uart.write(bytes([0xC5, 41]))

# print('MPR121 test code')
# for Seeed GROVE 12-key Capacitive I2C Touch Sensor V3
I2C_ADRS = 0x5B
i2c.init(freq=400000, sda=pin20, scl=pin19)
i2c.write(I2C_ADRS, bytes([0x80, 0x63]))
i2c.write(I2C_ADRS, bytes([0x2B, 0x01]))
i2c.write(I2C_ADRS, bytes([0x2C, 0x01]))
i2c.write(I2C_ADRS, bytes([0x2D, 0x00]))
i2c.write(I2C_ADRS, bytes([0x2E, 0x00]))
i2c.write(I2C_ADRS, bytes([0x2F, 0x01]))
i2c.write(I2C_ADRS, bytes([0x30, 0x01]))
i2c.write(I2C_ADRS, bytes([0x31, 0xFF]))
i2c.write(I2C_ADRS, bytes([0x32, 0x02]))

E0TTH = 0x41  # タッチ閾値の開始レジスタ
E0RTH = 0x42  # リリース閾値の開始レジスタ
# タッチ閾値の設定
for i in range(0, 12 * 2, 2):
    i2c.write(I2C_ADRS, bytes([E0TTH + i, 0x20]))  # 奇数レジスタに0x20を書き込み

# リリース閾値の設定
for i in range(0, 12 * 2, 2):
    i2c.write(I2C_ADRS, bytes([E0RTH + i, 0x10]))  # 偶数レジスタに0x10を書き込み

# Debounce Register DR=b6...4, DT=b2...0
i2c.write(I2C_ADRS, bytes([0x5B, 0x11]))
    
# Filter and Global CDC CDT Configuration (sample time, charge current)
i2c.write(I2C_ADRS, bytes([0x5C, 0x10]))
i2c.write(I2C_ADRS, bytes([0x5D, 0x20]))
    
# Auto-Configuration Registers
# http://cache.freescale.com/files/sensors/doc/app_note/AN3889.pdf
i2c.write(I2C_ADRS, bytes([0x7B, 0x33]))
i2c.write(I2C_ADRS, bytes([0x7C, 0x07]))
i2c.write(I2C_ADRS, bytes([0x7D, 0xC9]))
i2c.write(I2C_ADRS, bytes([0x7E, 0x83]))
i2c.write(I2C_ADRS, bytes([0x7F, 0xB5]))

# Electrode Configuration Register - enable all 12 and start
i2c.write(I2C_ADRS, bytes([0x5E, 0x8F]))

pin14.set_pull(pin14.PULL_UP)
prev_reg_val = 0
ch = 0
display.set_pixel(ch, 4, 1)

def on_falling_edge(channel):
    global prev_reg_val
    i2c.write(I2C_ADRS, bytes([0]), repeat=True)
    low = int.from_bytes(i2c.read(I2C_ADRS, 1), 'little')
    i2c.write(I2C_ADRS, bytes([1]), repeat=True)
    high = int.from_bytes(i2c.read(I2C_ADRS, 1), 'little')
    reg_val = low | (high << 8)
    sleep(1)
    i2c.write(I2C_ADRS, bytes([2]), repeat=True)
    low = int.from_bytes(i2c.read(I2C_ADRS, 1), 'little')
    i2c.write(I2C_ADRS, bytes([3]), repeat=True)
    high = int.from_bytes(i2c.read(I2C_ADRS, 1), 'little')
    oor_val = low | (high << 8)
    if (oor_val != 0):
        reset()
    
    for i in range(12):
        bit_ptn = reg_val & (1 << i)
        # if(reg_val & (1 << i)):
        if (bit_ptn != 0):
            if (i < 5):
                display.set_pixel(i, 0, 1)
            elif (i < 10):
                 display.set_pixel(i-5, 1, 1)
            elif (i < 12):
                 display.set_pixel(i-10, 2, 1)
            if((bit_ptn & prev_reg_val) == False):
                if (channel == 9):
                    uart.write(bytes([0x90 + channel, drum_table[i], 100]))
                else:
                    uart.write(bytes([0x90 + channel, note_table[i], 100]))
        else:
            if (i < 5):
                display.set_pixel(i, 0, 0)
            elif (i < 10):
                 display.set_pixel(i-5, 1, 0)
            elif (i < 12):
                 display.set_pixel(i-10, 2, 0)
            if (channel == 9):
                uart.write(bytes([0x80 + channel, drum_table[i], 0]))
            else:
                uart.write(bytes([0x80 + channel, note_table[i], 0]))
    prev_reg_val = reg_val
    return reg_val

while True:
    current_state = pin14.read_digital()
    if current_state == 0:
        btn = on_falling_edge(channel_table[ch])
    if button_a.was_pressed():
        ch += 1
        if (ch >= len(channel_table)):
            ch = 0
        for i in range(5):
            if (i == ch):
                display.set_pixel(i, 4, 1)
            else:
                display.set_pixel(i, 4, 0)
        sleep(100)
    elif button_b.is_pressed():
        reset()
    sleep(1)
