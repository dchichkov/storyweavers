#!/usr/bin/env python3
"""
A small storyworld for a rhyming mystery and reconciliation tale.

Premise:
A client arrives with a tiny worry: something important is missing.
The helper and the client search, misunderstand, and then reconcile when the
clue is found and the missing thing is restored.

The simulation tracks physical state in meters and feelings in memes.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "client"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    vibe: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    missing: str
    clue: str
    hideout: str
    rhyme1: str
    rhyme2: str
    risk: str


@dataclass
class ReconciliationTool:
    id: str
    label: str
    use_line: str
    effect_line: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "tiny_office": Setting(place="the tiny office", vibe="quiet", affords={"search", "tea"}),
    "front_desk": Setting(place="the front desk", vibe="busy", affords={"search", "tea"}),
    "reading_nook": Setting(place="the reading nook", vibe="cozy", affords={"search", "tea"}),
}

MYSTERIES = {
    "blue_button": Mystery(
        id="blue_button",
        missing="blue button",
        clue="under the round rug",
        hideout="a round rug",
        rhyme1="A blue button slipped away, and hid itself from view.",
        rhyme2="It whispered, 'Find the rug, and I will peek out too.'",
        risk="the client would feel blue",
    ),
    "red_key": Mystery(
        id="red_key",
        missing="red key",
        clue="behind the teapot",
        hideout="the teapot",
        rhyme1="A red key skated out of sight with a tiny clink and ping.",
        rhyme2="It hid behind the teapot, like a secret little king.",
        risk="the door would stay locked tight",
    ),
    "golden_note": Mystery(
        id="golden_note",
        missing="golden note",
        clue="inside the basket",
        hideout="the basket",
        rhyme1="A golden note was gone one day, as quiet as a bee.",
        rhyme2="It tucked itself inside the basket, where warm napkins could be.",
        risk="the client would miss the message",
    ),
}

TOOLS = {
    "gentle_words": ReconciliationTool(
        id="gentle_words",
        label="gentle words",
        use_line="She took a breath and chose some gentle words.",
        effect_line="The air grew soft, and both hearts felt heard.",
    ),
    "shared_search": ReconciliationTool(
        id="shared_search",
        label="shared search",
        use_line="Then they searched together, side by side.",
        effect_line="The grumpy look slipped away like a low tide.",
    ),
    "warm_tea": ReconciliationTool(
        id="warm_tea",
        label="warm tea",
        use_line="A cup of warm tea helped the worry slow.",
        effect_line="The steam rose up like a friendly hello.",
    ),
}

CLIENT_NAMES = ["Mina", "Toby", "Lena", "Noah", "Pia", "Eli"]
HELPER_NAMES = ["June", "Moss", "Rae", "Finn", "Iris", "Zed"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    mystery: str
    tool: str
    client_name: str
    helper_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A mystery is reasonable if it has a clue and a reconciliation path.
reasonable(M) :- mystery(M), clue(M,_), tool(T), helps(T,M).

% A tool helps a mystery when it can settle the feelings and support the search.
helps(T,M) :- reconciliation_tool(T), searchable(M), soothing(T).

#show reasonable/1.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue", mid, m.clue))
        lines.append(asp.fact("searchable", mid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("reconciliation_tool", tid))
        lines.append(asp.fact("soothing", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show reasonable/1."))
    clingo_set = set(asp.atoms(model, "reasonable"))
    python_set = {(mid,) for mid in valid_mysteries()}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_mysteries() ({len(clingo_set)} mysteries).")
        return 0
    print("MISMATCH between clingo and valid_mysteries():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def valid_mysteries() -> list[str]:
    return [mid for mid, m in MYSTERIES.items() if m.clue and m.risk]


def can_reconcile(tool: ReconciliationTool, mystery: Mystery) -> bool:
    return tool.id in TOOLS and mystery.id in MYSTERIES


def choose_name(rng: random.Random, genderish: str) -> str:
    return rng.choice(CLIENT_NAMES if genderish == "client" else HELPER_NAMES)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming mystery storyworld with reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--client-name")
    ap.add_argument("--helper-name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = []
    for setting in SETTINGS:
        for mystery in MYSTERIES:
            for tool in TOOLS:
                if args.setting and setting != args.setting:
                    continue
                if args.mystery and mystery != args.mystery:
                    continue
                if args.tool and tool != args.tool:
                    continue
                combos.append((setting, mystery, tool))
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, tool = rng.choice(sorted(combos))
    client_name = args.client_name or rng.choice(CLIENT_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    return StoryParams(setting=setting, mystery=mystery, tool=tool, client_name=client_name, helper_name=helper_name)


def valid_story_combo(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    if params.tool not in TOOLS:
        raise StoryError("Unknown tool.")
    if not can_reconcile(TOOLS[params.tool], MYSTERIES[params.mystery]):
        raise StoryError("This reconciliation path is not reasonable.")


def generate(params: StoryParams) -> StorySample:
    valid_story_combo(params)
    world = World(SETTINGS[params.setting])
    client = world.add(Entity(id=params.client_name, kind="character", type="client"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type="helper"))
    mystery = MYSTERIES[params.mystery]
    tool = TOOLS[params.tool]

    # Set up state
    client.memes["worry"] = 2.0
    helper.memes["care"] = 1.0
    world.facts.update(client=client, helper=helper, mystery=mystery, tool=tool)

    world.say(f"In {world.setting.place}, the day was {world.setting.vibe} and still.")
    world.say(f"A client named {client.id} came in with a puzzled face, a tiny wobble, a hint of worry spill.")
    world.say(mystery.rhyme1)
    world.say(f"{client.id} looked high and low, but the {mystery.missing} was nowhere near.")
    world.para()

    # Conflict: a misunderstanding and a search.
    client.memes["tension"] = 1.0
    helper.memes["tension"] = 1.0
    world.say(f"{helper.id} said, 'Let's look around,' but {client.id} snapped, 'I cannot wait here!'")
    world.say(f"Then the two of them searched by the desk and the shelves, with quick little feet.")
    world.say(f"The clue was waiting {mystery.clue}, where soft things often meet.")
    world.facts["clue_found"] = True
    world.para()

    # Resolution: reconciliation.
    world.say(tool.use_line)
    client.memes["worry"] = 0.0
    client.memes["trust"] = 2.0
    helper.memes["trust"] = 2.0
    client.memes["tension"] = 0.0
    helper.memes["tension"] = 0.0
    world.say(tool.effect_line)
    world.say(f"They found the {mystery.missing} at last, with a sparkle and a grin.")
    world.say(f"{client.id} said, 'I am sorry,' and {helper.id} replied, 'Come on in.'")
    world.say(mystery.rhyme2)
    world.say(f"By the end, the client felt calm, and the helper felt proud; the lost thing was back, and the room felt loud with happy peace.")

    world.facts["resolved"] = True
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    m: Mystery = f["mystery"]
    t: ReconciliationTool = f["tool"]
    c: Entity = f["client"]
    h: Entity = f["helper"]
    return [
        f'Write a short rhyming story about a client who loses a {m.missing} and finds it with help.',
        f"Tell a gentle mystery story in {world.setting.place} where {c.id} and {h.id} reconcile after a search.",
        f"Write a child-friendly rhyme about a missing {m.missing}, a clue, and {t.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c: Entity = f["client"]
    h: Entity = f["helper"]
    m: Mystery = f["mystery"]
    t: ReconciliationTool = f["tool"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about a client named {c.id}, a helper named {h.id}, and a small missing mystery about the {m.missing}.",
        ),
        QAItem(
            question=f"What was missing?",
            answer=f"The missing thing was the {m.missing}. The clue led them to {m.clue}.",
        ),
        QAItem(
            question=f"How did the client and helper make peace?",
            answer=f"They made peace by using {t.label}, searching together, and saying sorry after the clue led them to the {m.missing}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps solve a mystery.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means two people stop being upset and become friendly again.",
        ),
        QAItem(
            question="Why can a shared search help?",
            answer="A shared search can help because two people can look in more places and work together instead of apart.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def asp_facts_show() -> str:
    return asp_facts()


def asp_valid_mysteries() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/1."))
    return sorted(set(asp.atoms(model, "reasonable")))


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for m in MYSTERIES:
            for t in TOOLS:
                combos.append((s, m, t))
    return combos


def build_samples(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for s, m, t in valid_combos():
            p = StoryParams(setting=s, mystery=m, tool=t, client_name=CLIENT_NAMES[0], helper_name=HELPER_NAMES[0])
            samples.append(generate(p))
        return samples
    seen: set[str] = set()
    i = 0
    while len(samples) < args.n and i < max(50, args.n * 20):
        seed = base_seed + i
        i += 1
        params = resolve_params(args, random.Random(seed))
        params.seed = seed
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_mysteries()
        print(f"{len(triples)} reasonable mysteries:\n")
        for t in triples:
            print(f"  {t[0]}")
        return

    samples = build_samples(args)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
