"""THE REACT LOOP - this is yours to write.

Everything else in this project is plumbing. These ~20 lines are the whole of
chapter 1: think -> act -> observe, with `context = static prefix + trajectory`
rebuilt from scratch on every single turn.

The book's skeleton (ch.1, fig 1-4):

    trajectory = [user_request]
    repeat:
        context  = stable_prefix + trajectory
        decision = Model(context)
        trajectory.append(decision)
        if decision has no tool call:
            return decision.answer
        for call in decision.tool_calls:
            validated   = Harness.validate(call)
            observation = Environment.execute(validated)
            trajectory.append(observation)

Verify your implementation with NO api key and NO cost:

    uv run python test_loop.py

All tests must pass. Then run it for real:

    uv run python main.py --task "..." --simulate 0
"""


def run_react_loop(model, harness, task, tracer, max_turns=12):
    """Run the agent until it answers, or until the turn budget is exhausted.

    Parameters
    ----------
    model : callable
        `model(messages, tools) -> Decision`. Decision has `.message` (dict),
        `.tool_calls` (list, possibly empty), `.answer` (str or None) and
        `.usage` (dict with 'prompt' / 'cached' / 'completion').
    harness : Harness
        Assembles context and executes tools. The methods you need:
            harness.build_context(trajectory) -> list[dict]   # prefix + trajectory
            harness.tools_param()             -> list | None  # tool schemas
            harness.record_decision(trajectory, decision)     # append the reply
            harness.execute(call)             -> str          # validate + run
            harness.record_observation(trajectory, call_id, name, content)
    task : str
        The user's request.
    tracer : Tracer
        Call `tracer.turn(turn_number, decision.usage, len(context), tool_names)`
        exactly once per model call, right after the model returns.
    max_turns : int
        Stop condition. Without one, a confused agent loops forever.

    Returns
    -------
    (answer, trajectory, stop_reason)
        answer      : str  when the model replied with no tool calls, else None
        trajectory  : the full message history you built
        stop_reason : "answered" | "max_turns"
    """

    # 1. Seed the trajectory with the user's request.
    #    Note what is NOT here: the system prompt and the tool definitions.
    #    They are the static prefix; the harness prepends them every turn.
    trajectory = [{"role": "user", "content": task}]

    for turn in range(1, max_turns + 1):
        # TODO 2. Build this turn's context.        -> harness.build_context(...)

        # TODO 3. Ask the model what to do next.    -> model(context, harness.tools_param())

        # TODO 4. Record the turn for instrumentation.
        #         tracer.turn(turn, decision.usage, len(context),
        #                     [c["function"]["name"] for c in decision.tool_calls])

        # TODO 5. Append the decision to the trajectory. -> harness.record_decision(...)
        #         Why before executing anything? Because the tool results that
        #         follow must come *after* the call that asked for them, or the
        #         provider rejects the message sequence.

        # TODO 6. Stop condition: no tool calls means the model is done.
        #         return decision.answer, trajectory, "answered"

        # TODO 7. Otherwise execute every call and append each observation.
        #         for call in decision.tool_calls:
        #             observation = harness.execute(call)
        #             harness.record_observation(trajectory, call["id"],
        #                                        call["function"]["name"], observation)
        #         Independent calls could run in parallel here - the book's
        #         comment "independent calls may run in parallel" lives at this line.

        raise NotImplementedError("loop.py: implement steps 2-7, then delete this line")

    # 8. Budget exhausted. Returning a reason beats returning nothing.
    return None, trajectory, "max_turns"
