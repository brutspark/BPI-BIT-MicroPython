FIRMWARE_MAJOR_VERSION = 2
FIRMWARE_MINOR_VERSION = 5
FIRMWARE_BUGFIX_VERSION = 6

PROTOCOL_MAJOR_VERSION = 2  # for non-compatible changes
PROTOCOL_MINOR_VERSION = 5  # for backwards compatible changes
PROTOCOL_BUGFIX_VERSION = 1  # for bugfix releases

DIGITAL_MESSAGE = 0x90  # send data for a digital port (collection of 8 pins)
ANALOG_MESSAGE = 0xE0  # send data for an analog pin (or PWM)
REPORT_ANALOG = 0xC0  # enable analog input by pin #
REPORT_DIGITAL = 0xD0  # enable digital input by port pair

SET_PIN_MODE = 0xF4  # set a pin to INPUT/OUTPUT/PWM/etc
SET_DIGITAL_PIN_VALUE = 0xF5  # set value of an individual digital pin

REPORT_VERSION = 0xF9  # report protocol version
SYSTEM_RESET = 0xFF  # reset from MIDI

START_SYSEX = 0xF0  # start a MIDI Sysex message
END_SYSEX = 0xF7  # end a MIDI Sysex message

SERIAL_DATA = 0x60  # communicate with serial devices, including other boards
ENCODER_DATA = 0x61  # reply with encoders current positions
SERVO_CONFIG = 0x70  # set max angle, minPulse, maxPulse, freq
STRING_DATA = 0x71  # a string message with 14-bits per char
STEPPER_DATA = 0x72  # control a stepper motor
ONEWIRE_DATA = 0x73  # send an OneWire read/write/reset/select/skip/search request
SHIFT_DATA = 0x75  # a bitstream to/from a shift register
I2C_REQUEST = 0x76  # send an I2C read/write request
I2C_REPLY = 0x77  # a reply to an I2C read request
I2C_CONFIG = 0x78  # config I2C settings such as delay times and power pins
REPORT_FIRMWARE = 0x79  # report name and version of the firmware
EXTENDED_ANALOG = 0x6F  # analog write (PWM, Servo, etc) to any pin
PIN_STATE_QUERY = 0x6D  # ask for a pin's current mode and value
PIN_STATE_RESPONSE = 0x6E  # reply with pin's current mode and value
CAPABILITY_QUERY = 0x6B  # ask for supported modes and resolution of all pins
CAPABILITY_RESPONSE = 0x6C  # reply with supported modes and resolution
ANALOG_MAPPING_QUERY = 0x69  # ask for mapping of analog to pin numbers
ANALOG_MAPPING_RESPONSE = 0x6A  # reply with mapping info
SAMPLING_INTERVAL = 0x7A  # set the poll rate of the main loop
SCHEDULER_DATA = 0x7B  # send a createtask/deletetask/addtotask/schedule/querytasks/querytask request to the scheduler
SYSEX_NON_REALTIME = 0x7E  # MIDI Reserved for non-realtime messages
SYSEX_REALTIME = 0x7F  # MIDI Reserved for realtime messages

PIN_MODE_INPUT = 0x00  # same as INPUT defined in Arduino.h
PIN_MODE_OUTPUT = 0x01  # same as OUTPUT defined in Arduino.h
PIN_MODE_ANALOG = 0x02  # analog pin in analogInput mode
PIN_MODE_PWM = 0x03  # digital pin in PWM output mode
PIN_MODE_SERVO = 0x04  # digital pin in Servo output mode
PIN_MODE_SHIFT = 0x05  # shiftIn/shiftOut mode
PIN_MODE_I2C = 0x06  # pin included in I2C setup
PIN_MODE_ONEWIRE = 0x07  # pin configured for 1-wire
PIN_MODE_STEPPER = 0x08  # pin configured for stepper motor
PIN_MODE_ENCODER = 0x09  # pin configured for rotary encoders
PIN_MODE_SERIAL = 0x0A  # pin configured for serial communication
PIN_MODE_PULLUP = 0x0B  # enable internal pull-up resistor for pin
PIN_MODE_IGNORE = 0x7F  # pin configured to be ignored by digitalWrite and capabilityResponse

class FirmataParser:

    MaxSize = 64

    def analogCb(self, command, value):
        print(str('analogCb'))
    def digitalCb(self, command, value):
        print(str('digitalCb'))
    def pinModeCb(self, command, value):
        print(str('pinModeCb'))
    def pinValueCb(self, command, value):
        print(str('pinValueCb'))
    def reportAnalogCb(self, command, value):
        print(str('reportAnalogCb'))
    def reportDigitalCb(self, command, value):
        print(str('reportDigitalCb'))
    def reportVersionCb(self):
        print(str('reportVersionCb'))
    def systemResetCb(self):
        print(str('SystemResetCb'))
    def reportFirmwareCb(self, sv_major, sv_minor, firmware):
        print(str('reportFirmwareCb'))
    def stringCb(self):
        print(str('stringCb'))
    def sysexCb(self, command, *args):
        print(str('sysexCb'))

    def __init__(self):
        self.buffer = [0] * FirmataParser.MaxSize
        self.parsingSysex = False
        self.executeMultiByteCommand = 0  # execute this after getting multi-byte data
        self.multiByteChannel = 0  # channel data for multiByteCommands
        self.waitForData = 0  # this flag says the next serial input will be data
        self.sysexBytesRead = 0

    def decodeByteStream(self, offset, limit):
        buffer = ""
        for i in range(offset, limit / 2, 2):
            buffer += self.buffer[i] + self.buffer[i + 1] << 7
        return buffer

    def processSysexMessage(self):
        # first byte in buffer is command
        command = self.buffer[0]
        if (command == REPORT_FIRMWARE):
            offset = 3
            # Test for malformed REPORT_FIRMWARE message (used to query firmware prior to Firmata v3.0.0)
            if (3 > self.sysexBytesRead):
                self.reportFirmwareCb(0, 0, None)
            else:
                buf = self.decodeByteStream(offset, self.sysexBytesRead - offset)
                self.buffer[offset + len(buf)] = '\0'
                self.reportFirmwareCb(self.buffer[1], self.buffer[2], buf)
        elif command == STRING_DATA:
            offset = 1
            buf = self.decodeByteStream(offset, self.sysexBytesRead - offset)
            self.buffer[offset + len(buf)] = '\0'
            self.stringCb(buf)
        else:
            self.sysexCb(self.buffer[0], self.sysexBytesRead - 1, bytes(self.buffer[1:]))

    def systemReset(self):
        self.__init__(self)
        self.SystemResetCb()

    def parse(self, inputData):
        if (self.parsingSysex):
            if (inputData == END_SYSEX):
                self.parsingSysex = False
                self.processSysexMessage()
            else:
                self.buffer[self.sysexBytesRead] = inputData
                self.sysexBytesRead = self.sysexBytesRead + 1
        elif (self.waitForData > 0 and inputData < 128):
            self.waitForData = self.waitForData - 1
            self.buffer[self.waitForData] = inputData
            if (self.waitForData == 0 and self.executeMultiByteCommand):
                if self.executeMultiByteCommand == ANALOG_MESSAGE:
                    self.analogCb(self.multiByteChannel, (self.buffer[0] << 7) + self.buffer[1])
                elif self.executeMultiByteCommand == DIGITAL_MESSAGE:
                    self.digitalCb(self.multiByteChannel, (self.buffer[0] << 7) + self.buffer[1])
                elif self.executeMultiByteCommand == SET_PIN_MODE:
                    self.pinModeCb(self.multiByteChannel, (self.buffer[0] << 7) + self.buffer[1])
                elif self.executeMultiByteCommand == SET_DIGITAL_PIN_VALUE:
                    self.pinValueCb(self.multiByteChannel, (self.buffer[0] << 7) + self.buffer[1])
                elif self.executeMultiByteCommand == REPORT_ANALOG:
                    self.reportAnalogCb(self.multiByteChannel, (self.buffer[0] << 7) + self.buffer[1])
                elif self.executeMultiByteCommand == REPORT_DIGITAL:
                    self.reportDigitalCb(self.multiByteChannel, (self.buffer[0] << 7) + self.buffer[1])
                else:
                    pass
            self.executeMultiByteCommand = 0
        else:
            # remove channel info from command byte if less than 0xF0
            if inputData < 0xF0:
                command = inputData & 0xF0
                self.multiByteChannel = inputData & 0x0F
            else:
                command = inputData
            # commands in the 0xF* range don't use channel data
            if command in [ANALOG_MESSAGE, DIGITAL_MESSAGE, SET_PIN_MODE, SET_DIGITAL_PIN_VALUE]:
                self.waitForData = 2;  # two data bytes needed
                self.executeMultiByteCommand = command
            if command in [REPORT_ANALOG, REPORT_DIGITAL]:
                self.waitForData = 1;  # one data byte needed
                self.executeMultiByteCommand = command
            if command == START_SYSEX:
                self.parsingSysex = True
                self.sysexBytesRead = 0
            if command == SYSTEM_RESET:
                self.systemReset()
            if command == REPORT_VERSION:
                self.reportVersionCb()

# Here is an example FirmataMarshaller

from machine import UART, ADC, Pin


class Uno32(FirmataParser):
    INPUT = 0x00  # digital pin in input mode
    OUTPUT = 0x01  # digital pin in output mode
    ANALOG = 0x02  # analog pin in input mode
    PWM = 0x03  # digital pin in PWM output mode
    SERVO = 0x04  # digital pin in Servo output mode

    IS_PIN_DIGITAL, IS_PIN_PWM, IS_PIN_DIGITAL, IS_PIN_ANALOG = 1, 2, 3, 4

    # Define Pin for UNO32
    AllPins = [
        [IS_PIN_DIGITAL],
        [IS_PIN_DIGITAL],
        [IS_PIN_DIGITAL],
        [IS_PIN_DIGITAL, IS_PIN_PWM],
        [IS_PIN_DIGITAL],
        [IS_PIN_DIGITAL, IS_PIN_PWM],
        [IS_PIN_DIGITAL, IS_PIN_PWM],
        [IS_PIN_DIGITAL],
        [IS_PIN_DIGITAL, IS_PIN_ANALOG],
        [IS_PIN_DIGITAL, IS_PIN_PWM, IS_PIN_ANALOG],
        [IS_PIN_DIGITAL, IS_PIN_PWM, IS_PIN_ANALOG],
        [IS_PIN_DIGITAL, IS_PIN_PWM, IS_PIN_ANALOG],
        [IS_PIN_DIGITAL, IS_PIN_ANALOG],
        [IS_PIN_DIGITAL, IS_PIN_ANALOG],
    ]

    Adcs = [
        ADC(Pin(36)),
        ADC(Pin(39)),
        ADC(Pin(32)),
        ADC(Pin(33)),
        ADC(Pin(34)),
        ADC(Pin(35)),
    ]

    Pins = [
        (Pin(2)),  # 3
        (Pin(2)),  # 1
        (Pin(2)),
        (Pin(4)),
        (Pin(15)),
        (Pin(13)),
        (Pin(12)),
        (Pin(14)),
        (Pin(25)),
        (Pin(26)),
        (Pin(05)),
        (Pin(23)),
        (Pin(19)),
        (Pin(18)),
    ]

    def __init__(self, Stream):
        super(Uno32, self).__init__()
        self.Stream = Stream
        self.analogInputsToReport = 0  # bitwise array to store pin reporting

    def processInput(self):
        if self.Stream.any():
            data = self.Stream.read(1)[0]
            if (-1 != data):
                # print(data)
                self.parse(data)

    def compose_two_byte(self, value):
        return (value & 0b01111111,  # LSB
                (value >> 7) & 0b01111111)  # MSB

    def send_message(self, msg=[]):
        for m in msg:
            self.Stream.write((m) if type(m) is bytes else bytes([m]))

    def send_sysex_message(self, msg):
        msg.insert(0, START_SYSEX)
        msg.append(END_SYSEX)
        self.send_message(msg)

    def reportVersionCb(self):
        print(str('reportVersionCb'))
        self.send_message([REPORT_VERSION, PROTOCOL_MAJOR_VERSION, PROTOCOL_MINOR_VERSION])

    def reportFirmwareCb(self, sv_major, sv_minor, firmware):
        print(str('reportFirmwareCb'))
        self.send_sysex_message(
            [REPORT_FIRMWARE, PROTOCOL_MAJOR_VERSION, PROTOCOL_MINOR_VERSION, bytes('StandardFirmata.ino', 'ascii')])

    def reportAnalogCb(self, pin, command=0):
        if pin < len(Adcs):
            value = int(Adcs[pin].read() / 4)
            print(str(Adcs[pin]), str(pin), str(value))
            msg = [ANALOG_MESSAGE | (pin & 0xF)]
            msg.extend(self.compose_two_byte(value))
            self.send_message(msg)
        '''
        else:
            Adcs.append(ADC(Pin(pin)))
            value = Adcs[pin].read()
            msg = [EXTENDED_ANALOG, pin]
            msg.extend(self.compose_two_byte(value))
            self.send_sysex_message(msg)
        '''

    def reportDigitalCb(self, pin, command=0):
        if pin < len(Pins):
            value = Pins[pin].value()
            print(str('reportDigitalCb'), str(pin), str(value))
            msg = [REPORT_DIGITAL | (pin & 0xF), value]
            self.send_message(msg)

    def sysexCb(self, command, *args):
        print(str('sysexCb'), str(command), str(args))
        if (command == CAPABILITY_QUERY):
            msg = [CAPABILITY_RESPONSE]
            for pin in AllPins:
                if IS_PIN_DIGITAL in pin:
                    msg.extend([INPUT, 1, OUTPUT, 1, PIN_MODE_SERVO, 14])
                if IS_PIN_ANALOG in pin:
                    msg.extend([PIN_MODE_ANALOG, 10])
                if IS_PIN_PWM in pin:
                    msg.extend([PIN_MODE_PWM, 8])
                msg.append(127)
            self.send_sysex_message(msg)
        elif (command == ANALOG_MAPPING_QUERY):
            msg = [ANALOG_MAPPING_RESPONSE]
            for i in range(len(AllPins)):
                msg.append(i if IS_PIN_ANALOG in AllPins[i] else 127)
            # for i in range(len(Adcs)):
            # msg.append(i)
            self.send_sysex_message(msg)

Stream = UART(2)
Stream.init(57600, bits=8, parity=None, stop=1)

firmata = Uno32(Stream)


timerCheckUpdate = 0

firmata.reportVersionCb()
firmata.reportFirmwareCb(0, 0, None)
firmata.sysexCb(CAPABILITY_QUERY)
firmata.sysexCb(ANALOG_MAPPING_QUERY)

import utime
while True:
    if (utime.ticks_ms() - timerCheckUpdate >= 100):
        '''
        for i in range(len(Uno32.Adcs)):
            firmata.reportAnalogCb(i, 128)
        for i in range(len(Pins)):
             firmata.reportDigitalCb(i)
        '''
        timerCheckUpdate = utime.ticks_ms()
    firmata.processInput()
