from browser import document
import re, math

SPECIAL_CONSTANTS = {'pi', 'e', 'tau'}


def validate_input(string):
    # Remove all whitespaces
    string = re.sub(r'\s', '', string)
    # Some special constants are ok
    for constant in SPECIAL_CONSTANTS:
        string = re.sub(r'(\W)('+constant+')(\W)', r'\1'+r'\3', ' ' + string)[1:]
    # All numbers are ok
    string = re.sub(r'(\.\d+)|(-*\d+)', '', string)
    # Basic operators + - * / % and an ',' are ok
    string = re.sub(r'[+\-*/%,]', '', string)
    # Attributes from the math module are ok
    used_functions = set()
    for function in list(map(lambda i: i[0], re.findall(r'(\w+)(\()', string))):
        if hasattr(math, function):
            string = re.sub(r'('+function+')(\()', r'\2', string)
            used_functions.add(function)
    # Now there should only be an equal amount of open and closed brackets left
    open_brackets = string.count('(')
    closed_brackets = string.count(')')
    if open_brackets == closed_brackets and open_brackets+closed_brackets == len(string):
        return used_functions
    elif open_brackets > closed_brackets:
        return f"ERROR: missing {open_brackets-closed_brackets} closed bracket(s): ')'"
    elif open_brackets < closed_brackets:
        return f"ERROR: missing {closed_brackets-open_brackets} open bracket(s): '('"
    else:
        # Remove all brackets
        string = re.sub(r'\(|\)', '', string)
        return f"ERROR: unexpected characters: {string}"


def handle_special_functions(string, used_functions):
    output = string
    for function in used_functions.union(SPECIAL_CONSTANTS):
        output = re.sub(r'('+function+')', 'math.'+r'\1', output)
    return output


def show_result(event):
    input_string = document["input_field"].value
    output = validate_input(input_string)
    if isinstance(output, set):
        try:
            output = "Result: " + str(eval(handle_special_functions(input_string, output)))
        except Exception as e:
            output = "ERROR: " + str(e)
    document["output_place"].clear()
    document["output_place"] <= (output)


