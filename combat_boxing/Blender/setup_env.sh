#!/bin/sh
# Rebuild the headless Blender 5 toolchain in this sandbox.
# (PyPI is reachable; apt mirrors are not. Uses no-op stub libs for X11/GL
# because headless Cycles-CPU never calls into them.)
set -e
cd "$(dirname "$0")/../.."
python3 -m venv .blenderenv
./.blenderenv/bin/pip install -q bpy numpy
mkdir -p .stubs
cd .stubs
# --- GL/GLX/OpenGL stub (no-op entry points; the 16 symbols bpy needs) ---
python3 - <<'PY'
import re
names = set("""glFinish glXChooseFBConfig glXCreateContext glXCreateNewContext glXCreateWindow
glXDestroyContext glXGetCurrentContext glXGetCurrentDisplay glXGetCurrentDrawable
glXGetProcAddress glXGetProcAddressARB glXGetVisualFromFBConfig glXMakeContextCurrent
glXMakeCurrent glXQueryContext glXSwapBuffers""".split())
lines = ["#include <stddef.h>"]
ptr = {"glXChooseFBConfig","glXCreateContext","glXCreateNewContext","glXCreateWindow",
       "glXGetCurrentContext","glXGetCurrentDisplay","glXGetCurrentDrawable",
       "glXGetProcAddress","glXGetProcAddressARB","glXGetVisualFromFBConfig",
       "glXMakeContextCurrent","glXMakeCurrent","glXQueryContext"}
for n in sorted(names):
    lines.append(("void *%s(void) { return NULL; }" if n in ptr else "void %s(void) { }") % n)
open("glstub.c","w").write("\n".join(lines))
PY
for L in libGL.so.1 libGLX.so.0 libOpenGL.so.0; do
  gcc -shared -o "$L" glstub.c -Wl,-soname,"$L"
done
# --- X extension stubs ---
cat > xfixes_stub.c <<'C'
#include <stddef.h>
void XFixesHideCursor(void) { }
void XFixesShowCursor(void) { }
C
gcc -shared -o libXfixes.so.3 xfixes_stub.c -Wl,-soname,libXfixes.so.3
cat > xi_stub.c <<'C'
#include <stddef.h>
void XCloseDevice(void) { }
void XFreeDeviceList(void) { }
void XFreeDeviceState(void) { }
void XQueryDeviceState(void) { }
void XSelectExtensionEvent(void) { }
void XGetExtensionVersion(void) { }
void _XiGetDevicePresenceNotifyEvent(void) { }
void *XOpenDevice(void) { return NULL; }
void *XListInputDevices(void) { return NULL; }
C
gcc -shared -o libXi.so.6 xi_stub.c -Wl,-soname,libXi.so.6
for L in libXrender.so.1 libSM.so.6 libICE.so.6 libXt.so.6; do
  printf '' > empty.c
  gcc -shared -o "$L" empty.c -Wl,-soname,"$L"
done
# --- xkbcommon stub: MUST carry the V_0.5.0 symbol version (glibc 2.36
# asserts otherwise on the versioned reference from bpy) ---
python3 - <<'PY'
syms = """XkbFreeKeyboard XkbGetControls XkbGetMap XkbGetNames XkbKeysymToModifiers XkbQueryExtension
XkbSetDetectableAutoRepeat xkb_compose_state_feed xkb_compose_state_get_status
xkb_compose_state_get_utf8 xkb_compose_state_new xkb_compose_state_reset
xkb_compose_state_unref xkb_compose_table_new_from_locale xkb_compose_table_unref
xkb_context_new xkb_context_unref xkb_keymap_key_repeats xkb_keymap_mod_get_index
xkb_keymap_new_from_string xkb_keymap_unref xkb_state_get_keymap xkb_state_key_get_one_sym
xkb_state_key_get_utf8 xkb_state_new xkb_state_serialize_mods xkb_state_unref
xkb_state_update_mask""".split()
obj = {'xkb_compose_state_new','xkb_compose_table_new_from_locale','xkb_context_new',
       'xkb_keymap_new_from_string','xkb_state_new','XkbGetControls','XkbGetMap','XkbGetNames'}
lines = ["#include <stddef.h>"]
for s_ in syms:
    lines.append("void *%s(void) { return NULL; }" % s_ if s_ in obj else "void %s(void) { }" % s_)
open("xkb_stub.c","w").write("\n".join(lines))
open("xkb.map","w").write("V_0.5.0 { global: Xkb*; xkb_*; local: *; };\n")
PY
gcc -shared -o libxkbcommon.so.0 xkb_stub.c -Wl,-soname,libxkbcommon.so.0 -Wl,--version-script=xkb.map
echo "stubs OK"
