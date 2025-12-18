
class Command:
  BIT_READ   = 0x00  # ビット一括読み出し
  WORD_READ  = 0x01  # ワード一括読み出し
  BIT_WRITE  = 0x02  # ビット一括書き込み
  WORD_WRITE = 0x03  # ワード一括書き込み

END_CODE = 0x00  # リクエストフォーマット 終了位置コード

class CommType:
  BINARY = "binary"
  ASCII  = "ascii"

class CommTypeError(Exception):
  def __init__(self):
      pass
  
  def __str__(self):
    return f"communication type must be \"{CommType.BINARY}\" or \"{CommType.ASCII}\""

class DeviceCodeError(Exception):
  def __init__(self, devicename):
    self.devicename = devicename
  
  def __str__(self):
    error_txt = f"devicename: {self.devicename} is not support.\n"
    return error_txt

def int2hexStr(val):
  s_hex = hex(val)          # "0x..."に変換
  s_hex_digits = s_hex[2:]  # "0x"以外
  # 桁が奇数の場合,"0"埋めにする
  if len(s_hex_digits) % 2 != 0:
    s_hex_digits = "0" + s_hex_digits
  return s_hex_digits # リスト

class DeviceConstants:
  #         command, sub command
  D_DEVICE =  [ 0x44, 0x20 ]  # データレジスタ
  R_DEVICE =  [ 0x52, 0x20 ]  # 拡張レジスタ
  TN_DEVICE = [ 0x54, 0x4E ]  # タイマ現在値 (TN)
  TS_DEVICE = [ 0x54, 0x53 ]  # タイマ接点 (TS)
  CN_DEVICE = [ 0x43, 0x4E ]  # カウンタ現在値 (CN)
  CS_DEVICE = [ 0x43, 0x53 ]  # カウンタ接点 (CS)
  X_DEVICE =  [ 0x58, 0x20 ]  # 入力
  Y_DEVICE =  [ 0x59, 0x20 ]  # 出力
  M_DEVICE =  [ 0x4D, 0x20 ]  # 補助リレー
  S_DEVICE =  [ 0x53, 0x20 ]  # ステート

  @staticmethod
  def _table():
    return {
      "D":  DeviceConstants.D_DEVICE,
      "R":  DeviceConstants.R_DEVICE,
      "TN": DeviceConstants.TN_DEVICE,
      "TS": DeviceConstants.TS_DEVICE,
      "CN": DeviceConstants.CN_DEVICE,
      "CS": DeviceConstants.CS_DEVICE,
      "X":  DeviceConstants.X_DEVICE,
      "Y":  DeviceConstants.Y_DEVICE,
      "M":  DeviceConstants.M_DEVICE,
      "S":  DeviceConstants.S_DEVICE,
    }

  @staticmethod
  def get_binary_devicecode(devicename):
    """デバイス種類から適切なデバイスコードをバイナリコードで返す
    
    Args:
      devicename(str): デバイス種類

    Returns:
      device_code(int): デバイスコード
        ※ 2byte 上位:コマンド 下位:サブコマンド
    """
    table = DeviceConstants._table()

    if devicename not in table:
      raise DeviceCodeError(devicename)
    
    cmd, sub = table[devicename]
    return (cmd << 8) | sub

  @staticmethod
  def get_ascii_devicecode(devicename):
    table = DeviceConstants._table()

    if devicename not in table:
      raise DeviceCodeError(devicename)

    cmd, sub = table[devicename]
    return f"{cmd:02X}{sub:02X}"
