# Decision Log
Record only decisions explicitly approved by the Game Director.

## Template
### YYYY-MM-DD — Short title
- **Status:** APPROVED / PROVISIONAL / REJECTED / DEFERRED
- **Decision:**
- **Reason:**
- **Consequences:**
- **Revisit when:**

### Initial direction — Python-first local prototype
- **Status:** PROVISIONAL
- **Decision:** Begin with a local Python prototype and minimal tooling.
- **Reason:** Validate the core loop before production infrastructure.

### 2026-10-16 — Defend action (prototype)
- **Status:** PROVISIONAL
- **Decision:** A character may Defend on its turn instead of attacking. The next attack against that character is blocked completely (0 damage, including an otherwise lethal hit) and consumes the block. Blocks do not stack, and the block belongs to the defended character.
- **Reason:** Give the player a tactical alternative to attacking in the combat prototype. Approved by the Game Director for this prototype; not final combat balance.
- **Consequences:** `Action.DEFEND`, `Character.defending`, `AttackResult.blocked`; `a`/`d`/`q` controls in `game.sim`. With fixed damage and an enemy that always attacks, a defend turn cancels one round and does not change the outcome.
- **Revisit when:** enemies vary their actions or damage gains variability, or playtesting shows Defend is not a meaningful choice.
