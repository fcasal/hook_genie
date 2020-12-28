all:
	gcc -fPIC -shared -rdynamic hooker.c -o hooker.so -ldl