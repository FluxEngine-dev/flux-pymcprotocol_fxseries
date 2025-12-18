
import binascii
from typing import Literal
import logging

from pymcprotocol_fxseries.sock_base import SockBase
from pymcprotocol_fxseries.utility import (
  twos_comp,
  get_device_number,
  get_device_type
)
import pymcprotocol_fxseries.type1e_const as const
import pymcprotocol_fxseries.mcprotocol_error as mcprotocolerror

PC_NO_HEX = 0xFF 
WATCH_TIMER_VAL = 0x000A # 2500ms

class Type1E(SockBase):
  """ PLC FXシリーズ 通信用モジュール
  
  Default:
    - デフォルトPC番号:   0xFF
    - デフォルト通信方式: バイナリ
    - PC通信タイムアウト: 2500ms(0x000A)
  
  Public:
    - set_commtype          通信方式
    - set_accessopt:        オプション設定
    - batchread_wordunits:  ワード読み込み
    - batchread_bitunits:   ビット読み込み
    - batchwrite_wordunits: ワード書き込み
    - batchwrite_bitunits:  ビット書き込み
  """

  SOCKBUFSIZE = 4096
  commtype = const.CommType.BINARY
  pc = PC_NO_HEX
  watch_timer = WATCH_TIMER_VAL
  wordsize = 2

  _debug = False

  def __init__(self
    , ip = None
    , port = None
    , timeout=2

    , commtype: Literal["binary", "ascii"]=None
  ):
    super().__init__(ip, port, timeout)
    
    self.logger = logging.getLogger(__class__.__name__)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)-8s] %(asctime)s %(name)s: %(message)s")
    handler.setFormatter(formatter)
    self.logger.addHandler(handler)
    self.logger.setLevel(logging.DEBUG if self._debug else logging.INFO)

    if commtype:
      self.set_commtype(commtype)

  def _set_debug(self, stat: bool):
    self._debug = stat
    self.logger.setLevel(logging.DEBUG if self._debug else logging.INFO)

  # *** (private) ソケット ***

  def _send(self, send_data):
    """sockのデータ送信
    """
    if not self.sock:
        raise ConnectionError("Socket is not connected. Please use connect method")

    if self._debug:
        hex_data = binascii.hexlify(send_data).decode()
        self.logger.debug(f"send data({self.commtype}): {hex_data}")

        if self.commtype == const.CommType.ASCII:
            ascii_chars = "".join(chr(b) for b in send_data)
            self.logger.debug(f"  ASCII: {ascii_chars}")

    self.sock.send(send_data)

  def _recv(self):
    """sockのデータ受信
    """
    recv_data = self.sock.recv(self.SOCKBUFSIZE)
    return recv_data
  
  # *** (private) コマンド作成 ***
  
  def _encode_value(self, value:int, size:int, byteorder="little"):
    try:
      if self.commtype == const.CommType.BINARY:
        value_byte = value.to_bytes(size, byteorder)

      else:
        mask = (1 << (size * 8)) - 1
        value = value & mask
        hex_str = format(value, "0{}X".format(size * 2))
        value_byte = hex_str.encode()
    except:
      raise ValueError("Exceeeded Device value range")
  
    return value_byte
  
  def _decode_value(self, byte:bytes, size:int, byteorder="little"):
    try:
      if self.commtype == const.CommType.BINARY:
        value = int.from_bytes(byte, byteorder)
      else:
        value = int(byte.decode(), 16)
        if byteorder == "big":
          value = twos_comp(value, size)
    except:
      raise ValueError("Could not decode byte to value")
    
    return value

  def _make_device_data(self, device:str):
    """デバイス名 + 先頭デバイス作成

    Args:
      device(str): デバイス. (ex: "D1000", "Y1")

    Returns:
      device_data(bytes): デバイスデータ
    """
    device_data = bytes()

    # デバイス種類取得
    device_type = get_device_type(device)
    # デバイス番号取得
    device_num = int(get_device_number(device))

    if self.commtype == const.CommType.BINARY:
      # デバイス番号コード取得
      device_code = const.DeviceConstants.get_binary_devicecode(device_type)
      
      device_data += device_num.to_bytes(4, "little") # 4byte
      device_data += device_code.to_bytes(2, "little")

    else:
      # デバイス番号コード取得
      device_code = const.DeviceConstants.get_ascii_devicecode(device_type)
      device_num = const.int2hexStr(device_num) # int -> hex -> str -> "0x"を除去

      device_data += device_code.encode()
      device_data += device_num.rjust(8, "0").upper().encode()
    
    return device_data

  def _make_send_data(self, command:int, device:str, size:int):
    """送信データ作成
      [サブヘッダ] [PC番号] [監視タイマ] [先頭デバイス] [デバイス点数] [終了コード]

    Args:
      command(int):      サブヘッダ番号
      device(str):       デバイス名 (ex: "D1000")
      size(int):         データ数

    Returns:
      mc_data(bytes): 送信データ
    """
    mc_data = bytes()

    mc_data += self._encode_value(command, 1)           # サブヘッダ
    mc_data += self._encode_value(self.pc, 1)           # PC番号
    mc_data += self._encode_value(self.watch_timer, 2)  # 監視タイマ
    mc_data += self._make_device_data(device)           # 先頭デバイス
    mc_data += self._encode_value(size, 1)              # デバイス点数
    mc_data += self._encode_value(const.END_CODE, 1)    # 終了コード

    return mc_data

  def _get_answerdata_index(self):
    index = 2 if self.commtype == const.CommType.BINARY else 4
    return index

  def _check_cmd_answer(self, recv_data):
    index = self._get_answerdata_index()

    #   0x00         0x00      0x00 0x00...
    # [subheader] [end code] [char response...]
    status = self._decode_value(recv_data[0:index], 2, "big")
    # 0x80がレスポンス番号 0x0~がコマンド番号
    sub_header = status >> 8 & 0xFF
    end_code =   status & 0xFF
    # mcprotocolerror.check_mcprotocol_error(status)
    if end_code != 0x00:
      raise mcprotocolerror.MCProtocolError(status)
    return None

  # *** (public) PLC通信 ***

  def set_commtype(self, commtype: str):
    """通信方式変更

    Args:
      commtype(str): "binary" もしくは "ascii"
    """
    if commtype == "binary":
      self.commtype = const.CommType.BINARY
      self.wordsize = 2
    elif commtype == "ascii":
      raise ValueError("\"ascii\"による通信は、まだ、未搭載です。")
      
      self.commtype = const.CommType.ASCII
      self.wordsize = 4
    else:
      raise const.CommTypeError()

  def set_accessopt(self
    , commtype: str=None
    , pc :int=None
    , watch_timer: int=None
  ):
    """通信オプション
    
    Args:
      commtype(str):    "binary"もしくは、"ascii" (デフォルト:"binary")
      pc(int):          いや、お前なんなん
      watch_timer(int): PLC通信時のレスポンス待機時間

    """
    if commtype:
      self.set_commtype(commtype)

    if pc:
      try:
        pc.to_bytes(1, "little")
        self.pc = pc
      except:
        raise ValueError("pc must be 0 <= pc <= 255") 

    if watch_timer:
      try:
        watch_timer.to_bytes(2, "little")
        self.watch_timer = watch_timer
      except:
        raise ValueError("timer_sec must be 0 <= timer_sec <= 16383, / sec") 

  def batchread_wordunits(self, headdevice:str, readsize: int) -> list[int]:
    """ワード単位読み込み

    Args:
      headdevice(str):             デバイス名 (ex: "D1000", "Y1")
      readsize(int):               読み込み数

    Returns:
      wordunits_values(list[int]): ワード単位値リスト
    """
    send_data = self._make_send_data(const.Command.WORD_READ, headdevice, readsize)

    self._send(send_data)
    recv_data = self._recv()
    self._check_cmd_answer(recv_data)

    # 取得データ
    word_values = []
    index = self._get_answerdata_index()
    for _ in range(readsize):
      value = self._decode_value(recv_data[index:index+self.wordsize], 2, isSigned=True)
      word_values.append(value)
      index += self.wordsize
    
    return word_values

  def batchread_bitunits(self, headdevice:str, readsize: int):
    """ビット単位読み込み

    Args:
      headdevice(str):             デバイス名 (ex: "D1000", "Y1")
      readsize(int):               読み込み数

    Returns:
      bitunits_values(list[int]):  ビット単位値(0 or 1) リスト
    """
    send_data = self._make_send_data(const.Command.BIT_READ, headdevice, readsize)

    self._send(send_data)
    recv_data = self._recv()
    self._check_cmd_answer(recv_data)

    # 取得データ
    word_values = []
    index = self._get_answerdata_index()
    
    for _ in range((readsize + 1) // 2):
      value = self._decode_value(recv_data[index:index+self.wordsize-1], 1)
      upper_4bit = value >> 4
      word_values.append(upper_4bit)
      lower_4bit = value & 0xF
      word_values.append(lower_4bit)
      index += self.wordsize-1
    
    if readsize % 2 != 0:
      del word_values[-1]
    
    return word_values

  def batchwrite_wordunits(self, headdevice: str, values: list[int]):
    """ワード単位書き込み

    Args:
      headdevice(str):   デバイス名 (ex: "D1000", "Y1")
      values(list[int]): 書き込みリスト list[2byte]
    """
    send_data = self._make_send_data(const.Command.WORD_WRITE, headdevice, len(values))
    # 書き込みデータ
    for v in values:
      send_data += self._encode_value(v, 2)

    self._send(send_data)
    recv_data = self._recv()
    self._check_cmd_answer(recv_data)
    return None

  def batchwrite_bitunits(self, headdevice: str, values: list[int]):
    """ビット単位書き込み
    
    Args:
      headdevice(str):             デバイス名 (ex: "D1000", "Y1")
      values(list[int]):           書き込み1bitリスト
    """
    new_values = []
    
    # 4ビットずつまとめて1バイトに
    for i in range(0, len(values), 2):
      high_nibble = values[i] & 0x0F
      try:
        low_nibble = values[i+1] & 0x0F
      except:
        low_nibble = 0x00
      byte_val = (high_nibble << 4) | low_nibble
      new_values.append(byte_val)

    send_data = self._make_send_data(const.Command.BIT_WRITE, headdevice, len(values))
    # 書き込みデータ
    for v in new_values:
      send_data += self._encode_value(v, 1)

    self._send(send_data)
    recv_data = self._recv()
    self._check_cmd_answer(recv_data)
    return None
