import socket
import struct
import threading

DEVICE_CODE_MAP = {
  0x4420: 'D',
  0x5220: 'R',
  0x4D20: 'M',
}

def is_ascii_frame(data: bytes) -> bool:
  """最初の1バイトで ASCII かどうか判定"""
  return not (data[0] <= 0x0F)

def ascii_to_binary(data: bytes) -> bytes:
  """ASCII形式 (例: b'01FF000A...') → バイナリに変換"""
  try:
    hex_str = data.strip().decode()
    return bytes.fromhex(hex_str)
  except Exception:
    raise ValueError("Invalid ASCII hex frame")


def parse_request(data: bytes) -> dict:
  """
  バイナリ1フレームを解析する（ASCIIは事前に変換する）
  """
  if len(data) < 12:
    raise ValueError("Frame too short")

  subheader   = data[0]
  pc_no     = data[1]
  watch_timer  = struct.unpack('>H', data[2:4])[0]
  address    = struct.unpack('<I', data[4:8])[0]
  dev_code   = struct.unpack('<H', data[8:10])[0]
  size     = data[10]
  end_code   = data[11]

  dev_char = DEVICE_CODE_MAP.get(dev_code, '?')

  write_data = []
  if len(data) > 12:
    pos = 12
    for i in range(size):
      val = struct.unpack_from('>H', data, pos + i * 2)[0]
      write_data.append(val)

  return {
    "subheader": subheader,
    "pc_no": pc_no,
    "watch_timer": watch_timer,
    "address": address,
    "dev_code": dev_code,
    "dev_char": dev_char,
    "size": size,
    "end_code": end_code,
    "write_data": write_data,
    "raw_hex": data.hex()
  }


def print_parsed_info(info: dict):
  print("------ Request Frame ------")
  print(f" RAW HEX       : {info['raw_hex']}")
  print(f" Subheader     : 0x{info['subheader']:02X}")
  print(f" PC No         : 0x{info['pc_no']:02X}")
  print(f" Watch Timer   : {info['watch_timer']} (0x{info['watch_timer']:04X})")
  print(f" Address       : {info['address']} (0x{info['address']:08X})")
  print(f" Device Code   : 0x{info['dev_code']:04X} → {info['dev_char']}")
  print(f" Size          : {info['size']}")
  print(f" End Code      : 0x{info['end_code']:02X}")
  if info['write_data']:
    print(f" Write Data     : {[hex(v) for v in info['write_data']]}")
  print("----------------------------\n")


def build_response_ok(values: list[int]):
  header = bytes([0x00, 0x00])
  body = b''.join(v.to_bytes(2, 'little') for v in values)
  return header + body


def handle_client(conn, addr):
  print(f"[SERVER] Client connected: {addr}")

  while True:
    try:
      data = conn.recv(4096)
      if not data:
        break

      # 通信モード判定
      if is_ascii_frame(data):
        print("[SERVER] ASCII Frame detected")
        data = ascii_to_binary(data)
      else:
        print("[SERVER] Binary Frame detected")

      req = parse_request(data)
      print_parsed_info(req)

      dev = req["dev_char"]
      address = req["address"]
      size = req["size"]

      if req["subheader"] == 0x01:
        print("[SERVER] READ request")
        values = [address + i for i in range(size)]
        resp = build_response_ok(values)
        conn.send(resp)
        print(f"[SERVER] RESP HEX : {resp.hex()}\n")

      elif req["subheader"] == 0x03:
        print("[SERVER] WRITE request")
        conn.send(bytes([0x00, 0x00]))

      else:
        conn.send(bytes([0x00, 0x55]))

    except Exception as e:
      print("Error:", e)
      break

  conn.close()
  print(f"[SERVER] Client disconnected: {addr}")


def start_server(host="0.0.0.0", port=5000):
  print(f"[SERVER] Start server {host}:{port}")

  server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  server.bind((host, port))
  server.listen()
  server.settimeout(1.0)

  try:
    while True:
      try:
        conn, addr = server.accept()
        th = threading.Thread(target=handle_client, args=(conn, addr))
        th.daemon = True
        th.start()
      except socket.timeout:
        pass
  except KeyboardInterrupt:
    print("\n[SERVER] KeyboardInterrupt - shutting down server")
  finally:
    server.close()


if __name__ == "__main__":
  start_server()
