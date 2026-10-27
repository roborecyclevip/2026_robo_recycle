# System flowchart

Updated 28 October 2026 from `System Integration/main/` at commit `3b2d02b` and the team's intended RPM/current engagement plan. The physical setup no longer uses the load cell. This is a documentation update; it does not change the firmware.

![Current removal cycle, experimental sensing and planned engagement](images/system_flowchart.svg)

[PNG for Canva](images/system_flowchart.png) · [SVG](images/system_flowchart.svg)

## Current removal cycle

`UNSCREW X Y` calls `runScrewRemovalFlow`. `UNSCREWCHAIN` runs it for a coordinate list. The `LoadcellPi_*` names are legacy names: these functions currently ask the operator through Serial; they are not automatic sensor decisions.

```mermaid
flowchart LR
  A([Start]) --> B[Initialise serial, motor, encoder and gantry]
  B --> C{Endstops ready?}
  C -- No --> D[Stay still at startup; check endstops]
  C -- Yes --> E[Home axes]
  E --> F[Input screw XY; move at safe Z]
  F --> G[Manual XY nudges; operator enters DONE]
  G --> H[Operator confirms contact or commands 0.5 mm Z steps]
  H --> I{Contact before 8.5 mm limit?}
  I -- No --> X[Report this screw failed]
  I -- Yes --> J[Unscrew 180 degrees counterclockwise]
  J --> K{Completed within 8 seconds?}
  K -- No --> X
  K -- Yes --> L{Operator confirms screw dropped?}
  L -- No --> M{Operator requests another pass?}
  M -- No --> X
  M -- Yes --> N[Optional operator-controlled 0.5 mm Z feed]
  N --> J
  L -- Yes --> O[Retract to safe Z; brake spindle]
  O --> P[Move to magnet / screw drop-off]
  P --> Q{Another coordinate?}
  X --> Q
  Q -- Yes --> F
  Q -- No --> R([Finish / report results])
```

The chain currently continues after a failed screw. The failure returns do **not** all perform the success-path retraction and drop-off; do not interpret the diagram as a complete automatic recovery system. Startup's endstop check is not a general motion interlock.

The code's safe Z is 80 mm and drop-off coordinates are `(225, 330)` via approach Y = 280 mm. These are firmware configuration values, not verified dimensions of the illustration model.

## Experimental engagement test already in code

`UNSCREW_ENGAGE X Y Z [signed_speed] [finish_ms]` is separate from `UNSCREW`; it does not automatically begin the removal cycle or reverse direction when engagement is detected.

```mermaid
flowchart LR
  A[Validate arguments] --> B[Raise before XY travel; approach 20 mm above target Z]
  B --> C[Spin up 1 second; sample free-spin baseline for 1 second]
  C --> D{Baseline valid and stable?}
  D -- No --> Z[Brake; stop Z; report abort]
  D -- Yes --> E[Brake 0.5 seconds; restart; ignore 1 second spin-up]
  E --> F[Bounded Z move to target; sample RPM and motor current]
  F --> G[Record engagement candidate when both signals agree]
  G --> H[Complete the same bounded finish spin either way]
  H --> I[Brake; retract vertically; report detected / not detected]
  F -. BRAKE command or descent timeout .-> Z
```

Current detector settings in `EngagementDetection.h`:

- Compare absolute RPM with a stable free-spin baseline.
- Candidate RPM drop: at least 2.5%, on two checks spaced at least 100 ms apart.
- Candidate current increase: at least 0.08 A above baseline, using a five-sample moving average.
- Require the current rise within a 200 ms coincidence window of RPM confirmation.

These are experimental tuning values, **not proof that the bit is seated** and not calibrated limits for every drill/HDD. The test records detection but finishes the same Z/spin sequence whether detection occurs or not.

## Planned integration

```mermaid
flowchart LR
  A[Stable free-spin RPM/current baseline] --> B[Controlled approach within travel and time bounds]
  B --> C{Sustained RPM drop AND current rise?}
  C -- No --> D{Retry / travel budget remains?}
  D -- Yes --> B
  D -- No --> E[Stop and request operator review]
  C -- Yes --> F[Validate engagement; stop approach]
  F --> G[Hand off to counterclockwise removal passes]
  G --> H[Keep manual release confirmation until separately validated]
```

The planned change replaces the manual contact/engagement prompt with combined RPM/current feedback. Automatic hand-off/reversal, retry handling and reliable release sensing still need integration and validation. Camera-to-gantry coordinate generation is also future work; the current removal entry point receives XY over Serial.

Legacy `Loadcell_Init()`, `LOAD` support and load-cell wording remain in the source. They are omitted from the intended physical workflow because the team has removed the load cell. No force threshold or tare step belongs in the new hardware diagram.

Sources: [main.ino](../System%20Integration/main/main.ino), [Loadcell_pi.cpp](../System%20Integration/main/Loadcell_pi.cpp), [ScrewEngagement.cpp](../System%20Integration/main/ScrewEngagement.cpp), [EngagementDetection.h](../System%20Integration/main/EngagementDetection.h).
