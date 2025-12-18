
import socket
import time

class SockBase:
  def __init__(self
    , ip: str=None
    , port: int=None
    , timeout:int=2
  ):
    # -- 接続ポート --
    self.soc_ip = ip
    self.soc_port = port
    self.soc_timeout = timeout

    self.sock = None

  def _do_connect(self, ip: str, port: int, timeout: int):
    """実際のTCP接続処理（内部専用）"""
    try:
      self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.sock.settimeout(self.soc_timeout if timeout is None else timeout)
      self.sock.connect((ip, port))
    except socket.error as e:
      self.sock = None
      raise ConnectionError(f"Connection failed ({ip}:{port}): {e}")

  def connect(self, ip:str=None, port:int=None, timeout:int=None):
    """PLC（または指定のTCPサーバ）に接続します。

    指定がなければ、インスタンス生成時に設定した `soc_ip` と `soc_port` を使用します。
    既に接続済みの場合は、自動的に既存接続を閉じて再接続します。

    Args:
      ip (str, optional): 接続先PLCのIPv4アドレス。指定しない場合はインスタンス設定値を使用。
      port (int, optional): 接続先PLCのポート番号。指定しない場合はインスタンス設定値を使用。
      timeout (int, optional): 通信タイムアウト（秒）。指定しない場合はインスタンス設定値を使用。

    Raises:
      ValueError: IPまたはポートが指定されていない場合。
      ConnectionError: TCP接続に失敗した場合。
    """
    ip = ip or self.soc_ip
    port = port or self.soc_port
    timeout = timeout if timeout is not None else self.soc_timeout
    
    if ip is None or port is None:
      raise ValueError("IP or port is missing")
    
    # 既に open状態 なら閉じる
    if self.sock:
      self.close()

    self._do_connect(ip, port, timeout)

  def force_connect(self, ip: str = None, port: int = None, timeout: int = None
    , retries: int = 3, delay: float = 1.0
  ):
    """
    強制接続。接続失敗時にリトライします。

    Args:
      ip, port, timeout: connect() と同様
      retries(int): リトライ回数
      delay(float): リトライ間隔 (秒)
    """
    ip = ip or self.soc_ip
    port = port or self.soc_port
    timeout = timeout if timeout is not None else self.soc_timeout
    
    last_exc = None
    for attempt in range(1, retries + 1):
      try:
        self.connect(ip, port, timeout)
        return # 正常した場合
      except ConnectionError as e:
        last_exc = e
        self.close()
        time.sleep(delay)
    
    raise ConnectionError(f"force_connect failed after {retries} attempts: {last_exc}")

  def close(self):
    """PLCとの通信切断
    """
    if self.sock:
      try:
        self.sock.close()
      except Exception:
        pass
      finally:
        self.sock = None

  def shutdown(self, how: int=socket.SHUT_RDWR):
    """ソケットをシャットダウンします。

    Args:
        how (int, optional): シャットダウン方法。デフォルトは socket.SHUT_RDWR。
    """
    if self.sock:
      try:
        self.sock.shutdown(how)
      except Exception:
        pass
      finally:
        self.sock = None

  def __enter__(self):
    self.connect(ip=self.soc_ip, port=self.soc_port)
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    self.close()
