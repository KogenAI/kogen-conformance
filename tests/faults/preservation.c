/* Inject EACCES only for new recovery data, allowing durable outcome/journal updates.
 * Never alter the source workspace. Used inside disposable conformance worlds. */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <fcntl.h>
#include <stdarg.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <unistd.h>
static int deny(const char *p) {
  const char *root = getenv("KOGEN_CONFORMANCE_PRESERVATION_ROOT");
  if (!root || !p || !strstr(p, root)) return 0;
  /* Atomic run records and journals remain writable; candidate/archive data does not. */
  if (strstr(p, "run.json") || strstr(p, "events.jsonl") || strstr(p, "transcript.jsonl") || strstr(p, "cleanup-pending") || strstr(p, "cleanup.json")) return 0;
  if (strstr(p, "/runs/") || strstr(p, "recovery") || strstr(p, "archive")) { errno = EACCES; return 1; }
  return 0;
}
static int injected_open(const char *p, int flags, ...) {
  mode_t mode = 0;
  if (flags & O_CREAT) { va_list a; va_start(a, flags); mode = va_arg(a, int); va_end(a); }
  if ((flags & (O_CREAT|O_WRONLY|O_RDWR)) && deny(p)) return -1;
#ifdef __APPLE__
  return open(p, flags, mode);
#else
  int (*real_open)(const char*, int, ...) = dlsym(RTLD_NEXT, "open");
  return real_open(p, flags, mode);
#endif
}
static int injected_rename(const char *a, const char *b) {
  if (deny(b)) return -1;
#ifdef __APPLE__
  return rename(a,b);
#else
  int (*real_rename)(const char*, const char*) = dlsym(RTLD_NEXT, "rename");
  return real_rename(a,b);
#endif
}
#ifdef __APPLE__
#define INTERPOSE(replacement, target) \
 __attribute__((used)) static struct {const void *newf; const void *oldf;} interpose_##target \
 __attribute__((section("__DATA,__interpose"))) = {(const void*)&replacement,(const void*)&target};
INTERPOSE(injected_open, open)
INTERPOSE(injected_rename, rename)
#else
int open(const char *p, int flags, ...) {
  mode_t mode=0; if(flags&O_CREAT){va_list a;va_start(a,flags);mode=va_arg(a,int);va_end(a);} return injected_open(p,flags,mode);
}
int rename(const char *a, const char *b) {return injected_rename(a,b);}
#endif
