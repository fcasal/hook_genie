import os
import re
import argparse
import subprocess


def fetch_type_from_manpage(function_name):
    for man_section in (2, 3):
        args = []
        decl = ""
        ret_type = "void"
        includes = ""
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
                includes = "\n".join(
                    [
                        line.strip()
                        for line in match.group(0).split("\n")
                        if "#include" in line
                    ]
                )
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

    return includes, decl.strip(), ret_type, function_name, args


def get_type_format(typ):
    if "char *" in typ:
        return '\\"%s\\"'
    elif "char" in typ:
        return "'%c'"
    elif "*" in typ:
        return "%p"
    elif "int" in typ:
        return "%d"
    elif "size_t" in typ:
        return "%ldu"
    else:
        return "%p"


def gen_hook_code(function_name):
    includes, decl, ret_type, function_name, args = fetch_type_from_manpage(function_name)
    arg_list = [f'{arg["type"]} {arg["name"]}' for arg in args]
    arg_list_no_type = [f'{arg["name"]}' for arg in args]
    type_list = ", ".join([f'{get_type_format(arg["type"])}' for arg in args])
    new_fcn_ptr = f"{ret_type} (*orig_function)({', '.join(arg_list)})"

    result = ""
    if ret_type and ret_type != "void":
        result = f"{ret_type} result = "

    code = f"""

{includes}

{new_fcn_ptr};

{ret_type} {function_name}({', '.join(arg_list)})
{{
    // PREPARE
    fprintf(stderr, "\t[hook_genie] %s({type_list})\\n", {', '.join(['__func__'] + arg_list_no_type)});
    if (!orig_function) {{
        orig_function = dlsym(RTLD_NEXT, __func__);
    }}
    if (!orig_function) {{
        printf("failed to dlsym");
        exit(-1);
    }}


    // BEFORE CALL
    // print_caller();


    // CALL ORIGINAL
    {result}orig_function({', '.join(arg_list_no_type)});


    // AFTER CALL

    return {'result' if result else ''};
}}

"""

    return code


def gen_makefile(function_name):
    return f"all:\n\tgcc -fPIC -shared -rdynamic {function_name}_hook.c -o {function_name}_hook.so -ldl\n"

import pkg_resources

def gen_hook(function_name, dir_name="./hooks/"):
    code = gen_hook_code(function_name)

    base_file = pkg_resources.resource_filename(__name__, 'template/base_hook.c')
    with open(base_file, "r") as f:
        base = f.read()

    if not os.path.exists(dir_name):
        os.mkdir(dir_name)

    with open(dir_name + function_name + "_hook.c", "w") as f:
        f.write(base + code)

    with open(dir_name + "Makefile", "w") as f:
        f.write(gen_makefile(function_name))


def main():
    parser = argparse.ArgumentParser(description="Hook genie")
    parser.add_argument("function_name", help="Generate a hook for this function")
    parser.add_argument(
        "-c",
        "--code_only",
        action="store_true",
        help="print the generated hook (does not write files)",
    )
    args = parser.parse_args()

    if args.code_only:
        print(gen_hook_code(args.function_name))
    else:
        gen_hook(args.function_name)


if __name__ == "__main__":
    main()
