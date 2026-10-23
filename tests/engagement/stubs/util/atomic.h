#pragma once
// Native tests have no interrupts; AVR compilation checks the real implementation.
#define ATOMIC_RESTORESTATE 0
#define ATOMIC_BLOCK(mode) for (bool once = true; once; once = false)
