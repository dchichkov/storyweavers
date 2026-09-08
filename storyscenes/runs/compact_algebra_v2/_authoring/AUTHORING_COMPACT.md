# Executable Storyscenes algebra

Author warm, clever stories for ages 5–8, with concrete wants, an earned turn,
and endings that show what changed. Compose reusable opportunities on shared
physical characters/props; their guards decide order. Do not write fixed routes.
The seed chooses initial conditions, not a completed story. Generate one JSON
world: no Python and no duplicate explanatory plan. The compiler supplies RNG,
knowledge slots, bookkeeping, constraints, search, traces and later prose guards.

## World format

Required: title (text), entities (map), compose (map), goal (conditions),
outcomes (state-key list). Optional: premise (one sentence), vary (map), kernels
(map), rules (map), premises (key list), labels (key-to-text map), prune (boolean,
default true).

Each entity: {"name":"Ada","kind":"child","state":{"want":"deliver invitations",
"memes.Care":2,"delivered":false}}. Every state field belongs to a physically
present carrier. Use ada.performance_style, not an abstract concert entity
disguised as a prop. State is scalar string/number/boolean/null. Declare all state
keys before using them except knowledge and loan bookkeeping, which the library
adds. Physical .owner/.location values must name entity IDs. Entities may include
places. Ownership, knowledge, motives and physical state must stay distinct.

vary maps dimension names to arrays of overrides, e.g.
{"weather":[{"garden.wind":"still"},{"garden.wind":"breezy"}],
 "recipient":[{"neighbor.want":"quiet"},{"neighbor.want":"join"}]}.
Dimensions are sampled independently; each override changes already declared
full dotted keys. Correlated changes can share one dimension. At most 64 initial
configurations; every one must be solvable. Prefer a few interacting differences
over cosmetic variation. premises defaults to the varied keys.

Conditions use {"key":value} for equality or {"key":["ne",value]} etc.
Operations: eq/ne/lt/le/gt/ge. A list of [key,op,value] triples also works.
goal is a conjunction of conditions. rules maps names to {must:conditions,
when:conditions}; when is optional. Outcome keys describe completed physical or
social consequences, not just an intention or selected plan. The goal must require
the actual delivery/performance/response. A goal may require outcome != "none"
so several different accomplishments can satisfy it.

## Opportunities and reusable kernels

compose is a map of stable instance IDs to nodes. A node has op and optional
args, when, summary, pivotal, weight, max_uses, divide. Summary is one short
factual clause for the trace, not finished prose. max_uses defaults to 1; weight
defaults to 1. divide attenuates selection weight; it cannot override a guard.

Built-ins (args are positional strings):

- Observe: [observer, physical_fact_key]. Copies the actual fact to
  observer.knows.physical_fact_key, automatically declared null. Add perceptual
  prerequisites when needed; no automatic omniscience.
- Tell: [speaker,listener,physical_fact_key]. Requires non-null speaker knowledge,
  copies the speaker's stored belief, including a stale belief. It does not read
  truth directly. Knowledge slots are automatically declared; do not duplicate
  them unless someone starts with explicit knowledge or a false belief.
- Transfer: [giver,recipient,prop]. Requires prop.owner == giver and changes
  ownership to recipient. Additional when guards restrict consent, motives etc.
- Lend: [lender,borrower,prop]. Transfer plus prop.loaned_by=lender, requires no
  existing loan; the loan slot defaults to null.
- Return: [borrower,lender,prop]. Requires borrower ownership and the recorded
  lender, returns ownership and clears the loan. Require loaned_by:null in the
  goal if this story must finish with the object returned.
- Move: [actor,prop,destination]. Requires actor ownership, sets prop.location to
  an existing destination entity. Declare the initial location explicitly.
- Act: custom story-specific operation. Use actors:[entity IDs], when,
  set:{key:scalar}, inc:{key:number}, copy:{destination_key:source_key}. No args.
  Effects are simultaneous; copies read pre-state. At least one effect is needed.
  Optional label names the operation in traces. Only Act accepts actors/effects.

Every physical success needs sufficient prerequisites. A desire is not knowledge.
Observe before knowledge-dependent decisions; show reasons for changing motives
by updating embedded state, e.g. child.memes.Care. Do not introduce narration-only
bookkeeping like phase counters. A character cannot transfer another's prop.

The shared composite DiscoverAndShare takes [observer,listener,fact] and adds
two opportunities, notice (Observe) and share (Tell). It is already in the
library: call it directly, without redefining it. The solver may interleave
other patterns between its steps, or use discovery without sharing if sufficient.

Local kernels have roles (ordered argument names) and body (a compose map).
Role references use $name, also inside dotted keys. They can call other local
kernels, but recursive expansion is forbidden. Example:

    "kernels": {
      "LearningPair": {
        "roles":["observer","listener","fact"],
        "body": {
          "notice":{"op":"Observe","args":["$observer","$fact"]},
          "share":{"op":"Tell","args":["$observer","$listener","$fact"]}
        }
      }
    },
    "compose": {
      "wind_news":{"op":"LearningPair","args":["ada","dragon","garden.wind"]},
      "wish_news":{"op":"LearningPair","args":["dragon","ada","neighbor.want"]}
    }

Expanded IDs are wind_news.notice, wind_news.share etc. A composite call accepts
only op,args,divide; put guards/effects in its body, with roles for variable values.
All opportunities compose through shared state; the map order does not prescribe
a plot. A named composite should be useful with different bindings, not contain
an entire predetermined plot. Use a shared or local composite with two bindings,
and shared Observe/Tell/Transfer actions that matter. Define local kernels only
when they express useful behavior beyond what the shared library already does.

Aim for 12–18 expanded candidates and 5–10 selected consequential events. Give
at least three genuinely different initial problems and consequences, with
interactions between kernels. Avoid independent errands and fake alternatives
that differ only in color. Pivotal marks an earned character turn, not every step.
All intended outcome fields with scene writers must change in some sampled path.
The driver will compile, test all initial configurations and 100 seeds, show
three executed previews, then ask for prose. Keep this output focused on the
world's distinctive causal design; the shared library provides the machinery.
