import test from "node:test";
import assert from "node:assert/strict";

test("web smoke test baseline", () => {
  assert.equal(1 + 1, 2);
});
