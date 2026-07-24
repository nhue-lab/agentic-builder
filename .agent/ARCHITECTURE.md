# System Architecture Reference

## Execution & Task Loops (Ralph Loop)
The system separates tactical execution from strategic task evaluation:

1. **Execution Loop (Tactical ReAct)**:
   `Idle -> Reason -> Route -> Execute (Skills)`
   Runs inside `AgentEngine`. The agent calls tools (skills) and accumulates intermediate execution history.

2. **Task Loop / Ralph Loop (Strategic Validation)**:
   Runs inside `TaskLoop`. Once the agent proposes a solution, `CritiqueAgent` evaluates it. 
   If validation fails:
   * The context is completely reset (empty message history) to avoid *context rot*.
   * A post-mortem feedback message is formulated and injected into the system prompt.
   * A fresh attempt is launched with the post-mortem context.

## Rule of Permission Cloisonnement
Any skill invoked by the LLM must be explicitly listed in `AgentState.injected_skills`. If a mismatch is detected, a `PermissionError` is raised.
