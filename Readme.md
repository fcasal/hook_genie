## Hook genie

Generate basic hooks for library functions.

### Install
`pip3 instal -e . --user`

### Usage
Generate a hook for `statfs`:
```bash
$ hook_genie statfs

$ ls hooks/
Makefile  statfs_hook.c

$ make -C hooks/

$ LD_PRELOAD=./hooks/statfs_hook.so ls hooks/
	[hook_genie] statfs("/sys/fs/selinux", 0x7fffd272a420)
	[hook_genie] statfs("/selinux", 0x7fffd272a420)
Makefile  statfs_hook.c  statfs_hook.so
```

The hooking function is written to `hooks/statfs_hook.c` which can be modified as desired.

