#!/usr/bin/env python3
"""
A tiny nursery-rhyme story world about a tremor mystery that is solved with
insight, teamwork, and reconciliation.

The premise:
- A small place feels a mysterious tremor.
- The child hero wants to solve the mystery.
- Friends join in, share clues, and reach an insight.
- The ending resolves the worry and mends a friendship.

This script follows the Storyweavers world contract:
- standalone stdlib script
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- eager import of storyworlds.results
- lazy import of storyworlds.asp inside ASP helpers
- inline ASP_RULES twin and a Python reasonableness gate
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"dust": 0.0, "noise": 0.0, "busy": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "worry": 0.0, "insight": 0.0, "joy": 0.0, "hurt": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    cause: str
    reveal: str
    setting_hint: str
    triggers: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    helps: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_shake(world: World) -> list[str]:
    out: list[str] = []
    for m in world.facts.get("mystery_marks", []):
        if m not in world.fired:
            world.fired.add(m)
    if world.facts.get("tremor_active") and not world.facts.get("reveal_done"):
        for e in world.characters():
            if e.memes["worry"] >= THRESHOLD:
                sig = ("shake", e.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    e.memes["worry"] += 0.5
                    out.append(f"{e.id} felt a tiny shake in the floor.")
    return out


def _r_insight(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("clues_shared"):
        return out
    for e in world.characters():
        if e.memes["curiosity"] >= THRESHOLD and e.memes["worry"] >= THRESHOLD:
            sig = ("insight", e.id)
            if sig not in world.fired:
                world.fired.add(sig)
                e.memes["insight"] += 1
                out.append(f"{e.id} had a bright little insight.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    friend = world.facts.get("friend")
    if not hero or not friend:
        return out
    if hero.memes["hurt"] >= THRESHOLD and world.facts.get("revealed"):
        sig = ("reconcile", hero.id, friend.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["hurt"] = 0.0
            friend.memes["hurt"] = 0.0
            hero.memes["joy"] += 1
            friend.memes["joy"] += 1
            out.append("The two friends smiled and made up.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_shake, _r_insight, _r_reconcile):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(params: "StoryParams") -> None:
    if params.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    if params.tool not in TOOLS:
        raise StoryError("Unknown tool.")
    mystery = MYSTERIES[params.mystery]
    tool = TOOLS[params.tool]
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    setting = SETTINGS[params.setting]
    if params.mystery not in setting.affords:
        raise StoryError("That setting cannot host this mystery.")
    if not mystery.triggers.intersection(tool.helps):
        raise StoryError("That tool cannot help solve this mystery.")
    if params.friend == params.name:
        raise StoryError("The hero and friend must be different characters.")


def can_solve(mystery: Mystery, tool: Tool) -> bool:
    return bool(mystery.triggers.intersection(tool.helps))


def _start(world: World, hero: Entity, friend: Entity, mystery: Mystery) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} with a curious nose for clues, "
        f"and {friend.id} was a friend who liked to listen."
    )
    world.say(
        f"At {world.setting.place}, a tiny tremor went tip-tap-tap, "
        f"and everyone looked around in a flap."
    )
    hero.memes["curiosity"] += 1
    hero.memes["worry"] += 1
    friend.memes["worry"] += 1


def _clue(world: World, hero: Entity, friend: Entity, mystery: Mystery) -> None:
    world.para()
    world.say(
        f"They found a clue that {mystery.clue}, and that made the mystery feel less shy."
    )
    hero.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    world.facts["clues_shared"] = True


def _friction(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"But {hero.id} and {friend.id} spoke too fast, and their words came out wrong."
    )
    hero.memes["hurt"] += 1
    friend.memes["hurt"] += 1


def _tool_work(world: World, hero: Entity, friend: Entity, mystery: Mystery, tool: Tool) -> None:
    world.para()
    world.say(
        f"Then they used {tool.label}, {tool.prep} while they searched for the cause."
    )
    world.say(
        f"Together they noticed that {mystery.setting_hint}, and the answer began to glow."
    )
    hero.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    world.facts["revealed"] = True
    world.facts["reveal_text"] = mystery.reveal
    world.facts["reveal_done"] = True
    world.say(mystery.reveal)
    propagate(world, narrate=True)


def _ending(world: World, hero: Entity, friend: Entity, mystery: Mystery, tool: Tool) -> None:
    world.para()
    world.say(
        f"After that, the tremor was only the little bump of a loose latch, "
        f"and the room was calm again."
    )
    world.say(
        f"{hero.id} and {friend.id} laughed softly, {tool.tail}, and their friendship felt warm and new."
    )


SETTINGS = {
    "toyroom": Setting(place="the toyroom", indoor=True, affords={"toybox"}),
    "hall": Setting(place="the hall", indoor=True, affords={"floorboard"}),
    "garden": Setting(place="the garden path", indoor=False, affords={"stone"}),
}

MYSTERIES = {
    "toybox": Mystery(
        id="toybox",
        clue="a tiny rattle came from the striped toy chest",
        cause="a wooden block had slipped under the lid",
        reveal="Under the lid sat the block, bumping just so when the box moved.",
        setting_hint="the toy chest had one block stuck beneath its lid",
        triggers={"listen", "peek", "open"},
    ),
    "floorboard": Mystery(
        id="floorboard",
        clue="the plank by the rug squeaked like a mouse",
        cause="a pebble had wedged under the board",
        reveal="A little pebble was hiding under the plank, and that was the squeak-maker.",
        setting_hint="a pebble sat snug under the floorboard",
        triggers={"knock", "press", "listen"},
    ),
    "stone": Mystery(
        id="stone",
        clue="a round stone kept wobbling beside the path",
        cause="a worm had nudged the soil below it",
        reveal="The stone rocked because the ground beneath it was soft and busy with a worm.",
        setting_hint="the soil under the stone was soft after a warm shower",
        triggers={"dig", "brush", "peek"},
    ),
}

TOOLS = {
    "lantern": Tool(
        id="lantern",
        label="a small lantern",
        helps={"peek", "listen"},
        prep="to shine on the dark corners",
        tail="shared the glow and walked home hand in hand",
    ),
    "magnifier": Tool(
        id="magnifier",
        label="a round magnifier",
        helps={"peek", "press"},
        prep="to study each clue with care",
        tail="put the magnifier away and smiled together",
    ),
    "spoon": Tool(
        id="spoon",
        label="a silver spoon",
        helps={"knock", "listen"},
        prep="to tap gently and hear the sound",
        tail="left the spoon in the dish and giggled",
    ),
    "trowel": Tool(
        id="trowel",
        label="a little trowel",
        helps={"dig", "brush"},
        prep="to lift the soft earth with care",
        tail="set the trowel down and brushed dirt from their sleeves",
    ),
}


@dataclass
class StoryParams:
    setting: str
    mystery: str
    tool: str
    name: str
    friend: str
    seed: Optional[int] = None


NAMES = ["Mimi", "Rory", "Lina", "Toby", "Pip", "Nell", "Tara", "Otto"]
FRIENDS = ["Pip", "Nell", "Toby", "Mimi", "Rory", "Lina", "Tara", "Otto"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme mystery story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    candidates = []
    for setting_id, setting in SETTINGS.items():
        for mystery_id in setting.affords:
            mystery = MYSTERIES[mystery_id]
            for tool_id, tool in TOOLS.items():
                if can_solve(mystery, tool):
                    candidates.append((setting_id, mystery_id, tool_id))
    if args.setting:
        candidates = [c for c in candidates if c[0] == args.setting]
    if args.mystery:
        candidates = [c for c in candidates if c[1] == args.mystery]
    if args.tool:
        candidates = [c for c in candidates if c[2] == args.tool]
    if not candidates:
        raise StoryError("No valid combination matches the given options.")
    setting, mystery, tool = rng.choice(sorted(candidates))
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice([n for n in FRIENDS if n != name])
    params = StoryParams(setting=setting, mystery=mystery, tool=tool, name=name, friend=friend)
    reasonableness_gate(params)
    return params


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    mystery = MYSTERIES[params.mystery]
    tool = TOOLS[params.tool]
    hero = world.add(Entity(id=params.name, kind="character", type="child", label=params.name))
    friend = world.add(Entity(id=params.friend, kind="character", type="child", label=params.friend))
    world.facts["hero"] = hero
    world.facts["friend"] = friend
    world.facts["mystery"] = mystery
    world.facts["tool"] = tool
    world.facts["tremor_active"] = True

    _start(world, hero, friend, mystery)
    _clue(world, hero, friend, mystery)
    _friction(world, hero, friend)
    _tool_work(world, hero, friend, mystery, tool)

    world.para()
    _ending(world, hero, friend, mystery, tool)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    m: Mystery = f["mystery"]
    t: Tool = f["tool"]
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    return [
        f'Write a nursery-rhyme style story about a tiny tremor and an insight at {world.setting.place}.',
        f"Tell a gentle mystery where {hero.id} and {friend.id} use {t.label} to solve what makes the {m.id} mystery happen.",
        f'Create a short child-friendly tale with teamwork, reconciliation, and the word "insight".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    m: Mystery = f["mystery"]
    t: Tool = f["tool"]
    qa = [
        QAItem(
            question=f"What small mystery did {hero.id} and {friend.id} try to solve?",
            answer=f"They tried to solve a {m.id} mystery at {world.setting.place}, where a tiny tremor kept coming back.",
        ),
        QAItem(
            question=f"What clue helped them begin to understand the problem?",
            answer=f"The clue was that {m.clue}. That clue made the mystery feel less scary and more solvable.",
        ),
        QAItem(
            question=f"What tool did they use together?",
            answer=f"They used {t.label} together, and they shared the work instead of doing it alone.",
        ),
        QAItem(
            question=f"What did the story's insight help them realize?",
            answer=f"Their insight helped them realize that {m.cause}. Once they knew that, they could fix the trouble.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {friend.id}?",
            answer=f"They made up, laughed softly, and felt close again after solving the mystery together.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an insight?",
            answer="An insight is a quick, clear idea that helps you understand something puzzling.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and work together toward the same goal.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop being upset and make peace again.",
        ),
        QAItem(
            question="What is a tremor?",
            answer="A tremor is a small shake or quiver that can be felt in something like the floor or ground.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: meters={{{', '.join(f'{k}={v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}={v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
tremor(M) :- mystery(M), triggers(M, listen).
shared_clue :- clue_shared.
insight_ready(H) :- hero(H), shared_clue, worry(H), curiosity(H).
reconcile(H,F) :- hero(H), friend(F), revealed, hurt(H), hurt(F).
solved(M) :- mystery(M), cause_known(M).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for m in sorted(s.affords):
            lines.append(asp.fact("affords", sid, m))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        for tr in sorted(m.triggers):
            lines.append(asp.fact("triggers", mid, tr))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for h in sorted(t.helps):
            lines.append(asp.fact("helps", tid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    # simple parity: every valid combination in Python should be represented by ASP
    python_set = set()
    for sid, s in SETTINGS.items():
        for mid in s.affords:
            for tid, t in TOOLS.items():
                if can_solve(MYSTERIES[mid], t):
                    python_set.add((sid, mid, tid))
    model = asp.one_model(asp_program("#show valid/3."))
    asp_set = set(asp.atoms(model, "valid"))
    if asp_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(asp_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate.")
    print("only in asp:", sorted(asp_set - python_set))
    print("only in python:", sorted(python_set - asp_set))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    prog = asp_program("#show valid/3.")
    model = asp.one_model(prog)
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_story_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for mid in setting.affords:
            for tid, tool in TOOLS.items():
                if can_solve(MYSTERIES[mid], tool):
                    combos.append((sid, mid, tid))
    return combos


def valid_story_combos_with_names() -> list[tuple[str, str, str, str]]:
    out = []
    for sid, mid, tid in valid_story_combos():
        for name in NAMES:
            for friend in FRIENDS:
                if friend != name:
                    out.append((sid, mid, tid, name))
    return out


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
    StoryParams(setting="toyroom", mystery="toybox", tool="lantern", name="Mimi", friend="Pip"),
    StoryParams(setting="hall", mystery="floorboard", tool="spoon", name="Rory", friend="Nell"),
    StoryParams(setting="garden", mystery="stone", tool="trowel", name="Lina", friend="Toby"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible combos ({len(stories)} with names):\n")
        for sid, mid, tid in triples:
            print(f"  {sid:8} {mid:10} {tid:10}")
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
            header = f"### {p.name}: {p.mystery} at {p.setting} (tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
