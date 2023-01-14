import struct


class Command(object):
    def __init__(self, op_code, return_format, *arg_lengths):
        """

        :param op_code: string, command identifier string (two letters)
        :param return_format: string, format for unpacking of return value (see struct module documentation)
        :param arg_lengths: length to which each argument should be zero-padded
        """
        assert isinstance(op_code, str)
        assert isinstance(return_format, str)
        assert isinstance(arg_lengths, tuple)
        self.return_struct = struct.Struct(return_format)
        self.op_code = op_code
        self.arg_lengths = arg_lengths

    @property
    def response_length(self):
        """

        :return: response length (in bytes) to be expected
        """
        return self.return_struct.size

    def format(self, *args):
        """

        :param args: tuple, argument values (integers)
        :return: string ready to be sent to the device
        """
        assert isinstance(args, tuple)
        result = '\x06' + self.op_code
        for i in range(0, len(args)):
            result += '{val:0{width}d}'.format(val=args[i], width=self.arg_lengths[i])
        result += '\x0d'
        return result

    def parse(self, response):
        """

        :type response: bytes
        :param response: binary string returned from the device
        :return: tuple with result values
        """
        assert len(response) == self.return_struct.size
        assert isinstance(response, bytes)
        return self.return_struct.unpack(response)
