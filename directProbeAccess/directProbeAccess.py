#! /usr/bin/env pipenv-shebang
import serial
import time
import binascii
import inspect
from  .CRC16MODBUS import CRC16
from .modbus import modbus_write_single_message, modbus_write_single_response, modbus_read_message, modbus_read_response, parse_error, protocol_error
from .log_utils import print_data
from .errorlog import error_log
from binascii import hexlify, unhexlify

log = error_log(tag="probeAccess")


class ph_response(modbus_read_response):
    def __init__(self, raw_data, ignore_errors=False) -> None:
        super().__init__(raw_data, ignore_errors=ignore_errors)
        if self.byte_count != b'06' and not ignore_errors:
            log.info(message=parse_error("Byte count must be 6"), context=inspect.currentframe().f_lineno)
        self.ph_high_res_raw = self.data[0:4]
        self.ph_low_res_raw = self.data[4:8]
        self.temperature_raw = self.data[8:12]
        self.temperature = int.from_bytes(unhexlify(self.temperature_raw), byteorder='big')/10
        self.ph_high_res = int.from_bytes(unhexlify(self.ph_high_res_raw), byteorder='big')/100
        self.ph_low_res = int.from_bytes(unhexlify(self.ph_low_res_raw), byteorder='big')/10

class calibration_response(modbus_write_single_response):
    def __init__(self, raw_data, ingore_errors=False) -> None:
        super().__init__(raw_data, ignore_errors=ingore_errors)
        self.ignore_errors = ingore_errors
        if not self.is_empty:
            try:
                self.cal_value = int(self.value, 16)
                match self.cal_value:
                    case 4:
                        self.ph_calibration = 4
                        self.finished = False
                    case 6:
                        self.ph_calibration = 7
                        self.finished = False
                    case 9:
                        self.ph_calibration = 10
                        self.finished = False
                    case 41: # 29 = 41 base 10
                        self.ph_calibration = 4
                        self.finished = True
                    case 61: #3d = 61 base 10
                        self.ph_calibration = 7
                        self.finished = True
                    case 91: #5b = 91 base 10
                        self.ph_calibration = 10
                        self.finished = True
                    case 151:
                        self.ph_calibration = "Factory default"
                        self.finished = False
                    case other:
                        self.ph_calibration = "Error"
                        self.finished = False
            except Exception as e:
                if not self.ignore_errors:
                    log.info(message=parse_error(f"Could not parse calibration response: {e}", context=inspect.currentframe().f_lineno))
class cal_verify_response(modbus_read_response):
    def __init__(self, raw_data, ignore_errors=False) -> None:
        super().__init__(raw_data,ignore_errors=ignore_errors)
        self.cal_value = int(self.data, 16)
        match self.cal_value:
            case 4:
                self.ph_calibration = 4
                self.finished = False
            case 6:
                self.ph_calibration = 7
                self.finished = False
            case 9:
                self.ph_calibration = 10
                self.finished = False
            case 41: # 29 = 41 base 10
                self.ph_calibration = 4
                self.finished = True
            case 61: #3d = 61 base 10
                self.ph_calibration = 7
                self.finished = True
            case 91: #5b = 91 base 10
                self.ph_calibration = 10
                self.finished = True
            case 151:
                self.ph_calibration = "Factory default"
                self.finished = False
            case other:
                self.ph_calibration = "Error"
                self.finished = False

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
        # return modbus_response(message)
        pass

    # getters

    def get_ph_high_res(self, ignore_errors=False) -> ph_response:
        '''
        NOTE: The set pin of the device must be connected to GND to enter READ mode to read the pH value.
        ignore_errors must be set to True if you want to check if the SET pin is set incorrectly
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
        return ph_response(response, ignore_errors)

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
        def verify_calibration(self, expected_ph)-> bool:
            ''' subfunction to verify values are actually calibrated, SET pin must be LOW!!!!'''
            ph_resp = self.get_ph_high_res()
            print_data(ph_resp, self.name, expected_ph)
            ph_diff = ph_resp.ph_high_res - expected_ph
            if abs(ph_diff) > 0.5:
                print(f"{self.name}: pH differs too much from expexted value: {ph_diff}")
                log.error(f"{self.name}: pH differs too much from expexted value: {ph_diff}")
                print("please repeat the calibration process. Note that it won't work if the pH is too far from the calibrated value. If the value is wrong , double check if you selected the right buffe. Note that it won't work if the pH is too far from the calibrated value. If the value is wrong , double check if you selected the right buffer")
                return False
            else:
                return True

        def wait_until_calibration_done(self) -> None:
            '''subfunction to wait until calibration is done. SET pin must be LOW!!!!'''
            check_message = self.build_modbus_message(
                'read_single_register', 'ph_calibrate', n_registers=b'\x00\x01', station_address=self.station_address)
            while True:
                time.sleep(1)
                check_response = self.send(check_message)
                chk_resp_decoded = cal_verify_response(check_response)
                if chk_resp_decoded.finished and chk_resp_decoded.ph_calibration == ph:
                    print(f"Calibration done for probe {self.name}")
                    break
                else:
                    print(".")           
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
                expected_ph=4.01
            case 7:
                message=b'\xFF\x06\x00\x0A\x00\x06\x3C\x14'
                expected_ph=6.86
            case 10:
                # message=b'\xFF\x06\x00\x0A\x00\x09\xFC\x12'
                # FF 06 00 0A 00 09 7C 10
                message = b'\xFF\x06\x00\x0A\x00\x09\x7C\x10'
                expected_ph=9.18
            case other:
                raise ValueError('Invalid pH calibration value')
        send_retry_counter =0
        empty_response_retry_counter = 0
        while empty_response_retry_counter < 3:
            while send_retry_counter < 3:
                try:
                    response = self.send(message)
                    # resp_decoded = calibration_response(response)
                    # if not resp_decoded.is_empty:
                    #     break
                    break
                    # else:
                        # retry_counter += 1
                except Exception as e:
                    send_retry_counter += 1
                    log.info(message=str(e))
            else:
                raise OSError('timeout')
            resp_decoded = calibration_response(response)
            if resp_decoded.is_empty:
                log.info(message=protocol_error(f"probe {self.name} returned empty response"))
                empty_response_retry_counter += 1
                time.sleep(1)
            else:
                break
        else:
            error_log.error("Too many empty responses, check sent command: "+str(message))
            raise OSError('too many empty responses, check sent command')
        received_but_not_done= not resp_decoded.finished and resp_decoded.ph_calibration == ph
        done = resp_decoded.finished and resp_decoded.ph_calibration == ph
        if received_but_not_done:
            print(f"probe {self.name} received calibration command for {ph}")
            input(f"{self.name}: Please plug the SET pin into GND to verify the calibration")
            wait_until_calibration_done(self)
            verify_calibration(self, expected_ph)
        elif done:
            print(f"probe {self.name} calibration done for {ph}")
            input(f"{self.name}: Please plug the SET pin into GND to verify the calibration")
            verify_calibration(self, expected_ph)
            return
        else:
            raise ValueError(f"probe {self.name} calibration failed for {ph}, response was {str(resp_decoded)}")
        

        




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
