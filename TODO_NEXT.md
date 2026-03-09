# TODO (Next Debug Iteration)

1. Add async job mode for `wechat_send_message_fara` (`start`/`poll`) so MCP calls never block on long Fara inference.
2. Add hard timing telemetry to tool output: total runtime, per-step runtime, per-model-call runtime.
3. Improve WeChat search-popup targeting:
   - detect popup region explicitly,
   - click exact Group Chats row by relative geometry,
   - verify chat header after click before typing.
4. Add strict focus guard in Fara path (abort if active window is not WeChat before type action).
5. Add replayable integration test script for dual-monitor setups with saved evidence and pass/fail assertions.
6. Update README troubleshooting with timeout causes and recommended parameters (`max_runtime_seconds`, `max_steps`, `step_delay_ms`).
