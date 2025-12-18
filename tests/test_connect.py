
from pymcprotocol_fxseries import Type1E

if __name__ == '__main__':
  try:
    PLC_IP = '127.0.0.1'
    # PLC_IP = '192.168.1.10'
    PORT = 5000

    with Type1E(PLC_IP, port=PORT) as client:
      client._set_debug(True)

      print('>> binary 送信方式')
      client.set_commtype('binary')
      # print('* ワード読み込み')
      # values = client.batchread_wordunits(headdevice='D0', readsize=5)
      # print(f'read: {values}')
      print('* ワード書き込み')
      client.batchwrite_wordunits(headdevice='D700', values=[ 0x0001 ])
      # print('* ビット読み込み')
      # values = client.batchread_bitunits(headdevice='M700', readsize=10)
      # print(f'read: {values}')
      # print('* ビット書き込み')
      # client.batchwrite_bitunits(headdevice='M700', values=[ 1, 1, 1, 0, 1])

      # print('>> ascii 送信方式')
      # client.set_commtype('ascii')
      # print('* ワード読み込み')
      # values = client.batchread_wordunits(headdevice='D0', readsize=5)
      # print(f'read: {values}')
      # print('* ワード書き込み')
      # client.batchwrite_wordunits(headdevice='M100', values=[ 0x1122,0x3344,0x5566,0x7788,0x99AA ])
      # print('* ビット読み込み')
      # values = client.batchread_bitunits(headdevice='D0', readsize=5)
      # print(f'read: {values}')
      # print('* ビット書き込み')
      # client.batchwrite_bitunits(headdevice='M100', values=[ 1, 1, 0, 0, 1])

  except Exception as e:
    print(f'例外: {e}')