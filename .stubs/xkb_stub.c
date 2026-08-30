#include <stddef.h>
void XkbFreeKeyboard(void) { }
void *XkbGetControls(void) { return NULL; }
void *XkbGetMap(void) { return NULL; }
void *XkbGetNames(void) { return NULL; }
void XkbKeysymToModifiers(void) { }
int XkbQueryExtension(void) { return 0; }
void XkbSetDetectableAutoRepeat(void) { }
void xkb_compose_state_feed(void) { }
int xkb_compose_state_get_status(void) { return 0; }
int xkb_compose_state_get_utf8(void) { return 0; }
void *xkb_compose_state_new(void) { return NULL; }
void xkb_compose_state_reset(void) { }
void xkb_compose_state_unref(void) { }
void *xkb_compose_table_new_from_locale(void) { return NULL; }
void xkb_compose_table_unref(void) { }
void *xkb_context_new(void) { return NULL; }
void xkb_context_unref(void) { }
int xkb_keymap_key_repeats(void) { return 0; }
int xkb_keymap_mod_get_index(void) { return 0; }
void *xkb_keymap_new_from_string(void) { return NULL; }
void xkb_keymap_unref(void) { }
void xkb_state_get_keymap(void) { }
int xkb_state_key_get_one_sym(void) { return 0; }
int xkb_state_key_get_utf8(void) { return 0; }
void *xkb_state_new(void) { return NULL; }
int xkb_state_serialize_mods(void) { return 0; }
void xkb_state_unref(void) { }
void xkb_state_update_mask(void) { }