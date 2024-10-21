#%%
from binascii import hexlify, unhexlify 
response = b'\xfe\x03\x06\x01\x91\x00(\x01;X\xc6'
hx = hexlify(response)

#%%
# from itertools import tee

# def pairwise(iterable):
#     "s -> (s0,s1), (s1,s2), (s2, s3), ..."
#     a, b = tee(iterable)
#     next(b, None)
#     return zip(a, b)

# #%%
# for a,b in pairwise(hx):
#     print(bytes.fromhex(str(a)+str(b)), 'big')
# # %%
# print(hx)
# %%

class modbus_message:
    def __init__(self, raw_data) -> None:
        self.raw_data = hexlify(raw_data)
        self.station_address = self.raw_data[0:2]
        self.function_code = self.raw_data[2:4]  
        self.n_bytes = self.raw_data[4:6]
        self.data = self.raw_data[6:-2]
        self.crc = self.raw_data[-2:]

class ph_response(modbus_message):
    def __init__(self, raw_data) -> None:
        super().__init__(raw_data)
        self.ph_high_res_raw = self.data[0:4]
        self.ph_low_res_raw = self.data[4:8]
        self.temperature_raw = self.data[8:12]
        self.temperature = int.from_bytes(unhexlify(self.temperature_raw), byteorder='big')/10
        self.ph_high_res = int.from_bytes(unhexlify(self.ph_high_res_raw), byteorder='big')/100
        self.ph_low_res = int.from_bytes(unhexlify(self.ph_low_res_raw), byteorder='big')/10


# %%
ph = ph_response(response)
print(ph.ph_high_res)
print(ph.ph_low_res)
print(ph.temperature)
# %%
