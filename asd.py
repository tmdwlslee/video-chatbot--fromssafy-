import chardet

euc_data = '손흥민골'.encode('utf-8')
print( euc_data )

# 인코딩 알아내기
print (chardet.detect (euc_data))