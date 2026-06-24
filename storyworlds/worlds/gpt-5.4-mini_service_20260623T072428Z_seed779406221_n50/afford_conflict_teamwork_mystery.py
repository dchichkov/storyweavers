#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T072428Z_seed779406221_n50/afford_conflict_teamwork_mystery.py
===============================================================================================================

A standalone story world for a small Mystery-style domain built from the seed
idea: something is missing, a conflict grows, and teamwork reveals what the
setting can afford.

Premise:
- A child and a helper search a small setting for a missing object.
- The setting affords only a few actions or hiding places.
- Conflict appears when they disagree about the clue.
- Teamwork resolves the tension by combining different abilities.
- The ending proves what changed in the world, not just in the narration.

This script follows the storyworld contract:
- stdlib only in the prose path
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- support for default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, --show-asp
"""

from __future__ import annotations

import argparse
import copy
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
    carried_by: Optional[str] = None
    hidden_in: str = ""
    openable: bool = False
    searchable: bool = False
    affordances: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"seen": 0.0, "moved": 0.0}
        if not self.memes:
            self.memes = {"conflict": 0.0, "teamwork": 0.0, "curiosity": 0.0}

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


@dataclass
class Setting:
    id: str
    place: str
    places: set[str] = field(default_factory=set)
    affords: set[str] = field(default_factory=set)
    hiding_spots: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    hiding_spot: str
    needed_tool: str
    conflict_reason: str
    reveal_reason: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    can_search: bool = False
    can_reach: bool = False
    can_open: bool = False
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    place: str
    clue: str
    tool: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    helper_role: str
    seed: Optional[int] = None


SETTINGS = {
    "library": Setting(
        id="library",
        place="the little library",
        places={"library"},
        affords={"search", "open", "whisper"},
        hiding_spots={"shelf", "drawer", "bookcase"},
    ),
    "attic": Setting(
        id="attic",
        place="the dusty attic",
        places={"attic"},
        affords={"search", "lift", "open"},
        hiding_spots={"box", "trunk", "blanket"},
    ),
    "garden": Setting(
        id="garden",
        place="the quiet garden",
        places={"garden"},
        affords={"search", "dig", "look"},
        hiding_spots={"pot", "bush", "stone"},
    ),
}

CLUES = {
    "key": Clue(
        id="key",
        label="small key",
        phrase="a small brass key",
        hiding_spot="drawer",
        needed_tool="search",
        conflict_reason="one child thinks the key is in the bookcase while the other thinks it is in a drawer",
        reveal_reason="the helper spots a shine in the drawer crack",
        tags={"key", "metal", "search"},
    ),
    "note": Clue(
        id="note",
        label="folded note",
        phrase="a folded note with a tiny map",
        hiding_spot="bookcase",
        needed_tool="open",
        conflict_reason="one child wants to leave the shelf alone, but the helper knows the note is tucked behind a book",
        reveal_reason="the helper opens the right book and finds the note",
        tags={"note", "paper", "open"},
    ),
    "shell": Clue(
        id="shell",
        label="sea shell",
        phrase="a smooth sea shell",
        hiding_spot="box",
        needed_tool="lift",
        conflict_reason="one child looks under the blanket while the other insists the shell must be in the trunk",
        reveal_reason="they lift the blanket together and find the shell in the box",
        tags={"shell", "lift", "search"},
    ),
}

TOOLS = {
    "magnifier": Tool(
        id="magnifier",
        label="magnifying glass",
        phrase="a magnifying glass",
        can_search=True,
        can_reach=True,
        tags={"search", "look"},
    ),
    "ladder": Tool(
        id="ladder",
        label="little ladder",
        phrase="a little ladder",
        can_reach=True,
        can_open=True,
        tags={"lift", "open"},
    ),
    "gloves": Tool(
        id="gloves",
        label="garden gloves",
        phrase="garden gloves",
        can_search=True,
        can_reach=True,
        tags={"dig", "search"},
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Ava", "Nora", "Ivy", "Zoe", "Ella", "Maya"]
BOY_NAMES = ["Leo", "Ben", "Theo", "Max", "Noah", "Finn", "Eli", "Jack"]
HELPER_ROLES = ["friend", "sibling", "neighbor"]
TRAITS = ["curious", "careful", "patient", "brave", "quiet"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for clue_id, clue in CLUES.items():
            if clue.needed_tool not in setting.affords:
                continue
            for tool_id, tool in TOOLS.items():
                if clue.needed_tool in tool.tags:
                    combos.append((place, clue_id, tool_id))
    return combos


def clue_at_risk(setting: Setting, clue: Clue) -> bool:
    return clue.needed_tool in setting.affords


def tool_helps(clue: Clue, tool: Tool) -> bool:
    return clue.needed_tool in tool.tags


def choose_tool(clue: Clue) -> Tool:
    for tool in TOOLS.values():
        if tool_helps(clue, tool):
            return tool
    raise StoryError("No tool can reasonably help with that clue.")


def choose_tool_for_setting(setting: Setting, clue: Clue) -> Optional[Tool]:
    if not clue_at_risk(setting, clue):
        return None
    for tool in TOOLS.values():
        if tool_helps(clue, tool):
            return tool
    return None


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
        for h in sorted(setting.hiding_spots):
            lines.append(asp.fact("hiding_spot", sid, h))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("needed_tool", cid, clue.needed_tool))
        lines.append(asp.fact("hiding_spot_of", cid, clue.hiding_spot))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for tag in sorted(tool.tags):
            lines.append(asp.fact("tool_tag", tid, tag))
    return "\n".join(lines)


ASP_RULES = r"""
helpful(T, C) :- tool(T), clue(C), needed_tool(C, N), tool_tag(T, N).
valid(P, C, T) :- setting(P), clue(C), tool(T), affords(P, N), needed_tool(C, N), helpful(T, C).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


@dataclass
class Rule:
    name: str

    def apply(self, world: World) -> list[str]:
        out: list[str] = []
        hero = world.get("hero")
        helper = world.get("helper")
        clue = world.get("clue")
        tool = world.get("tool")

        if hero.memes["conflict"] >= THRESHOLD and helper.memes["teamwork"] >= THRESHOLD:
            sig = ("reveal", clue.id)
            if sig not in world.fired:
                world.fired.add(sig)
                clue.meters["seen"] = 1.0
                helper.meters["moved"] += 1
                out.append("__reveal__")
        return out


CAUSAL_RULES = [Rule("reveal")]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(setting: Setting, clue: Clue, tool: Tool, hero_name: str, hero_gender: str,
         helper_name: str, helper_gender: str, helper_role: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name))
    clue_ent = world.add(Entity(id="clue", type="clue", label=clue.label, phrase=clue.phrase,
                                hidden_in=clue.hiding_spot))
    tool_ent = world.add(Entity(id="tool", type="tool", label=tool.label, phrase=tool.phrase))
    world.facts["helper_role"] = helper_role

    hero.memes["curiosity"] += 1
    helper.memes["curiosity"] += 1

    world.say(f"{hero_name} and {helper_name} arrived at {setting.place}, where something small had gone missing.")
    world.say(f"They knew the place only afforded a few good ways to search: {', '.join(sorted(setting.affords))}.")
    world.para()
    world.say(f'{hero_name} pointed to the {clue.hiding_spot}. "{clue.conflict_reason.capitalize()}."')
    world.say(f'{helper_name} shook {helper.pronoun("subject")} head. "{helper_name} thought the better clue was hidden in another spot."')
    hero.memes["conflict"] += 1
    helper.memes["conflict"] += 1
    world.para()
    world.say(f"Then they stopped arguing and used teamwork.")
    helper.memes["teamwork"] += 1
    hero.memes["teamwork"] += 1
    if tool.can_search or tool.can_reach or tool.can_open:
        world.say(f"{helper_name} brought {tool.phrase}, and {hero_name} looked again with careful eyes.")
    propagate(world, narrate=False)
    if clue_ent.meters["seen"] >= THRESHOLD:
        world.say(f"At last, {clue.reveal_reason}.")
        world.say(f"The missing {clue.label} was found, and the little mystery felt solved.")
    world.facts.update(hero=hero, helper=helper, clue=clue_ent, tool=tool_ent, setting=setting, clue_cfg=clue)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    clue = f["clue_cfg"]
    role = f["helper_role"]
    return [
        f'Write a short mystery story for a young child about a missing {clue.label} and a helper who uses teamwork.',
        f"Tell a gentle story in which a child and a {role} argue about where to search, then solve the mystery together.",
        f'Write a simple story where the setting only affords a few places to look, and the clue is finally revealed.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    clue = f["clue_cfg"]
    setting = f["setting"]
    role = f["helper_role"]
    return [
        QAItem(
            question=f"What kind of story is this about {hero.label} and {helper.label} at {setting.place}?",
            answer=f"It is a mystery about a missing {clue.label} that gets solved when they stop arguing and work together.",
        ),
        QAItem(
            question=f"What did {hero.label} think first, and what did {helper.label} think?",
            answer=f"{hero.label} thought the clue was in the {clue.hiding_spot}, but {helper.label} disagreed. That disagreement caused the conflict in the story.",
        ),
        QAItem(
            question=f"How did {role} {helper.label} help solve the mystery?",
            answer=f"{helper.label} used teamwork, brought the right tool, and helped search again until the {clue.label} was found.",
        ),
    ]


KNOWLEDGE = {
    "search": [("What does it mean to search?", "To search means to look carefully for something that is missing or hidden.")],
    "open": [("What does open mean?", "To open something means to make it not closed so you can see or get inside.")],
    "lift": [("What does lift mean?", "To lift means to raise something up with your hands.")],
    "key": [("What is a key for?", "A key is used to unlock something like a lock, door, or box.")],
    "note": [("What is a note?", "A note is a short piece of writing.")],
    "shell": [("What is a shell?", "A shell is a hard outer covering that some sea animals live in.")],
    "teamwork": [("What is teamwork?", "Teamwork means people help each other and do a job together.")],
    "conflict": [("What is conflict?", "Conflict is a disagreement or problem between people.")],
}
KNOWLEDGE_ORDER = ["search", "open", "lift", "key", "note", "shell", "teamwork", "conflict"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["clue_cfg"].tags) | {"teamwork", "conflict"}
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
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
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("library", "key", "magnifier", "Mia", "girl", "Leo", "boy", "friend"),
    StoryParams("attic", "note", "ladder", "Noah", "boy", "Ivy", "girl", "sibling"),
    StoryParams("garden", "shell", "gloves", "Ava", "girl", "Finn", "boy", "neighbor"),
]


def explain_rejection(setting: Setting, clue: Clue) -> str:
    return (
        f"(No story: the setting {setting.place} does not really afford the search "
        f"action needed to find a {clue.label}. Pick a place that can support that clue.)"
    )


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.clue:
        setting = SETTINGS[args.place]
        clue = CLUES[args.clue]
        if not clue_at_risk(setting, clue):
            raise StoryError(explain_rejection(setting, clue))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, clue_id, tool_id = rng.choice(sorted(combos))
    clue = CLUES[clue_id]
    tool = TOOLS[tool_id]

    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    helper_role = args.helper_role or rng.choice(HELPER_ROLES)
    return StoryParams(
        place=place,
        clue=clue_id,
        tool=tool_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        helper_role=helper_role,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        CLUES[params.clue],
        TOOLS[params.tool],
        params.hero_name,
        params.hero_gender,
        params.helper_name,
        params.helper_gender,
        params.helper_role,
    )
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with conflict, teamwork, and affordances.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-role", choices=HELPER_ROLES)
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


def asp_verify() -> int:
    py = set(valid_story_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("only in ASP:", sorted(cl - py))
    print("only in Python:", sorted(py - cl))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for p, c, t in combos:
            print(f"  {p:8} {c:8} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
