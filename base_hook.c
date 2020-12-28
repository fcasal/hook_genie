#define _GNU_SOURCE
#include <dlfcn.h>
#include <execinfo.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>


// UTILS
#define CALLER_DEPTH 3
#define MAX_DEPTH 100

void print_caller()
{
    void *buffer[CALLER_DEPTH];

    int nptrs = backtrace(buffer, CALLER_DEPTH);
    char **strings = backtrace_symbols(buffer, CALLER_DEPTH);

    // print third callee:
    // 0 -> get_caller
    // 1 -> function that calls get_caller (what we are hooking)
    // 2 -> what calls the hooked function
    printf("called by: %s\n", strings[CALLER_DEPTH - 1]);
    free(strings);
}

void print_backtrace()
{
    void *buffer[MAX_DEPTH];

    int nptrs = backtrace(buffer, MAX_DEPTH);
    backtrace_symbols_fd(buffer, nptrs, STDOUT_FILENO);
}


// HOOK HERE

