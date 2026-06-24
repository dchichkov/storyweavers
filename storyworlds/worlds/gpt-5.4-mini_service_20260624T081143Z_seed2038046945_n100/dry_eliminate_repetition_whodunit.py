#!/usr/bin/env python3
"""
storyworlds/worlds/dry_eliminate_repetition_whodunit.py
=======================================================

A small whodunit-flavored storyworld about a dry room, a repeated clue, and
a suspect line that helps eliminate the repetition.

The tale premise:
- A child notices a strange repeated mark or note.
- The grown-up worries because the same clue keeps appearing.
- The pair use careful looking, a small tool, and a dry place to test the clue.
- The repetition is eliminated, and the real answer is revealed.

The simulated world uses:
- physical meters for dryness, wetness, and evidence
- emotional memes for worry, curiosity, relief, and suspicion
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)


@dataclass
class Setting:
    place: str
    dry: bool = True
    clues: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    repeated_line: str
    hidden_truth: str
    tag: str


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    method: str
    effect: str


@dataclass
class Suspect:
    id: str
    label: str
    phrase: str
    alibi: str
    tell: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple[str, str]] = set()
        self.facts: dict[str, object] = {}

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
        clone = World(self.setting)
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "owner": v.owner, "caretaker": v.caretaker,
            "meters": dict(v.meters), "memes": dict(v.memes)
        }) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        return clone


def _apply_dryness(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meter("wet") >= THRESHOLD and world.setting.dry:
            sig = ("dry", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.meters["dry"] = ent.meter("dry") + 1.0
            ent.meters["wet"] = max(0.0, ent.meter("wet") - 1.0)
            out.append(f"The dry room helped {ent.label} dry off a little.")
    return out


def _apply_eliminate_repetition(world: World) -> list[str]:
    clue = world.facts.get("clue")
    if not isinstance(clue, Clue):
        return []
    suspect: Suspect = world.facts["suspect"]  # type: ignore[assignment]
    tool: Tool = world.facts["tool"]  # type: ignore[assignment]
    detective: Entity = world.facts["child"]  # type: ignore[assignment]

    if detective.meme("curiosity") < THRESHOLD:
        return []
    if world.facts.get("tested_repetition"):
        return []
    if world.facts.get("repetition_removed"):
        return []

    if world.facts.get("tool_used") and world.facts.get("clue_checked"):
        world.facts["repetition_removed"] = True
        detective.memes["relief"] = detective.meme("relief") + 1.0
        world.facts["revealed_truth"] = clue.hidden_truth
        return [f"The repeated line was eliminated once {tool.label} showed the dry clue underneath."]
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in (_apply_dryness, _apply_eliminate_repetition):
            sents = fn(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def ask_question(world: World) -> None:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    child.memes["curiosity"] = child.meme("curiosity") + 1.0
    world.say(
        f"{child.label} noticed the same clue again and again, and that repetition felt odd."
    )


def describe_setting(world: World) -> None:
    if world.setting.dry:
        world.say(f"The {world.setting.place} was dry and still, with no rain to blur the clues.")
    else:
        world.say(f"The {world.setting.place} was damp, so every clue needed a careful look.")


def introduce_clue(world: World, clue: Clue) -> None:
    world.say(
        f"On the floor, {clue.phrase} appeared more than once. Each repeated line looked the same."
    )


def suspect_scene(world: World, suspect: Suspect) -> None:
    world.say(
        f"{suspect.label} had an alibi, but {suspect.tell} made the child look twice."
    )


def test_clue(world: World, clue: Clue, tool: Tool) -> None:
    world.facts["clue_checked"] = True
    world.facts["tool_used"] = True
    world.say(
        f"{tool.phrase} helped {world.facts['child'].label} check the clue with care."
    )
    if world.setting.dry:
        world.say(
            f"In the dry light, the same mark no longer hid itself."
        )
    else:
        world.say(
            f"Because the room was damp, the mark only showed after the careful test."
        )
    world.say(f"{tool.method.capitalize()} {tool.effect}, and the repeated clue became easy to read.")


def reveal(world: World, suspect: Suspect, clue: Clue) -> None:
    world.say(
        f"It was not {suspect.label} at all. The clue kept repeating because {clue.hidden_truth}."
    )
    world.say(
        f"Once the repetition was gone, the room felt calm and dry again."
    )


def tell(setting: Setting, clue: Clue, tool: Tool, suspect: Suspect, hero_name: str = "Mina") -> World:
    world = World(setting)
    child = world.add(Entity(
        id=hero_name,
        kind="character",
        type="child",
        label=hero_name,
        meters={"dry": 1.0},
        memes={"curiosity": 0.0, "worry": 0.0, "relief": 0.0, "suspicion": 0.0},
    ))
    grownup = world.add(Entity(
        id="grownup",
        kind="character",
        type="adult",
        label="the grown-up",
        memes={"worry": 1.0},
    ))
    world.facts.update(child=child, grownup=grownup, clue=clue, tool=tool, suspect=suspect)

    describe_setting(world)
    world.say(f"{child.label} found {clue.phrase} in the {setting.place}.")
    introduce_clue(world, clue)
    ask_question(world)
    world.para()

    world.say(f"{grownup.label} said the repeated line might point to someone nearby.")
    suspect_scene(world, suspect)
    child.memes["suspicion"] = child.meme("suspicion") + 1.0
    world.say(
        f"{child.label} wanted to eliminate the repetition and see what the clue was hiding."
    )
    world.para()

    test_clue(world, clue, tool)
    world.facts["tested_repetition"] = True
    propagate(world, narrate=True)
    reveal(world, suspect, clue)
    return world


SETTINGS = {
    "study": Setting(place="the study", dry=True, clues={"ink", "paper", "desk"}),
    "hall": Setting(place="the hall", dry=True, clues={"shoe", "key", "note"}),
    "attic": Setting(place="the attic", dry=False, clues={"dust", "box", "rope"}),
}

CLUES = {
    "note": Clue(
        id="note",
        label="a note",
        phrase="a folded note",
        repeated_line="Meet me by the lamp",
        hidden_truth="the copier had jammed and printed the same line twice",
        tag="paper",
    ),
    "ink": Clue(
        id="ink",
        label="an ink mark",
        phrase="a dark ink mark",
        repeated_line="The same drop, again",
        hidden_truth="the ink bottle tipped and left the same shape in two spots",
        tag="ink",
    ),
    "shoe": Clue(
        id="shoe",
        label="a shoe print",
        phrase="a muddy shoe print",
        repeated_line="Left, left, left",
        hidden_truth="someone had walked in circles near the door",
        tag="shoe",
    ),
}

TOOLS = {
    "lamp": Tool(
        id="lamp",
        label="a small lamp",
        phrase="A small lamp",
        method="the lamp dried the page",
        effect="it showed the hidden repeat clearly",
    ),
    "cloth": Tool(
        id="cloth",
        label="a clean cloth",
        phrase="A clean cloth",
        method="the cloth wiped away the extra smear",
        effect="it cleared the surface without ruining the clue",
    ),
    "ruler": Tool(
        id="ruler",
        label="a ruler",
        phrase="A ruler",
        method="the ruler lined up the marks",
        effect="it made the repeated part easy to compare",
    ),
}

SUSPECTS = {
    "janitor": Suspect(
        id="janitor",
        label="the janitor",
        phrase="the janitor",
        alibi="was mopping the far room",
        tell="the bucket by the door looked freshly moved",
    ),
    "neighbor": Suspect(
        id="neighbor",
        label="the neighbor",
        phrase="the neighbor",
        alibi="was reading on the porch",
        tell="the footprints stopped before the window",
    ),
    "cook": Suspect(
        id="cook",
        label="the cook",
        phrase="the cook",
        alibi="was in the kitchen",
        tell="the flour on their sleeve was too neat to be a clue",
    ),
}


@dataclass
class StoryParams:
    place: str
    clue: str
    tool: str
    suspect: str
    name: str
    seed: Optional[int] = None


VALID_COMBOS = [
    ("study", "note", "lamp", "janitor"),
    ("study", "ink", "ruler", "neighbor"),
    ("hall", "note", "cloth", "neighbor"),
    ("hall", "shoe", "ruler", "janitor"),
    ("attic", "shoe", "lamp", "cook"),
    ("attic", "ink", "cloth", "cook"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit storyworld with dry clues and repetition.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--name")
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
    combos = [c for c in VALID_COMBOS
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.tool is None or c[2] == args.tool)
              and (args.suspect is None or c[3] == args.suspect)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, tool, suspect = rng.choice(combos)
    name = args.name or rng.choice(["Mina", "Noah", "Ivy", "Theo", "Nia"])
    return StoryParams(place=place, clue=clue, tool=tool, suspect=suspect, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CLUES[params.clue], TOOLS[params.tool], SUSPECTS[params.suspect], params.name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    clue: Clue = world.facts["clue"]  # type: ignore[assignment]
    return [
        f'Write a short whodunit for a young child about a dry room and a clue that repeats "{clue.repeated_line}".',
        f"Tell a mystery story where a child named {world.facts['child'].label} tries to eliminate repetition and find the truth.",
        f"Write a gentle detective story using the words dry and eliminate, with one clue that appears more than once.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    clue: Clue = world.facts["clue"]  # type: ignore[assignment]
    tool: Tool = world.facts["tool"]  # type: ignore[assignment]
    suspect: Suspect = world.facts["suspect"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What did {child.label} want to eliminate in the story?",
            answer="The child wanted to eliminate the repetition in the clue so the real answer could be seen clearly.",
        ),
        QAItem(
            question=f"Why did the clue seem suspicious in {world.setting.place}?",
            answer=f"It seemed suspicious because {clue.phrase} kept appearing again and again, which made the pattern hard to ignore.",
        ),
        QAItem(
            question=f"How did {tool.label} help solve the mystery?",
            answer=f"{tool.phrase} helped by using {tool.method.lower()}, so the repeated clue could be checked in a dry place.",
        ),
        QAItem(
            question=f"Who was not the culprit?",
            answer=f"It was not {suspect.label}; the repeated clue was explained by {clue.hidden_truth}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="The repetition was eliminated, the clue became clear, and the room felt calm and dry again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is repetition?",
            answer="Repetition means something happens or appears again and again.",
        ),
        QAItem(
            question="Why is a dry room useful for looking at clues?",
            answer="A dry room helps because water or dampness can blur marks, while dryness makes details easier to see.",
        ),
        QAItem(
            question="What does it mean to eliminate something?",
            answer="To eliminate something means to remove it or get rid of it.",
        ),
    ]
    if world.facts.get("clue"):
        out.append(QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that can help solve a mystery.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


ASP_RULES = r"""
clue_repeated(C) :- clue(C), repeated(C).
dry_place(P) :- place(P), dry(P).
can_eliminate_repetition(P, C) :- dry_place(P), clue_repeated(C), place_has(P, C).
solved(P, C) :- can_eliminate_repetition(P, C).
#show can_eliminate_repetition/2.
#show solved/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if s.dry:
            lines.append(asp.fact("dry", pid))
        for c in sorted(s.clues):
            lines.append(asp.fact("place_has", pid, c))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("repeated", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show can_eliminate_repetition/2."))
    asp_pairs = set(asp.atoms(model, "can_eliminate_repetition"))
    py_pairs = {
        (place, clue)
        for place, setting in SETTINGS.items()
        for clue in CLUES
        if setting.dry and clue in setting.clues
    }
    if asp_pairs == py_pairs:
        print(f"OK: clingo gate matches Python reasoner ({len(py_pairs)} pairs).")
        return 0
    print("MISMATCH between clingo and Python reasoner")
    print("  only in clingo:", sorted(asp_pairs - py_pairs))
    print("  only in python:", sorted(py_pairs - asp_pairs))
    return 1


def valid_combos() -> list[tuple[str, str]]:
    return [(p, c) for p, c, t, s in VALID_COMBOS]


def resolve_check(args: argparse.Namespace) -> None:
    if args.place and args.clue and args.place == "attic" and args.clue == "note":
        raise StoryError("The attic is too damp for that note mystery; choose a matching clue.")
    if args.place and args.clue and (args.place, args.clue) not in {(p, c) for p, c, _, _ in VALID_COMBOS}:
        raise StoryError("(No valid combination matches the given options.)")


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("study", "note", "lamp", "janitor", "Mina"),
    StoryParams("hall", "shoe", "ruler", "janitor", "Noah"),
    StoryParams("attic", "ink", "cloth", "cook", "Ivy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import storyworlds.asp as asp
        except Exception as exc:
            raise SystemExit(f"ASP unavailable: {exc}")
        model = asp.one_model(asp_program("#show can_eliminate_repetition/2."))
        print(sorted(set(asp.atoms(model, "can_eliminate_repetition"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.place} / {p.clue} / {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    resolve_check(args)
    combos = [c for c in VALID_COMBOS
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.tool is None or c[2] == args.tool)
              and (args.suspect is None or c[3] == args.suspect)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, tool, suspect = rng.choice(combos)
    name = args.name or rng.choice(["Mina", "Noah", "Ivy", "Theo", "Nia"])
    return StoryParams(place=place, clue=clue, tool=tool, suspect=suspect, name=name)


if __name__ == "__main__":
    main()
