import os
import time
from pathlib import PurePath

rootdir = PurePath('/sys/class/gpio')

def read_file(path):
  with open(path, 'r') as f:
    return f.read()

def read_int_file(path):
  return int(read_file(path))

def write_file(path, value):
  with open(path, 'w') as f:
    return f.write(value)

def write_int_file(path, value):
  write_file(path, str(value))

chips = sorted([
  (
    de.name,
    base,
    ngpio,
    range(base, base + ngpio),
  )
  for de in os.scandir(rootdir)
  if de.name.startswith('gpiochip')
  for base, ngpio in [(
    read_int_file(rootdir / de.name / 'base'),
    read_int_file(rootdir / de.name / 'ngpio'),
  )]
], key = lambda chip: chip[1])

pins = sorted([pin for name, base, ngpio, pins in chips for pin in pins])

print(chips)
print(pins)

def select_pin(pin):
  if pin >= 190 and pin < 200:
    raise Exception(f'Pin {pin} in crash range 190..199')
def export(pin):
  write_int_file(rootdir / 'export', pin)
def unexport(pin):
  write_int_file(rootdir / 'unexport', pin)
def set_out(pin):
  write_file(rootdir / f'gpio{pin}' / 'direction', 'out')
def set_1(pin):
  write_int_file(rootdir / f'gpio{pin}' / 'value', 1)
def set_0(pin):
  write_int_file(rootdir / f'gpio{pin}' / 'value', 0)

def scan():
  for pin in pins:
    error = None
    error_action = None
    def try_action(action):
      nonlocal error
      nonlocal error_action
      try:
        action(pin)
      except Exception as e:
        if error is None:
          error = e
          error_action = action
        raise
    try:
      try_action(select_pin)
      try_action(export)
      try:
        try_action(set_out)
        try_action(set_1)
        print(f'Pin {pin}=1')
        time.sleep(1)
        try_action(set_0)
        print(f'Pin {pin}=0')
        time.sleep(1)
      finally:
        try_action(unexport)
    except:
      pass
    finally:
      print(f'''Pin {pin}: {'OK' if error is None else f'{error_action.__name__} {error}'}''')
      time.sleep(0.2)

# scan()

# pins = range(118, 120)
# scan()

from gpio4 import GPIO

gpio = GPIO()

heartbeat_pin = 'PD23'
warm_out_pin = 'PG10'
cold_out_pin = 'PG14'
warm_in_pin = 'PD21'
cold_in_pin = 'PG12'

gpio.setup([heartbeat_pin], ['out'])
gpio.setup([warm_out_pin], ['out'])
gpio.setup([cold_out_pin], ['out'])
gpio.setup([warm_in_pin], ['in'])
gpio.setup([cold_in_pin], ['in'])

class Counter:
  def __init__(self, name, input_pin, output_pin):
    self.name = name
    self.input_pin = input_pin
    self.output_pin = output_pin
    self.value = None
    self.count = 0
  def check(self):
    value = int(gpio.input(self.input_pin))
    if value != self.value:
      if value == 1 and self.value == 0:
        self.count += 1
      print(f'{time.time()} {self.name} ({self.count}): {self.value}->{value}')
      self.value = value
      gpio.output(self.output_pin, self.value)

warm = Counter('warm', warm_in_pin, warm_out_pin)
cold = Counter('cold', cold_in_pin, cold_out_pin)

while True:
  warm.check()
  cold.check()
  time.sleep(0.05)
  gpio.output(heartbeat_pin, 1 - int(gpio.input(heartbeat_pin)))

# # green - heartbeat
# pin = 'PD23'
# gpio.setup([pin], ['out'])
# gpio.output(pin, 0)
# time.sleep(1)
# gpio.output(pin, 1)
# time.sleep(1)
# gpio.output(pin, 0)
# time.sleep(1)

# # orange - warm out
# pin = 'PG10'
# gpio.setup([pin], ['out'])
# gpio.output(pin, 0)
# time.sleep(1)
# gpio.output(pin, 1)
# time.sleep(1)
# gpio.output(pin, 0)
# time.sleep(1)

# # purple - cold out
# pin = 'PG14'
# gpio.setup([pin], ['out'])
# gpio.output(pin, 0)
# time.sleep(1)
# gpio.output(pin, 1)
# time.sleep(1)
# gpio.output(pin, 0)
# time.sleep(1)

# # red - warm in
# pin = 'PD21'
# gpio.setup([pin], ['in'])
# while True:
#   print(gpio.input(pin))
#   time.sleep(0.1)

# # blue - cold in
# pin = 'PG12'
# gpio.setup([pin], ['in'])
# while True:
#   print(gpio.input(pin))
#   time.sleep(0.1)

