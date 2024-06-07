# -------------------- Classes --------------------
class addons:
    @staticmethod
    def print_error(*message):
        print('\033[91m', *message, '\033[0m')

    @staticmethod
    def print_ok(*message):
        print('\033[92m', *message, '\033[0m')

    @staticmethod
    def print_descriptor_header():
        print('   №        type  links      length  blocks  name')

    @staticmethod
    def check_state():
        if ActiveFileSystem.FS is None:
            addons.print_error('The file system is not initialised')
            return 1
        return 0


class ActiveFileSystem:
    BLOCK_SIZE = 64
    MAX_FILE_NAME_LENGTH = 15
    FS = None


class FileSystem:
    def __init__(self, des_n):
        self.descriptors_max_num = des_n
        self.descriptors_num = 0
        self.descriptors = []
        self.descriptorsBitmap = [0 for _ in range(des_n)]
        self.Blocks = {}
        self.opened_files_num_descriptors = []
        self.opened_files = []


class Descriptor:
    def __init__(self, num, file_type, length, name):
        self.NUM = num
        self.TYPE = file_type
        self.links_num = 1
        self.length = length
        self.blocks = []
        self.name = name
        self.links = [self]

    def show_info(self):
        print(
            '%4d  %10s  %5d  %10d  %6d  %s' %
            (self.NUM,
             self.TYPE,
             self.links_num,
             self.length,
             len(self.blocks),
             self.name))

    def show_statistics(self):
        print(f'#{self.NUM}, {self.TYPE}, links_num={self.links_num}, length={self.length},'
              f' blocks_num={len(self.blocks)}, name={self.name}')


class Link:
    def __init__(self, descriptor, name):
        descriptor.links_num += 1
        self.descriptor = descriptor
        self.name = name

    def show_info(self):
        print('%4d  %10s  %5d  %10d  %6d  %s' %
              (self.descriptor.NUM,
               self.descriptor.TYPE,
               self.descriptor.links_num,
               self.descriptor.length,
               len(self.descriptor.blocks),
               f'{self.name}->{self.descriptor.name}'))

    def show_statistics(self):
        print(f'#{self.descriptor.NUM}, {self.descriptor.TYPE}, links_num={self.descriptor.links_num},'
              f' length={self.descriptor.length}, blocks_num={len(self.descriptor.blocks)},'
              f' name={self.name} links to {self.descriptor.name}')


class fd:
    def __init__(self, descriptor):
        if isinstance(descriptor, Link):
            self.descriptor = descriptor.descriptor
        else:
            self.descriptor = descriptor
        num_desc = 0
        while num_desc in ActiveFileSystem.FS.opened_files_num_descriptors:
            num_desc += 1
        ActiveFileSystem.FS.opened_files_num_descriptors.append(num_desc)
        self.num_descriptor = num_desc
        self.offset = 0


# -------------------- Functions --------------------
def mkfs(n):
    if ActiveFileSystem.FS is not None:
        addons.print_error('The file system was already been initialised')
        return
    ActiveFileSystem.FS = FileSystem(n)
    addons.print_ok('File system is initialised')


def stat(name):
    if addons.check_state():
        return
    for descriptor in ActiveFileSystem.FS.descriptors:
        if descriptor.name == name:
            descriptor.show_statistics()
            return
    addons.print_error(f'There is no file with this given name')


def ls():
    if addons.check_state():
        return
    addons.print_descriptor_header()
    for descriptor in ActiveFileSystem.FS.descriptors:
        descriptor.show_info()


def create(name):
    if addons.check_state():
        return
    if len(str(name)) > ActiveFileSystem.MAX_FILE_NAME_LENGTH:
        addons.print_error(f'File name is too large. should be less then {ActiveFileSystem.MAX_FILE_NAME_LENGTH}')
    if ActiveFileSystem.FS.descriptors_num >= ActiveFileSystem.FS.descriptors_max_num:
        addons.print_error('All descriptors are used')
        return
    for descriptor in ActiveFileSystem.FS.descriptors:
        if descriptor.name == name:
            addons.print_error('File with this name exist')
            return
    descriptor_num = None
    for i, value in enumerate(ActiveFileSystem.FS.descriptorsBitmap):
        if not value:
            ActiveFileSystem.FS.descriptorsBitmap[i] = 1
            descriptor_num = i
            break
    descriptor = Descriptor(descriptor_num, 'regular', 0, name)
    ActiveFileSystem.FS.descriptors.append(descriptor)
    ActiveFileSystem.FS.descriptors_num += 1
    addons.print_descriptor_header()
    descriptor.show_info()


def link(name1, name2):
    if addons.check_state():
        return
    if len(str(name2)) > ActiveFileSystem.MAX_FILE_NAME_LENGTH:
        addons.print_error(f'File name is too large. should be less then {ActiveFileSystem.MAX_FILE_NAME_LENGTH}')
    for descriptor in ActiveFileSystem.FS.descriptors:
        if descriptor.name == name2:
            addons.print_error(f'An instance with name2 was already created')
            return
    for descriptor in ActiveFileSystem.FS.descriptors:
        if descriptor.name == name1:
            new_link = Link(descriptor, name2)
            descriptor.links.append(new_link)
            ActiveFileSystem.FS.descriptors.append(new_link)
            addons.print_descriptor_header()
            new_link.show_info()
            return
    addons.print_error(f'There is no file with given name')


def unlink(name):
    if addons.check_state():
        return
    for descriptor in ActiveFileSystem.FS.descriptors:
        if descriptor.name == name:
            if isinstance(descriptor, Descriptor):
                addons.print_error(f'There is no link with given name. It is a file.')
                return
            else:
                descriptor.descriptor.links_num -= 1
                ActiveFileSystem.FS.descriptors.remove(descriptor)
                addons.print_ok('Unlinked')
                return
    addons.print_error(f'There is no link with given name')


def open(name):
    if addons.check_state():
        return
    for descriptor in ActiveFileSystem.FS.descriptors:
        if descriptor.name == name:
            openedFile = fd(descriptor)
            ActiveFileSystem.FS.opened_files.append(openedFile)
            addons.print_ok(f'File is opened. ID={openedFile.num_descriptor}')
            return
    addons.print_error(f'There is no file with given name')


def close(fd):
    if addons.check_state():
        return
    if fd in ActiveFileSystem.FS.opened_files_num_descriptors:
        ActiveFileSystem.FS.opened_files_num_descriptors.remove(fd)
        for openedFile in ActiveFileSystem.FS.opened_files:
            if openedFile.num_descriptor == fd:
                ActiveFileSystem.FS.opened_files.remove(openedFile)
                del openedFile
                addons.print_ok(f'File is closed')
                return
    addons.print_error(f'There is no file opened with given ID')


def seek(fd, offset):
    if addons.check_state():
        return
    if fd not in ActiveFileSystem.FS.opened_files_num_descriptors:
        addons.print_error(f'There is no opened file with given ID')
        return
    for openedFile in ActiveFileSystem.FS.opened_files:
        if openedFile.num_descriptor == fd:
            openedFile.offset = offset
            addons.print_ok('Offset is set')
            return


def write(fd, size, val):
    if addons.check_state():
        return
    if len(str(val)) != 1:
        addons.print_error('Value should be 1 byte size')
        return
    if fd not in ActiveFileSystem.FS.opened_files_num_descriptors:
        addons.print_error(f'There is no opened file with given ID')
        return
    for openedFile in ActiveFileSystem.FS.opened_files:
        if openedFile.num_descriptor == fd:
            num = len(openedFile.descriptor.blocks)
            while openedFile.offset + size > num * ActiveFileSystem.BLOCK_SIZE:
                openedFile.descriptor.blocks.append(['\0' for _ in range(ActiveFileSystem.BLOCK_SIZE)])
                num += 1
            num = 0
            for i in range(openedFile.offset + size):
                if i == ActiveFileSystem.BLOCK_SIZE * num + ActiveFileSystem.BLOCK_SIZE:
                    num += 1
                if i >= openedFile.offset:
                    openedFile.descriptor.blocks[num][i - num * ActiveFileSystem.BLOCK_SIZE] = val
            if openedFile.descriptor.length < openedFile.offset + size:
                openedFile.descriptor.length = openedFile.offset + size
            addons.print_ok('Data were written')
            return


def read(fd, size):
    if addons.check_state():
        return
    if fd not in ActiveFileSystem.FS.opened_files_num_descriptors:
        addons.print_error(f'There is no opened file with given ID')
        return
    for openedFile in ActiveFileSystem.FS.opened_files:
        if openedFile.num_descriptor == fd:
            if openedFile.descriptor.length < openedFile.offset + size:
                addons.print_error(
                    f'Can\' read - too big size')
                return
            num = openedFile.offset // ActiveFileSystem.BLOCK_SIZE
            answer = ""
            for i in range(openedFile.offset, openedFile.offset + size):
                if i == ActiveFileSystem.BLOCK_SIZE * num + ActiveFileSystem.BLOCK_SIZE:
                    num += 1
                answer += str(openedFile.descriptor.blocks[num][i - num * ActiveFileSystem.BLOCK_SIZE])
            print(answer)


def truncate(name, size):
    if addons.check_state():
        return
    for descriptor in ActiveFileSystem.FS.descriptors:
        if descriptor.name == name:
            if size < descriptor.length:
                num = len(descriptor.blocks)
                while num * ActiveFileSystem.BLOCK_SIZE > size + ActiveFileSystem.BLOCK_SIZE:
                    descriptor.blocks.pop(num - 1)
                    num -= 1
                descriptor.length = size
            if size > descriptor.length:
                num = len(descriptor.blocks) - 1
                for i in range(descriptor.length, size):
                    if i == ActiveFileSystem.BLOCK_SIZE * num + ActiveFileSystem.BLOCK_SIZE:
                        descriptor.blocks.append(['\0' for i in range(ActiveFileSystem.BLOCK_SIZE)])
                        num += 1
                    descriptor.blocks[num][i - num * ActiveFileSystem.BLOCK_SIZE] = 0
                descriptor.length = size
            addons.print_ok(f'File was successfully truncated')
            return
    addons.print_error(f'There is no file with given')


while True:
    try:
        answer_array = input('>>> ').split(' ')
        command = answer_array[0]
        if command == 'mkfs':
            mkfs(int(answer_array[1]))
        elif command == 'stat':
            stat(answer_array[1])
        elif command == 'ls':
            ls()
        elif command == 'create':
            create(answer_array[1])
        elif command == 'link':
            link(answer_array[1], answer_array[2])
        elif command == 'unlink':
            unlink(answer_array[1])
        elif command == 'open':
            open(answer_array[1])
        elif command == 'close':
            close(int(answer_array[1]))
        elif command == 'seek':
            seek(int(answer_array[1]), int(answer_array[2]))
        elif command == 'write':
            write(int(answer_array[1]), int(answer_array[2]), answer_array[3])
        elif command == 'read':
            read(int(answer_array[1]), int(answer_array[2]))
        elif command == 'truncate':
            truncate(answer_array[1], int(answer_array[2]))
        elif command == 'exit':
            exit(0)
        else:
            addons.print_error('Unknown command')
    except NameError as error:
        addons.print_error('Error in function name')
    except SyntaxError as error:
        addons.print_error('Syntax error')
    except TypeError as error:
        addons.print_error('Arguments error')
    except ValueError as error:
        addons.print_error('Value error')
