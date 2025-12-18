import re

def twos_comp(val, size:int):
  """compute the 2's complement of int value val
  """
  bit = size * 8
  if (val & (1 << (bit - 1))) != 0: # if sign bit is set e.g., 8bit: 128-255
    val = val - (1 << bit)        # compute negative value
  return val

def get_device_number(device:str) -> str:
  """デバイスからデバイス番号を取得

  Args:
    device(str):        デバイス名
  
  Returns:
    device_num(str) デバイス番号
  """
  device_num = re.search(r"\d.*", device)
  if device_num is None:
    raise ValueError("Invalid device number, {}".format(device))
  else:
    device_num = device_num.group(0)
  return device_num

def get_device_type(device:str) -> str:
  """デバイスからデバイス種類を取得

  Args:
    device(str):        デバイス名
  
  Returns:
    devicetype(str) デバイス種類
  """
  devicetype = re.search(r"\D+", device)
  if devicetype is None:
    raise ValueError("Invalid device ")
  else:
    devicetype = devicetype.group(0)  
  return devicetype
