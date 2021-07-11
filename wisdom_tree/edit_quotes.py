class Scanner:
    def __init__(self, original_text_path, new_text_path):
        self.original_text_path = original_text_path
        self.new_text_path = new_text_path

        # open the original file, copy it, then close it
        self.original_file = open(original_text_path, 'r')
        self.source = self.original_file.read()
        self.original_file.close()
        # self.edited_file will append, so 'edited_quotes.txt' needs to be empty before running the script
        self.edited_file = open(new_text_path, 'a')
        # the current index of self.source, or the current character we are looking at
        self.current = 0

        self.punctuation = {
            ' ': lambda c: self.whitespace(c),
            '.': lambda c: self.period(c),
            ',': lambda c: self.colon_comma(c),
            ':': lambda c: self.colon_comma(c),
            ';': lambda c: self.misc_punc(c),
        }
    

    def close(self):
        '''
        Closes files
        '''
        self.edited_file.close()
    

    def add_char(self, c):
        '''
        Add a character to the edited quotes file
        '''
        self.edited_file.write(c)
    

    def scan_file(self):
        '''
        Goes through the original quotes file character by character and fixes common punctuation errors
        '''
        while not self.is_at_end():
            c = self.advance() # get the current character
            if c in self.punctuation: # if whitespace or punctuation
                self.punctuation[c](c) # run the logic for that punctuation
            else: # else, add it to the edited quotes file
                self.add_char(c)
    

    def whitespace(self, current_c):
        '''
        If there is any whitespace or punctuation after this current whitespace character,
        do not add the whitespace to the new file.
        Else, add it to the new file (like single spaces between words).
        '''
        next_c = self.peek()
        if next_c not in self.punctuation:
            self.add_char(current_c)
    

    def misc_punc(self, current_c):
        '''
        Adds whitespace after punctuation unless there are quotations, newlines, ending brackets, 
        ending parentheses, ending curly braces, or more whitespace
        '''
        next_c = self.peek()
        # if there is no whitespace and no newline after this punctuation
        if (next_c != ' ') and (next_c != '\n') and (next_c != '"') and (next_c != "'") and (next_c != ']') and (next_c != ')') and (next_c != '}'):
            self.add_char(current_c) # add the current punctuation
            self.add_char(' ') # and add whitespace
        else:
            self.add_char(current_c)
    

    def period(self, current_c):
        '''
        If the next character is a period, add the current character
        Else, misc_punc()
        '''
        next_c = self.peek()
        if next_c == '.':
            self.add_char(current_c)
        else:
            self.misc_punc(current_c)
    

    def colon_comma(self, current_c):
        '''
        If the next character is a number, add the current character
        Else, misc_punc()
        '''
        next_c = self.peek()
        if next_c.isdigit():
            self.add_char(current_c)
        else:
            self.misc_punc(current_c)


    def advance(self):
        '''
        Return the current character and move current up 1 character
        '''
        c = self.source[self.current]
        self.current += 1
        return c
    

    def peek(self, extra=0):
        '''
        peeks at the next character
        '''
        return self.source[self.current + extra]


    def is_at_end(self):
        '''
        We are at the end -> return True
        We are not at the end -> return False
        '''
        return (self.current >= len(self.source))


def main():
    original_text_path = 'qts.txt'
    new_text_path = 'edited_quotes.txt'

    # clear the 'new' file before starting and then close it
    with open(new_text_path, 'w') as f:
        f.write('') # overwrites the file completely

    scanner = Scanner(original_text_path, new_text_path)
    scanner.scan_file()
    scanner.close()


# run the script
main()