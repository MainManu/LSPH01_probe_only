#! /usr/bin/env pipenv-shebang
import serial
import binascii
from  .CRC16MODBUS import CRC16
from binascii import hexlify, unhexlify

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

class probeAccess:
    def __init__(self, port='/dev/ttyUSB0', baudrate='9600', station_address=b'\xFE', name='probe1', dummy=False) -> None:
        self.name = name
        self.port = port
        self.baudrate = baudrate
        self.station_address = station_address
        self.retry_max = 3
        self.func_codes = {
            'read_single_register': b'\x03',
            'read_multiple_registers': b'\x04',
            'write_single_register': b'\x06',
            'write_multiple_registers': b'\x10',
            'read_device_id': b'\x11',
        }
        self.registers = {
            'ph_high_res': b'\x00\x00',
            'ph_low_res': b'\x00\x01',
            'temperture': b'\x00\x02',
            'ph_electrode_mv': b'\x00\x03',
            'ph_calibrate': b'\x00\x0A',
            'station_address': b'\x02\x00',
            'baud_rate': b'\x02\x01',
            'parity': b'\x02\x02',
            'stop_bits': b'\x02\x03',
            'serial_number1': b'\x02\x0B',
            'serial_number2': b'\x02\x0C',
        }
        self.calibration_mode_station_address=b'\FF'
        self.crc16 = CRC16()
        if not dummy:
            tries = 0
            while tries < self.retry_max:
                try:
                    self.ser = serial.Serial(port, baudrate, timeout=1)
                    break
                except IOError:
                    tries += 1
            else:
                print(f"IO error occured for {self.name}, try rebooting your device")
                raise IOError
        else:
            self.send = self.dummy_send
            self.close = self.dummy_close

    def dummy_send(self, bytes):
        return self.build_modbus_response('write_single_register',  b'\x00', b'\x00\x03')
    def send(self, bytes):
        self.ser.write(bytes)
        return self.ser.read(11)

    def dummy_close(self):
        return True
    def close(self):
        if hasattr(self, 'ser'):
            self.ser.close()
            return True
        else:
            return False

    def build_modbus_message(self, func_code: str, register: str, value: str = None, n_registers: str = None, station_address: str = b'\xFE'):
        message = station_address + \
            self.func_codes[func_code] + self.registers[register]
        if value != None:
            message = message  + value
        if n_registers != None:
            message = message + n_registers

        crc = bytes.fromhex(hex(self.crc16.swappedCalcBytesStart(message))[2:]) # ugly hack to remove 0x from the beginning of the string
        message = message + crc
        return message

    def build_modbus_response(self, func_code: str, value: str = None, n_registers: str = None, station_address: str = b'\xFE') -> str:
        message = station_address + \
            self.func_codes[func_code] 
        if value != None:
            message = message  + value
        if n_registers != None:
            message = message + n_registers

        crc = bytes.fromhex(hex(self.crc16.swappedCalcBytesStart(message))[2:]) # ugly hack to remove 0x from the beginning of the string
        message = message + crc
        return message
    
    def init_measurement(self):
        result = self.get_ph_high_res()
        while result.ph_high_res == 0.0:
            print(f"Probe {self.name} not connected or SET pin high")
            input("please fix and press enter to continue")
            result = self.get_ph_high_res()
        else:
            print(f"Probe {self.name} connected and working")
            return result


    def decode_modbus_response(self, message):
        # TODO: implement
        pass

    # getters

    def get_ph_high_res(self) -> ph_response:
        '''
        NOTE: The set pin of the device must be connected to GND to enter READ mode to read the pH value.
        '''
        message = self.build_modbus_message(
            'read_single_register', 'ph_high_res', n_registers=b'\x00\x03')
        # message = b'\xFE\x03\x00\x00\x00\x03\x11\xC4'
        retry_counter = 0
        while retry_counter < 3:
            try:
                response = self.send(message)
                break
            except IOError as e:
                retry_counter += 1
        else:
            raise IOError('Could not read from device: timeout')
        return ph_response(response)

    # setters

    def set_baud_rate(self, baudrate):
        '''
        NOTE: The set pin of the device must be connected to VCC to enter SET mode for baud rate change.
        '''
        value = 0x3
        match baudrate:
            case 1200:
                value = 0x0
            case 2400:
                value = 0x1
            case 4800:
                value = 0x2
            case 9600:
                value = 0x3
            case 19200:
                value = 0x4
            case 38400:
                value = 0x5
            case other:
                value = 0x3

        message = self.build_modbus_message(
            'write_single_register', 'baud_rate', value)
        return self.send(message)
    
    def set_station_address(self, address):
        '''
        NOTE: The set pin of the device must be connected to VCC to enter SET mode for station address change.
        '''
        message = self.build_modbus_message(
            'write_single_register', 'station_address', address)
        return self.send(message)
    
    def calibrate_ph(self, ph):
        '''
        NOTE: The set pin of the device must be connected to VCC to enter SET mode, which is required for calibration.
        '''
        # match ph:
        #     case 4:
        #         value = b'\x00\x04'
        #     case 7:
        #         value = b'\x00\x06'
        #     case 10:
        #         value = b'\x00\x09'
        #     case other:
        #         raise ValueError('Invalid pH calibration value')
        # message = self.build_modbus_message(
        #     'write_single_register', 'ph_calibrate', value, station_address=self.calibration_mode_station_address)
        match ph:
            case 4:
                message=b'\xFF\x06\x00\x0A\x00\x04\xBD\xD5'
            case 7:
                message=b'\xFF\x06\x00\x0A\x00\x06\x3C\x14'
            case 10:
                message=b'\xFF\x06\x00\x0A\x00\x09\xFC\x12'
            case other:
                raise ValueError('Invalid pH calibration value')
        return self.send(message)



def main():
    # test crc16 implementation
    # test_hex = b'\xFE\x03\x06\x02\xB7\x00\x46\x00\xFE'
    # crc16 = CRC16()
    # print(hex(crc16.calcStringStart(test_hex)))
    probe = probeAccess('/dev/ttyUSB0')
    response1 = probe.get_ph_high_res()
    print(response1.ph_high_res)
    print(response1.temperature)
    
    # response2 = probe.calibrate_ph(4)
    # print(response2)

    # response3 = probe.get_ph_high_res()
    # print(response3.ph_high_res)
    # print(response3.temperature)

if __name__ == '__main__':
    main()
