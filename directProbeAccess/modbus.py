from binascii import hexlify
from .CRC16MODBUS import CRC16
from .errorlog import error_log

crc = CRC16()
log = error_log(tag="modbus")

class modbus_exception(Exception):
    def __init__(self, message) -> None:
        self.message = message
    def __str__(self) -> str:
        return f"Modbus Exception: {self.message}"

class parse_error(modbus_exception):
    def __init__(self, details) -> None:
        super().__init__("parse error")
        self.details = details
    def __str__(self) -> str:
        return super().__str__() + f" Details: {self.details}"

class crc_error(modbus_exception):
    def __init__(self, details) -> None:
        super().__init__("crc error")
        self.details = details
    def __str__(self) -> str:
        return super().__str__() + f" Details: {self.details}"
    
class protocol_error(modbus_exception):
    def __init__(self, details) -> None:
        super().__init__("protocol error")
        self.details = details
    def __str__(self) -> str:
        return super().__str__() + f" Details: {self.details}"

class empty_message_error(modbus_exception):
    def __init__(self, details) -> None:
        super().__init__("empty message error")
        self.details = details
    def __str__(self) -> str:
        return super().__str__() + f" Details: {self.details}"
class modbus_message:
    def __init__(self, raw_data, ignore_errors=False) -> None:
        self.raw_data = hexlify(raw_data)
        self.ignore_errors = ignore_errors
        self.is_empty = False
        if self.raw_data == b'':
            self.is_empty = True
            if not ignore_errors:
                log.info(message=str(empty_message_error("Empty message")))
        if len(self.raw_data) < 8 and not ignore_errors:
                log.info(message=str(parse_error("Message must be at least 8 bytes long")))
        self.station_address = self.raw_data[0:2]
        self.function_code = self.raw_data[2:4]  
        self.payload = self.raw_data[4:-4]
        self.crc = self.raw_data[-4:]
        if not self.is_empty:
            self.verify_crc()
    def verify_crc(self):
        crc_calc = crc.swappedCalcBytesStart(self.raw_data)
        crc_calc_bts = crc.i_to_bytes_literal(crc_calc)
        if not crc_calc_bts == self.crc and not self.ignore_errors:
            log.info(message=str(crc_error(f"CRC mismatch, calculated:{crc_calc} received:{self.crc}")))
    def __str__(self) -> str:
        return f"Station Address:{self.station_address} Function Code:{self.function_code} CRC:{self.crc}"

class modbus_read_message(modbus_message):
    def __init__(self, raw_data, ignore_errors=False) -> None:
        super().__init__(raw_data, ignore_errors=ignore_errors)
        self.register_start_address = self.payload[0:4]
        self.n_registers = self.payload[4:8]
    def __str__(self) -> str:
        return super().__str__() + f" Register Start Address:{self.register_start_address} N Registers:{self.n_registers}"

class modbus_write_single_message(modbus_message):
    def __init__(self, raw_data,ignore_errors=False) -> None:
        super().__init__(raw_data, ignore_errors=ignore_errors)
        if len(self.payload) != 8 and not ignore_errors:
            log.info(message=str(parse_error(f"Payload must be 8 bytes long, is {len(self.payload)}")))
        self.register_address = self.payload[0:4]
        self.register_value = self.payload[4:8]
    def __str__(self) -> str:
        return super().__str__() + f" Register Address:{self.register_address} Register Value:{self.register_value}"

class modbus_write_multiple_message(modbus_message):
    def __init__(self, raw_data,ignore_errors=False) -> None:
        super().__init__(raw_data, ignore_errors=ignore_errors)
        if len(self.payload) < 6 and not ignore_errors:
            log.info(message=str(parse_error(f"Payload must be at least 6 bytes long, is {len(self.payload)}")))
        self.register_start_address = self.payload[0:4]
        self.n_registers = self.payload[4:8]
        self.byte_count = self.payload[8:10]
        self.data = self.payload[10:]
    def __str__(self) -> str:
        return super().__str__() + f" Register Start Address:{self.register_start_address} N Registers:{self.n_registers} Byte Count:{self.byte_count} Data:{self.data}"

# class modbus_response:
#     def __init__(self, raw_data) -> None:
#         self.raw_data = hexlify(raw_data)
#         self.station_address = self.raw_data[0:2]
#         self.function_code = self.raw_data[2:4]  
#         self.payload = self.raw_data[4:-4]
#         self.crc = self.raw_data[-4:]
#     def __str__(self):
#         return f'Station Address:{self.station_address} Function Code:{self.function_code} CRC:{self.crc}'
    
class modbus_read_response(modbus_message):
    def __init__(self, raw_data, ignore_errors=False) -> None:
        super().__init__(raw_data, ignore_errors=ignore_errors)
        self.byte_count = self.payload[0:2]
        self.data = self.payload[2:]
    def __str__(self):
        return super().__str__() + f' Byte Count:{self.byte_count} Data:{self.data}'

class modbus_write_single_response(modbus_message):
    def __init__(self, raw_data, ignore_errors=False) -> None:
        super().__init__(raw_data, ignore_errors=ignore_errors)
        self.address = self.payload[0:4]
        self.value = self.payload[4:]
    def __str__(self):
        return super().__str__() + f' Address:{self.address} Value:{self.value}'
    
class modbus_write_multiple_response(modbus_message):
    def __init__(self, raw_data, ignore_errors=False) -> None:
        super().__init__(raw_data, ignore_errors=ignore_errors)
        self.address = self.payload[0:4]
        self.n_registers = self.payload[4:8]
    def __str__(self):
        return super().__str__() + f' Address:{self.address} N Registers:{self.n_registers}'

