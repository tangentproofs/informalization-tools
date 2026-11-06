NODES = []
def node(id, title, summary, body, quiz, caveats=(), widgets=None):
    NODES.append(dict(id=id, title=title, summary=summary, body=body, quiz=quiz, caveats=list(caveats), widgets=widgets))
def q(text, choices, answer, explain):
    return {"q": text, "type": "choice", "choices": choices, "answer": answer, "explain": explain}
def walk(title, steps):
    return [{"type": "walkthrough", "title": title, "config": {"steps": steps}}]

node("Swarm",
 "A swarm: machines joined by channels",
 "A swarm is a list of b4 machines, a script (append-only log) of timestamped messages for each numbered channel, a read cursor per machine per channel, and an owner per channel, the only machine allowed to send on it.",
 r"""## Plain English

**Structure (`Swarm`, B4/Swarm.lean lines 32–41).**

* `ms`: the machines, each an ordinary [State](#/node/State);
* `chans`: for each channel number, the list of messages sent so far. A message (`Msg`, line 29) is a value and
  the sender's clock when it was sent;
* `rd`: for each machine, how far it has read on each channel. Each reader has its own cursor, so every reader
  sees every message: a channel is a broadcast log, not a queue that a read empties;
* `owner`: the machine allowed to write each channel. A send by any other machine waits forever.

Machines reach channels through the ordinary `io` instruction with three new commands (module doc, lines 11–19):
`'s'` send, `'r'` receive, `'k'` check. The interpreter by itself ignores them
([runOp](#/node/runOp)); the swarm intercepts them in [stepAt](#/node/Swarm.stepAt).

`Swarm.ofMachines` (lines 218–219) builds a swarm with empty channels and cursors at 0. `loadCode` (lines
212–214) loads bytes at 0x100 and sets the machine running.

**What is tested.** `SwarmDemo` (lines 221–235) runs a sender (send 2 on channel 0, halt) next to a receiver
(receive on channel 0, store at 0x200, halt) for 100 rounds. The comment at line 232 says the receiver ends with 2
at 0x200 and clock 1. That is an `#eval` whose expected output is written in a comment, so it fails nothing if the
output differs.
""",
 [q("If two machines both read channel 3, does one reader's receive hide the message from the other?",
    ["No. Each machine has its own cursor, so both see every message", "Yes, a receive removes it"], 0,
    "`rd` is per machine (B4/Swarm.lean line 38), and `recv` only advances that machine's cursor (lines 85–86)."),
  q("What does a message carry besides its value?",
    ["The sender's clock at the time of sending", "The sender's index", "Nothing"], 0, "B4/Swarm.lean lines 28–29 and 71."),
  q("What happens when a machine sends on a channel it doesn't own?",
    ["It can't take that step, so it waits forever", "The message is dropped", "Ownership transfers"], 0,
    "B4/Swarm.lean lines 39–40 and 110."),
 ],
 caveats=["The demo is TESTED only by an `#eval` with its expected output in a comment."])

node("Swarm.stepAt",
 "One swarm step for machine i",
 "Status: DEFINED, plus PROVEN unfolding lemmas. A running machine takes its own step, unless its next op is `io` with send, receive or check. Then the swarm does the I/O: a send needs ownership, and a receive or check needs a message already in the channel. Otherwise the machine waits.",
 r"""## Plain English

**Definition (`Swarm.stepAt`, B4/Swarm.lean lines 104–114).** Look up machine *i*. If it isn't running, no step.
Otherwise look at `ioCmd` (lines 51–52): if the next byte is `io`, the command is the top of the data stack.

* `'s'`: if machine *i* owns the channel, [send](#/node/Swarm.recv); otherwise no step.
* `'r'`: [receive](#/node/Swarm.recv), or no step if no message is waiting.
* `'k'`: [check](#/node/Swarm.check), or no step if no message is waiting.
* anything else: the machine's own [step](#/node/step).

**Scheduling.** `Swarm.sweep` (lines 117–121) gives each machine one chance, in index order, and reports whether
any moved. `Swarm.run` (lines 124–126) sweeps up to *n* times and stops early when no machine can move. Both are
total (fuel again).

**A second view of runs.** `Swarm.Step` (line 156) says *some* machine can step from *w* to *w'*, in any order,
and `Swarm.Steps` (lines 159–163) is its reflexive-transitive closure. The intent is to reason about all
interleavings, not just the round-robin one.

### What is proved

* `Swarm.Steps.trans` and `Swarm.Steps.single` (lines 165–171): runs compose.
* `Swarm.stepAt_eq`, `_other`, `_send`, `_recv`, `_check` (lines 175–204): unfolding lemmas, one per case above.
* `running_iff` (lines 206–207): the Boolean `running` matches B4.Theory's `Running`.

That is all. In particular nothing relates `sweep` or `Swarm.run` to `Steps`. The `owner` docstring claims that
"with one writer per channel, the order in which machines run does not matter" (lines 39–40). That claim is
**unproven**.
""",
 [q("Which commands does the swarm intercept?",
    ["io with 's', 'r' or 'k' on top of the stack", "Every io", "Only hl"], 0, "B4/Swarm.lean lines 109–112."),
  q("Is it proved that machine order doesn't matter when each channel has one owner?",
    ["No, it is only a docstring claim", "Yes, in Swarm.lean"], 0,
    "B4/Swarm.lean lines 39–40. No theorem states it."),
  q("Does `Swarm.Steps` follow the round-robin order of `sweep`?",
    ["No. It allows any machine to step at any point", "Yes"], 0, "B4/Swarm.lean line 156."),
  q("When does `stepAt` return `none` for a running machine?",
    ["A send it doesn't own, or a receive or check with no message yet", "Never", "When the stack is empty"], 0,
    "B4/Swarm.lean lines 110–112 and the `none` branches of recv/check (lines 79–80, 98–99)."),
 ],
 caveats=["Status: the definitions are CODE. The unfolding lemmas and `Steps.trans` are PROVEN (short proofs, not built). The order-independence claim is UNPROVEN."])

node("Swarm.recv",
 "Send and receive",
 "Status: DEFINED (no behavioural lemmas). A send appends (value, sender's clock) to the channel. A receive takes the message under this machine's cursor, pushes its value, and moves the clock to at least the send time + 1: a message takes one unit of time to arrive.",
 r"""## Plain English

**Definition (`Swarm.send`, B4/Swarm.lean lines 64–71).** Machine *i*'s stack holds value, channel and `'s'`, with
`'s'` on top. Pop all three, step the pointer past the `io`, and append (value, clock) to that channel.

**Definition (`Swarm.recv`, lines 74–86).** The stack holds channel and `'r'`. Let *r* be machine *i*'s cursor on
that channel. If message *r* exists, push its value, set the clock to the later of the current clock and
send time + 1 (`later`, line 58), move the pointer on, and advance the cursor. If it doesn't exist, return
`none`, so the machine waits.

Commit 4f352c5 describes these as "Swarm.send/recv by projections, for reasoning": they are written with
`(dpop s).1` and `(dpop s).2` rather than pattern matches, so that the [push/pop lemmas](#/node/dpush) apply
directly. **No lemma about send or receive is stated yet**, for example "after a send, a receive by another
machine gets the value".

The clock rule is a Lamport-style logical clock and matches Hehner's convention that communication takes time. It
is what gives the [check](#/node/Swarm.check) its meaning.
""",
 [q("After receiving a message sent at time 7, what is the receiver's clock if it was 3?",
    ["8", "7", "3", "10"], 0, "later(3, 7+1) = 8 (B4/Swarm.lean lines 58 and 83)."),
  q("…and if the receiver's clock was already 20?",
    ["20", "8", "21"], 0, "`later` keeps the larger value (line 58)."),
  q("What does a receive do when the next message hasn't been sent yet?",
    ["Returns none: the machine waits", "Pushes 0", "Halts"], 0, "B4/Swarm.lean line 80."),
 ],
 caveats=["Status: CODE. Nothing about send/receive behaviour is proved."])

node("Swarm.check",
 "The check `k`: Hehner's √c",
 "Status: DEFINED, no lemmas. `c 'k' io` asks whether a message on c is available now. If the next message is in the channel, the answer is −1 when it was sent before the machine's clock, else 0. If no message is there yet, the machine waits: one could still arrive with an earlier stamp.",
 r"""## Plain English

In Eric Hehner's *a Practical Theory of Programming*, √c ("check c") is a Boolean telling a process whether input
is available on channel c at the current time. In this swarm a message sent at time *t* arrives at *t* + 1
([receive](#/node/Swarm.recv)). So it is available at clock *c* exactly when *t* < *c*.

**Definition (`Swarm.check`, B4/Swarm.lean lines 95–100).** Look at the message under machine *i*'s cursor.
If there is one, answer (`Swarm.answer`, lines 89–92: pop the channel and command, push −1
or 0, move on) with whether its send time is below this machine's clock. The cursor does **not** advance, since a
check doesn't consume the message. If there is none, return `none`.

### Why wait instead of answering 0?

If the channel is empty now, the owner may simply not have run yet. Its next send could carry a timestamp earlier
than our clock, and then the right answer would have been −1. Answering 0 immediately would make the answer
depend on scheduling. So the machine waits, and either the message comes, or the swarm gets stuck and
[settle](#/node/Swarm.settle) decides.
""",
 [q("When does `k` answer −1 (true)?",
    ["When the next message on the channel was sent before the machine's current clock",
     "Whenever any message has been sent", "When the channel is empty"], 0,
    "B4/Swarm.lean line 100."),
  q("Does a check consume the message?",
    ["No, the read cursor stays where it is", "Yes"], 0, "`Swarm.answer` (lines 89–92) doesn't touch `rd`."),
  q("Why doesn't an empty channel answer 0 at once?",
    ["The owner might still send a message stamped earlier than this clock",
     "Lean can't decide emptiness", "To save fuel"], 0, "Module doc, B4/Swarm.lean lines 15–19."),
 ],
 caveats=["Status: CODE. That `k` matches Hehner's √c is a design claim in the docstring. No theorem relates it to a specification."])

node("Swarm.settle",
 "Headline: settle, answering a check when the swarm is stuck",
 "Status: DEFINED, soundness UNPROVEN. When no machine can move, `settle` answers 0 for the machine waiting at a check with the earliest clock. The docstring's reason (no message can arrive in time) is not formalised, and it seems to need clocks that never go backwards.",
 r"""## Plain English

**Definition (`Swarm.settle`, B4/Swarm.lean lines 131–143).** List the machines that are running and whose next
instruction is `io` with `'k'` on top. Pick the one with the smallest clock (ties go to the lowest index). Answer 0
for it with `Swarm.answer`. If no machine is waiting at a check, return `none`.

**Definition (`Swarm.runK`, lines 146–153).** With fuel *n* + 1: [run](#/node/Swarm.stepAt) the swarm for up to
*n* + 1 rounds. If machines can still move (the fuel ran out), stop. Otherwise call `settle`. If it answered a
check, continue with *n*; if not, stop: every machine is halted or waiting at a receive, or at a send it doesn't own.

### The argument in the docstring (lines 128–130)

When nothing can move, every other machine has halted, is waiting at a receive, or is waiting at a check with a
clock no earlier than ours. So "no message can come in time": any message that eventually reaches our channel
must be sent after some waiting machine resumes, and any such machine's clock is at least ours. A message stamped
*t* ≥ our clock would not count as available, so 0 is the answer the machine would have got with full knowledge.
This is the "earliest waiting check answers 0" rule of commit ab45195.

### What would make it a theorem, and what stands in the way

Nothing about `settle` or `runK` is proved. A faithful statement would say something like: in every continuation
of the swarm, the next message on that channel has send time ≥ the checker's clock. Two observations from
reading the code, not checked by Lean:

* The argument needs **clocks that never decrease**. But any program can lower its own clock with `!T`
  ([step_wrT](#/node/step_wrT)) or write byte 80 with `wi`, then send a message stamped in the past.
* A machine with its debug flag set counts as "not running", so it can't move. The model has no way to clear that
  flag again, so that case is harmless here.

With clocks that only move forward, the argument looks right.
""",
 [q("Which waiting machine does `settle` answer?",
    ["The running machine at a check with the smallest clock", "The first machine", "Every machine at a check"], 0,
    "B4/Swarm.lean lines 132–142."),
  q("What answer does `settle` give?",
    ["0 (false): no message can arrive in time", "−1", "It lets the machine skip the io"], 0,
    "B4/Swarm.lean line 142."),
  q("Is it proved that the settled answer is correct?",
    ["No. The reason is only argued in the docstring", "Yes, in Swarm.lean"], 0,
    "No theorem mentions `settle` or `runK`."),
  q("What assumption does the docstring's argument appear to need that the machine doesn't enforce?",
    ["Clocks never move backwards", "There are exactly two machines", "Channels have no owners"], 0,
    "`!T` stores any value (B4/Theory.lean lines 897–899)."),
  q("When does `runK` stop?",
    ["Out of fuel, or nothing can move and no machine waits at a check", "After exactly n rounds", "When the first machine halts"], 0,
    "B4/Swarm.lean lines 147–153."),
 ],
 caveats=["Status: DEFINED, with UNPROVEN soundness. Not even stated as a theorem. The headline here is the design, not a result.",
          "The observation about clocks moving backwards is this site's reading of the code, not something the author states. A program that never writes T or byte 80 keeps its clock monotone.",
          "No test exercises `settle` or `runK`: the only swarm `#eval` (SwarmDemo) uses `Swarm.run`."],
 widgets=walk("How settle and runK work (B4/Swarm.lean, lines 128-153)", [
  {"text": "Filter: the indices of machines that are running and whose next instruction is io with 'k' on top (lines 132–135).", "link": "Swarm.check"},
  {"text": "Fold: keep the index with the smallest clock, the first one found winning ties (lines 136–140)."},
  {"text": "Answer 0 for that machine: pop the channel and command, push 0, move past the io (lines 141–143; Swarm.answer, lines 89–92)."},
  {"text": "runK: run up to n+1 rounds. If something can still move, stop and return. Otherwise settle, and on success recurse with n (lines 146–153).", "link": "Swarm.stepAt"},
  {"text": "Unproven: that the 0 is what the machine would see in every continuation. That needs clocks that never go backwards.", "link": "step_wrT"},
 ]))
