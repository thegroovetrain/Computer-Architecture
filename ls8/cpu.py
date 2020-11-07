"""CPU functionality."""

import sys

# OPCODES
_hlt = 0x01
_ld = 0x83
_ldi = 0x82
_nop = 0x00
_pop = 0x46
_prn = 0x47
_push = 0x45

# PC MUTATORS
_call = 0x50
_jeq = 0x55
_jge = 0x5A
_jgt = 0x57
_jlt = 0x58
_jle = 0x59
_jmp = 0x54
_jne = 0x56
_ret = 0x11

# ALU INSTRUCTIONS
_add = 0xA0
_and = 0xA8
_cmp = 0xA7
_dec = 0x66
_inc = 0x65
_mul = 0xA2

class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        #
        self.reg = [0] * 8
        self.reg[7] = 0xF4

        self.ram = [0] * 256
        self.pc = 0
        self.ir = 0
        self.mar = 0
        self.mdr = 0
        self.fl = 0
        self.running = False

        # Initialize the opcode lookup table
        self.op_table = {}

        # CPU INSTRUCTIONS
        self.op_table[_hlt] = self._hlt
        self.op_table[_ld] = self._ld
        self.op_table[_ldi] = self._ldi
        self.op_table[_nop] = self._nop
        self.op_table[_pop] = self._pop
        self.op_table[_prn] = self._prn
        self.op_table[_push] = self._push

        # PC MUTATORS
        self.op_table[_call] = self._call
        self.op_table[_jeq] = self._jeq
        self.op_table[_jge] = self._jge
        self.op_table[_jgt] = self._jgt
        self.op_table[_jle] = self._jle
        self.op_table[_jlt] = self._jlt
        self.op_table[_jmp] = self._jmp
        self.op_table[_jne] = self._jne
        self.op_table[_ret] = self._ret

        # ALU INSTRUCTIONS
        self.op_table[_add] = self._add
        self.op_table[_and] = self._and
        self.op_table[_cmp] = self._cmp
        self.op_table[_dec] = self._dec
        self.op_table[_inc] = self._inc
        self.op_table[_mul] = self._mul


    def load(self):
        """Load a program into memory."""

        address = 0

        # For now, we've just hardcoded a program:

        program = [
            # From print8.ls8
            0b10000010,  # LDI R0,8
            0b00000000,
            0b00001000,
            0b01000111,  # PRN R0
            0b00000000,
            0b00000001,  # HLT
        ]

        # we can continue to use that default program (for now)
        # but if we pass in a file via command line we can clear the program and run that instead
        # ( maybe try and write a BASIC implementation? lol )
        if len(sys.argv) > 1:
            program = []
            with open(sys.argv[1], 'r') as file:
                all_lines = file.readlines()
                for line in all_lines:
                    if line[0] in ['0', '1']:
                        program.append(int(line[:8], 2))

        for instruction in program:
            self.ram[address] = instruction
            address += 1

    def alu(self, op, reg_a, reg_b):
        """ALU operations."""

        if op == "ADD":
            self.reg[reg_a] += self.reg[reg_b]
        #elif op == "SUB": etc
        else:
            raise Exception("Unsupported ALU operation")

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE: %02X %08s | %02X %02X %02X |" % (
            self.pc,
            bin(self.fl)[2:].rjust(8, '0'),
            #self.ie,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.reg[i], end='')

        print()

    def run(self):
        """Run the CPU."""
        self.running = True

        while self.running:
            # self.trace()

            # load the current instruction into the instruction register
            self.ir = self.ram_read(self.pc)

            # decode the instruction
            operands = self.ir >> 6
            is_alu_operation = (self.ir & 0x20) >> 5
            sets_pc = (self.ir & 0x10) >> 4
            instruction = self.ir & 0x0F

            # load the instruction's operands
            args = [self.ram_read(self.pc + i + 1) for i in range(operands)]

            # lookup and execute the opcode, passing any operands
            self.op_table[self.ir](*args)

            # increment the program counter by an appropriate amount
            if self.ir is not _hlt:
                self.pc += 0 if sets_pc else (1 + len(args))

            self.pc = self.pc if self.pc >= 0 else 255
            self.pc = self.pc if self.pc <= 255 else 0

    #################
    # RAM FUNCTIONS #
    #################

    def ram_read(self, address):
        return self.ram[address]

    def ram_write(self, address, value):
        self.ram[address] = value

    ####################
    # OVERFLOW HANDLER #
    ####################

    def handle_overflow(self, r):
        self.reg[r] = self.reg[r] if self.reg[r] >= 0 else 0xFF
        self.reg[r] = self.reg[r] if self.reg[r] <= 255 else 0x00

    ##########################
    # OPCODE IMPLEMENTATIONS #
    ##########################

    def _hlt(self):
        self.running = False

    def _ld(self, ra, rb):
        self.reg[ra] = self.ram_read(self.reg[rb])

    def _ldi(self, r, i):
        self.reg[r] = i

    def _nop(self):
        pass

    def _pop(self, r):
        self.reg[r] = self.ram_read(self.reg[7])
        self.reg[7] += 1
        self.handle_overflow(7)

    def _prn(self, r):
        print(self.reg[r])

    def _push(self, r):
        self.reg[7] -= 1
        self.handle_overflow(7)
        self.ram_write(self.reg[7], self.reg[r])

    ###############
    # PC MUTATORS #
    ###############

    def _call(self, r):
        self.reg[7] -= 1
        self.handle_overflow(7)
        self.ram_write(self.reg[7], self.pc + 2)
        self.pc = self.reg[r]

    def _jeq(self, r):
        if self.fl & 0b1:
            self.pc = self.reg[r]
        else:
            self.pc += 2

    def _jge(self, r):
        if self.fl & 0b11:
            self.pc = self.reg[r]
        else:
            self.pc += 2

    def _jgt(self, r):
        if self.fl & 0b10:
            self.pc = self.reg[r]
        else:
            self.pc += 2

    def _jle(self, r):
        if self.fl & 0b101:
            self.pc = self.reg[r]
        else:
            self.pc += 2

    def _jlt(self, r):
        if self.fl & 0b100:
            self.pc = self.reg[r]
        else:
            self.pc += 2

    def _jmp(self, r):
        self.pc = self.reg[r]

    def _jne(self, r):
        if self.fl & 0b1:
            self.pc += 2
        else:
            self.pc = self.reg[r]

    def _ret(self):
        self.pc = self.ram_read(self.reg[7])
        self.reg[7] += 1
        self.handle_overflow(7)

    ####################
    # ALU INSTRUCTIONS #
    ####################

    def _add(self, ra, rb):
        self.reg[ra] += self.reg[rb]

    def _and(self, ra, rb):
        self.reg[ra] &= self.reg[rb]

    def _cmp(self, ra, rb):
        # compare values in the two registers
        # if ra = rb, set equal flag E (0b00000001) to 1, otherwise to 0
        # if ra < rb, set less than flag L (0b00000100) to 1, otherwise to 0
        # if ra > rb, set greater than flag G (0b00000010) to 1, otherwise to 0
        self.fl &= 0xF8
        if self.reg[ra] == self.reg[rb]:
            self.fl |= 0x01
        elif self.reg[ra] < self.reg[rb]:
            self.fl |= 0x04
        elif self.reg[ra] > self.reg[rb]:
            self.fl |= 0x02

    def _dec(self, ra):
        self.reg[ra] -= 1
        self.handle_overflow(self.reg[ra])

    def _inc(self, ra):
        self.reg[ra] += 1
        self.handle_overflow(self.reg[ra])

    def _mul(self, ra, rb):
        self.reg[ra] *= self.reg[rb]