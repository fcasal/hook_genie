import os
import subprocess
import re


def parse_manpage(function_name):
    for man_section in (2, 3):
        args = []
        ret_type = ""
        try:
            with open(os.devnull, "w") as devnull:
                man_argv = ["man"]
                man_argv.extend(["-E", "UTF-8"])
                man_argv.extend(["-P", "col -b", str(man_section), function_name])
                output = subprocess.check_output(man_argv, stderr=devnull)

            match = re.search(
                r"^SYNOPSIS(?:.|\n)*?((?:^.+$\n)* {5}\w+[ \*\n]*"
                + function_name
                + r"\((?:.+\,\s*?$\n)*?(?:.+\;$\n))(?:.|\n)*^DESCRIPTION",
                output.decode("UTF-8", errors="replace"),
                re.MULTILINE,
            )
            if match:
                decl = match.group(1)
                ret_type = decl.split(function_name)[0].strip()

                for argm in re.finditer(r"[\(,]\s*(.+?)\s*\b(\w+)(?=[,\)])", decl):
                    typ = argm.group(1)
                    arg = argm.group(2)
                    if arg == "void":
                        continue
                    if arg == "...":
                        args.append('", ..." +')
                        continue

                    normalized_type = re.sub(r"\s+", "", typ)
                    if normalized_type.endswith("*restrict"):
                        normalized_type = normalized_type[:-8]

                    arg_index = len(args)
                    args.append({"idx": arg_index, "type": typ, "name": arg})
                break
        except Exception as e:
            pass

    return decl.strip(), ret_type, function_name, args


def get_type_format(typ):
    if 'char *' in typ:
        return '\\"%s\\"'
    elif 'char' in typ:
        return '\'%c\''
    elif '*' in typ:
        return '%p'
    elif 'int' in typ:
        return '%d'
    elif 'size_t' in typ:
        return '%ldu'

def template_hooker(function_name):
    decl, ret_type, function_name, args = parse_manpage(function_name)
    arg_list = [f'{arg["type"]} {arg["name"]}' for arg in args]
    arg_list_no_type = [f'{arg["name"]}' for arg in args]
    type_list = ', '.join([f'{get_type_format(arg["type"])}' for arg in args])
    new_fcn_ptr = f"{ret_type} (*orig_function)({', '.join(arg_list)})"

    template = f"""
    {new_fcn_ptr};

    {ret_type} {function_name}({', '.join(arg_list)})
    {{
        // PREPARE
        fprintf(stderr, "hooking %s({type_list})\\n", __func__, {', '.join(arg_list_no_type)});
        if (!orig_function) {{
            orig_function = dlsym(RTLD_NEXT, __func__);
        }}
        if (!orig_function) {{
            printf("failed to dlsym");
            exit(-1);
        }}


        // BEFORE CALL
        print_caller();


        // CALL ORIGINAL
        {ret_type} result = orig_function({', '.join(arg_list_no_type)});


        // AFTER CALL

        return result;
    }}

    """

    return template

def gen_makefile(function_name):
    return f'all:\n\tgcc -fPIC -shared -rdynamic {function_name}_hook.c -o {function_name}_hook.so -ldl\n'

def gen_hook(function_name):
    template = template_hooker(function_name)
    with open('base_hook.c', 'r') as f:
        base = f.read()

    with open('hooks/' + function_name + '_hook.c', 'w') as f:
        f.write(base + template)

    with open('hooks/Makefile', 'w') as f:
        f.write(gen_makefile(function_name))


