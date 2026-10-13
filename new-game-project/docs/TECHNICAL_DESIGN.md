# Technical Design
**Status: PROPOSED**

Start with a small local Python prototype. Keep game rules separate from UI and persistence; make random behavior testable; persist only the minimum profile/meta-progression data needed for the core loop. Avoid pre-creating modules without need.

Potential areas, to split only when useful: state, traits, combat, death attribution, meta-progression, world/rooms, UI, persistence.

Open questions: interface, save format, tick event ordering, testing random outcomes, and placement of simulation utilities.
