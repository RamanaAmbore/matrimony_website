import os

def create_structure_from_file(input_file):
    with open(input_file, 'r') as file:
        lines = file.readlines()

    # Maintain a stack of current paths based on indentation levels
    path_stack = []

    for line in lines:
        # Calculate the indentation level
        indent_level = len(line) - len(line.lstrip())
        name = line.strip()

        if not name:  # Skip empty lines
            continue

        # Adjust the path stack to match the current indentation level
        while len(path_stack) > indent_level:
            path_stack.pop()

        # Get the current path by appending the name
        if path_stack:
            current_path = os.path.join(path_stack[-1], name)
        else:
            current_path = name

        if name.endswith('/'):  # It's a folder
            os.makedirs(current_path, exist_ok=True)
            path_stack.append(current_path)  # Add to the stack
        else:  # It's a file
            with open(current_path, 'w') as f:
                pass

    print(f"Folder structure created based on {input_file}")

# Example usage
create_structure_from_file('folder_structure.txt')
