#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/dance_vague_extraction_happy_ending_flashback_pirate.py
======================================================================================

A tiny pirate tale world about a child crew, a missing dance clue, a vague memory
from a flashback, and a happy ending after they extract a hidden token from a
locked chest.

This world keeps the classic Storyweavers shape: typed entities with physical
meters and emotional memes, a forward-causal model, a reasonableness gate, an
inline ASP twin, and child-facing QA grounded in simulated world state.

Seed instruments:
- words: dance, vague, extraction
- features: Happy Ending, Flashback
- style: Pirate Tale
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class PirateTheme:
    id: str
    ship: str
    place: str
    crew_name: str
    goal: str
    flashback_place: str
    ending_image: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Hint:
    id: str
    label: str
    vague_phrase: str
    extracted: str
    where: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Tool:
    id: str
    label: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_tension(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes["worry"] < THRESHOLD:
            continue
        sig = ("tension", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["care"] += 1
        out.append("")
    return out


CAUSAL_RULES = [Rule("tension", "social", _r_tension)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sensical_tools() -> list[Tool]:
    return [t for t in TOOLS.values() if t.sense >= SENSE_MIN]


def hazard_ok(hint: Hint, target: str) -> bool:
    return bool(target) and bool(hint.label)


def extractable(tool: Tool, hint: Hint) -> bool:
    return tool.power >= 2 and hint.id in {"vague_note", "shell_song"}


def calm_prediction(world: World, hint: Hint) -> dict:
    sim = world.copy()
    _use_tool(sim, sim.get("tool"), sim.get("hint"), narrate=False)
    return {"found": sim.facts.get("found", False), "joy": sim.get("child").memes["joy"]}


def _use_tool(world: World, tool: Entity, hint: Entity, narrate: bool = True) -> None:
    hint.meters["found"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, child: Entity, friend: Entity, theme: PirateTheme) -> None:
    child.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"On a breezy afternoon, {child.id} and {friend.id} turned the deck into "
        f"a pirate stage. {theme.ship} rocked gently, and the lantern light shone "
        f"over the boards."
    )
    world.say(
        f'They wanted a dance for their crew, because {theme.crew_name} always '
        f'liked to end a hunt with a happy dance.'
    )


def flashback(world: World, child: Entity, theme: PirateTheme, hint: Hint) -> None:
    child.memes["remember"] += 1
    world.say(
        f"Then {child.id} stopped. A vague little memory tugged at {child.pronoun('possessive')} ear."
    )
    world.say(
        f"In a flashback, {child.id} had seen the clue hidden near {theme.flashback_place}, "
        f"wrapped in seaweed and tucked under a loose plank."
    )
    world.say(
        f'{child.id} whispered, "I remember something vague -- the clue was there."'
    )


def search(world: World, friend: Entity, hint: Hint) -> None:
    friend.memes["worry"] += 1
    world.say(
        f'{friend.id} peered around the deck. "That is still too vague," {friend.pronoun()} said. '
        f'"We need a proper extraction, not just a guess."'
    )


def extract(world: World, child: Entity, friend: Entity, hint: Hint, tool: Tool) -> None:
    child.memes["bravery"] += 1
    hint.meters["extracted"] += 1
    child.meters["dance"] += 1
    world.say(
        f"{child.id} smiled and used {tool.label} to pull the tiny clue out of its hiding place. "
        f"That careful extraction made the answer clear at last."
    )


def celebrate(world: World, child: Entity, friend: Entity, theme: PirateTheme, hint: Hint) -> None:
    child.memes["joy"] += 2
    friend.memes["joy"] += 2
    world.say(
        f"At once, the clue pointed to {theme.goal}, and the crew burst into a joyful dance."
    )
    world.say(
        f"They spun across the deck while the sea breeze rattled the ropes, and "
        f"{theme.ending_image}."
    )
    world.say(
        f"Their pirate day ended with laughter, bright feet, and a happy map in hand."
    )


def tell(theme: PirateTheme, hint_cfg: Hint, tool: Tool,
         child_name: str = "Maya", child_gender: str = "girl",
         friend_name: str = "Finn", friend_gender: str = "boy") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="seeker"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="mate"))
    captain = world.add(Entity(id="captain", kind="character", type="mother", role="captain", label="the captain"))
    hint = world.add(Entity(id="hint", type="hint", label=hint_cfg.label))
    tool_ent = world.add(Entity(id="tool", type="tool", label=tool.label))
    child.memes["worry"] = 1.0
    world.facts["theme"] = theme
    world.facts["hint_cfg"] = hint_cfg
    world.facts["tool"] = tool_ent

    setup(world, child, friend, theme)
    world.para()
    flashback(world, child, theme, hint_cfg)
    search(world, friend, hint_cfg)
    if extractable(tool, hint_cfg):
        extract(world, child, friend, hint_cfg, tool)
        celebrate(world, child, friend, theme, hint_cfg)
        outcome = "happy"
    else:
        world.say("But the clue stayed hidden, and the crew could not finish the dance.")
        outcome = "sad"

    world.facts.update(child=child, friend=friend, captain=captain, hint=hint, outcome=outcome, tool=tool)
    return world


THEMES = {
    "deck": PirateTheme(
        "deck",
        "their little ship",
        "the deck",
        "the dancing crew",
        "the treasure cove",
        "the old map chest by the mast",
        "the lantern glow and the new dance steps",
    ),
    "island": PirateTheme(
        "island",
        "their toy ship",
        "the sandy cove",
        "the dancing crew",
        "the shell cave",
        "the palm tree with the blue ribbon",
        "the driftwood drum and the new dance steps",
    ),
}

HINTS = {
    "vague_note": Hint("vague_note", "a vague note", "somewhere nearby", "a small brass key", "under the loose plank", {"vague"}),
    "shell_song": Hint("shell_song", "a shell song", "near the mast", "a tiny silver coin", "behind the old barrel", {"extraction"}),
}

TOOLS = {
    "hook": Tool("hook", "a small hook", 3, 3,
                 "hooked the little clue free with a careful tug",
                 "pulled too hard, and the clue slipped back out of reach",
                 "hooked the clue free",
                 {"extraction"}),
    "brush": Tool("brush", "a soft brush", 2, 2,
                  "brushed away the sand until the clue showed itself",
                  "brushed the wrong place and found nothing",
                  "brushed away the sand and found the clue",
                  {"extraction"}),
}

GIRL_NAMES = ["Maya", "Lina", "Nora", "Ava", "Zoe", "Lily"]
BOY_NAMES = ["Finn", "Theo", "Eli", "Noah", "Ben", "Max"]


@dataclass
@dataclass
class StoryParams:
    theme: str
    hint: str
    tool: str
    child: str
    child_gender: str
    friend: str
    friend_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for tid in THEMES:
        for hid, hint in HINTS.items():
            for tid2, tool in TOOLS.items():
                if hazard_ok(hint, tool.label) and extractable(tool, hint):
                    combos.append((tid, hid, tid2))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a pirate story for a young child that includes the words "dance", "vague", and "extraction".',
        f"Tell a happy pirate tale where {f['child'].id} remembers a vague clue in a flashback and helps the crew finish the dance.",
        f'Write a story with a flashback, a careful extraction, and a joyful dance on {f["theme"].place}.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, friend, theme, hint_cfg = f["child"], f["friend"], f["theme"], f["hint_cfg"]
    return [
        ("Who is the story about?",
         f"It is about {child.id} and {friend.id}, two little pirates on a happy crew. They are the ones who turn the deck into a dancing place."),
        ("What did the child remember in the flashback?",
         f"{child.id} remembered a vague clue near {theme.flashback_place}. The flashback helped them know where to look instead of guessing."),
        ("How did they get the clue out?",
         f"{child.id} used {f['tool'].label} for a careful extraction. That made the hidden clue come free at last."),
        ("How did the story end?",
         f"It ended happily, with a dance on {theme.place} and the crew smiling. The clue was found, so their pirate game could finish with joy."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a flashback?",
         "A flashback is a moment in a story that shows something from before. It helps the character remember an earlier event."),
        ("What does vague mean?",
         "Vague means not very clear or exact. A vague clue can still help, but you may need to look carefully."),
        ("What is extraction?",
         "Extraction means taking something out carefully. People can extract a clue from a hiding place without breaking it."),
        ("Why do pirates dance in stories?",
         "Pirates dance in stories because they are celebrating treasure, teamwork, or a good surprise. The dance shows that the crew is happy."),
    ]


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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("deck", "vague_note", "hook", "Maya", "girl", "Finn", "boy"),
    StoryParams("island", "shell_song", "brush", "Lina", "girl", "Theo", "boy"),
]


def explain_rejection(hint: Hint, tool: Tool) -> str:
    return f"(No story: the clue/tool pair is not reasonable enough for a pirate extraction tale.)"


def explain_tool(rid: str) -> str:
    r = TOOLS[rid]
    better = " / ".join(sorted(x.id for x in sensical_tools()))
    return f"(Refusing tool '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}). Try: {better}.)"


ASP_RULES = r"""
valid(T, H, U) :- theme(T), hint(H), tool(U), extractable(H, U).
happy :- chosen_hint(H), chosen_tool(U), extractable(H, U).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for hid in HINTS:
        lines.append(asp.fact("hint", hid))
    for uid, t in TOOLS.items():
        lines.append(asp.fact("tool", uid))
        lines.append(asp.fact("sense", uid, t.sense))
        lines.append(asp.fact("power", uid, t.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: gate matches valid_combos().")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(CURATED[0])
        assert sample.story.strip()
        print("OK: smoke test story generated.")
    except Exception as err:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate dance flashback extraction storyworld.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--hint", choices=HINTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        raise StoryError(explain_tool(args.tool))
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.hint is None or c[1] == args.hint)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, hint, tool = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if child_gender == "girl" else "girl")
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != child])
    return StoryParams(theme, hint, tool, child, child_gender, friend, friend_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(THEMES[params.theme], HINTS[params.hint], TOOLS[params.tool],
                 params.child, params.child_gender, params.friend, params.friend_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for t, h, u in combos:
            print(f"  {t:8} {h:12} {u}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
