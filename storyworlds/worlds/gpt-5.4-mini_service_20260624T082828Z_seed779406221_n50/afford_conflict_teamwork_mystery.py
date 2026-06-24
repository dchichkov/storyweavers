#!/usr/bin/env python3
"""
afford_conflict_teamwork_mystery.py
==================================

A small mystery storyworld about a child, a puzzling clue, a disagreement,
and a teamwork-based solution.

The premise is intentionally tiny: a child wants to solve a mystery, but the
first guess is wrong or incomplete. The world model tracks what each place and
object can afford, what clues become visible, and how conflict turns into
teamwork when the characters compare notes and follow evidence.

This world keeps the prose child-facing and concrete:
- the setting is a small place with a few usable affordances
- the mystery grows from visible state, not a frozen template
- conflict is caused by a bad assumption or a missing clue
- teamwork resolves the uncertainty and reveals the answer

The world includes:
- physical meters for clue visibility, noise, and tidiness
- emotional memes for worry, conflict, curiosity, and teamwork
- an inline ASP twin for the compatibility gate
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


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing" | "setting"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    affordances: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    indoors: bool = True
    afford: set[str] = field(default_factory=set)
    mood: str = "quiet"


@dataclass
class Mystery:
    id: str
    clue: str
    question: str
    guess: str
    answer: str
    reveal: str
    trigger: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    covers: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "library": Setting(place="the library", indoors=True, afford={"whisper", "read", "search"}, mood="quiet"),
    "kitchen": Setting(place="the kitchen", indoors=True, afford={"search", "listen", "share"}, mood="busy"),
    "attic": Setting(place="the attic", indoors=True, afford={"search", "shine", "listen"}, mood="dusty"),
    "garden_shed": Setting(place="the garden shed", indoors=True, afford={"search", "listen", "share"}, mood="creaky"),
}

MYSTERIES = {
    "missing_key": Mystery(
        id="missing_key",
        clue="a tiny brass key",
        question="Who moved the key?",
        guess="the cat took it",
        answer="the key had fallen behind a box",
        reveal="behind a box",
        trigger="search",
        tags={"key", "metal", "search"},
    ),
    "rattle": Mystery(
        id="rattle",
        clue="a soft rattle from a jar",
        question="What made the rattle?",
        guess="a mouse was inside",
        answer="two buttons were tapping together in the jar",
        reveal="inside the jar",
        trigger="listen",
        tags={"jar", "sound", "listen"},
    ),
    "lamp_glow": Mystery(
        id="lamp_glow",
        clue="a yellow glow under a blanket",
        question="Why was the blanket glowing?",
        guess="a fire was hiding there",
        answer="a toy lamp had been switched on by accident",
        reveal="under the blanket",
        trigger="shine",
        tags={"light", "blanket", "shine"},
    ),
}

TOOLS = [
    Tool(id="flashlight", label="flashlight", phrase="a small flashlight", helps={"shine", "search"}),
    Tool(id="stool", label="stool", phrase="a sturdy stool", helps={"reach", "search"}),
    Tool(id="notebook", label="notebook", phrase="a little notebook", helps={"write", "share"}),
]

NAMES = ["Maya", "Noah", "Lina", "Theo", "Ada", "Eli", "Nina", "Owen"]
TRAITS = ["curious", "careful", "bright", "brave", "patient", "quick-thinking"]
PARTNERS = ["mom", "dad", "grandma", "older brother", "older sister"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def mystery_affords(setting: Setting, mystery: Mystery) -> bool:
    return mystery.trigger in setting.afford


def compatible_tool(setting: Setting, mystery: Mystery) -> Optional[Tool]:
    for tool in TOOLS:
        if mystery.trigger in tool.helps:
            return tool
    return None


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for mid, mystery in MYSTERIES.items():
            if mystery_affords(setting, mystery) and compatible_tool(setting, mystery):
                out.append((sid, mid))
    return out


# ---------------------------------------------------------------------------
# World dynamics
# ---------------------------------------------------------------------------
def _narrate_search(world: World, child: Entity, partner: Entity, mystery: Mystery, tool: Tool) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1
    child.meters["searching"] = child.meters.get("searching", 0.0) + 1
    world.say(
        f"{child.id} wanted to solve the mystery of {mystery.clue}, "
        f"so {child.pronoun()} and {partner.label} used {tool.phrase} to look more closely."
    )


def _narrate_conflict(world: World, child: Entity, partner: Entity, mystery: Mystery) -> None:
    child.memes["conflict"] = child.memes.get("conflict", 0.0) + 1
    partner.memes["worry"] = partner.memes.get("worry", 0.0) + 1
    world.say(
        f"But {child.id} guessed {mystery.guess}, and {partner.label} did not agree."
    )
    world.say(
        f'"Maybe," said {partner.label}, "but let us not jump too fast."'
    )


def _narrate_teamwork(world: World, child: Entity, partner: Entity, mystery: Mystery, tool: Tool) -> None:
    child.memes["teamwork"] = child.memes.get("teamwork", 0.0) + 1
    partner.memes["teamwork"] = partner.memes.get("teamwork", 0.0) + 1
    child.memes["conflict"] = 0.0
    world.say(
        f"{child.id} and {partner.label} worked together: one looked, one listened, and one pointed the light."
    )
    world.say(
        f"Then they found the clue {mystery.reveal}, and the answer was that {mystery.answer}."
    )


def tell(setting: Setting, mystery: Mystery, hero_name: str, hero_type: str, partner_name: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    partner = world.add(Entity(id=partner_name, kind="character", type="adult", label=partner_name))
    clue = world.add(Entity(id="clue", type="thing", label=mystery.clue, phrase=mystery.clue))
    tool = compatible_tool(setting, mystery)
    if tool is None:
        raise StoryError("No compatible tool exists for this mystery.")

    tool_ent = world.add(Entity(id=tool.id, type="tool", label=tool.label, phrase=tool.phrase, plural=False))

    world.say(
        f"{child.id} was a {random.choice(TRAITS)} little {hero_type} who loved clues."
    )
    world.say(
        f"On a quiet day in {setting.place}, {child.id} noticed {clue.label} and felt a question wake up inside."
    )

    world.para()
    _narrate_search(world, child, partner, mystery, tool_ent)
    _narrate_conflict(world, child, partner, mystery)

    world.para()
    _narrate_teamwork(world, child, partner, mystery, tool_ent)

    world.say(
        f"At the end, {child.id} smiled because the mystery made sense at last, and the room felt calm again."
    )

    world.facts.update(
        child=child,
        partner=partner,
        mystery=mystery,
        clue=clue,
        tool=tool_ent,
        setting=setting,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    partner: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with conflict and teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--partner", choices=PARTNERS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.mystery:
        setting = SETTINGS[args.place]
        mystery = MYSTERIES[args.mystery]
        if not mystery_affords(setting, mystery) or not compatible_tool(setting, mystery):
            raise StoryError(f"(No story: {setting.place} does not reasonably afford that mystery.)")
    combos = [
        (p, m) for p, m in valid_combos()
        if (args.place is None or p == args.place)
        and (args.mystery is None or m == args.mystery)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    partner = args.partner or rng.choice(PARTNERS)
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, partner=partner)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a young child set in {f["setting"].place} that uses the word "{f["mystery"].clue}".',
        f"Tell a story where {f['child'].id} and {f['partner'].label} disagree at first, then work together to solve a small mystery.",
        f"Write a gentle detective story with a clue, a wrong guess, and a teamwork ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    partner = f["partner"]
    mystery = f["mystery"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who was trying to solve the mystery in {setting.place}?",
            answer=f"{child.id} was trying to solve the mystery in {setting.place} with {partner.label}.",
        ),
        QAItem(
            question=f"What was the clue that made {child.id} curious?",
            answer=f"The clue was {mystery.clue}. It made the room feel puzzling and important.",
        ),
        QAItem(
            question=f"Why did {child.id} and {partner.label} argue a little at first?",
            answer=f"{child.id} guessed {mystery.guess}, but {partner.label} thought they should look again before deciding.",
        ),
        QAItem(
            question="How did they solve the mystery?",
            answer=f"They used teamwork, looked carefully, and found that {mystery.answer}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps someone solve a mystery.",
        ),
        QAItem(
            question="Why is teamwork helpful?",
            answer="Teamwork is helpful because two people can notice different things and solve a problem together.",
        ),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
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
        if e.affordances:
            bits.append(f"affords={sorted(e.affordances)}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    mystery = MYSTERIES[params.mystery]
    world = tell(setting, mystery, params.name, params.gender, params.partner)
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(P) :- place(P).
mystery(M) :- clue_of(M, _).

affords(P, T) :- setting(P), place_afford(P, T).
triggered(M, T) :- clue_of(M, _), trigger_of(M, T).

compatible(P, M) :- affords(P, T), triggered(M, T), tool_helps(T).
valid(P, M) :- compatible(P, M).

#show valid/2.
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("place", sid))
        for a in sorted(s.afford):
            lines.append(asp.fact("place_afford", sid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("clue_of", mid, m.clue))
        lines.append(asp.fact("trigger_of", mid, m.trigger))
    for tool in TOOLS:
        lines.append(asp.fact("tool_helps", tool.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="library", mystery="missing_key", name="Maya", gender="girl", partner="mom"),
    StoryParams(place="kitchen", mystery="rattle", name="Noah", gender="boy", partner="dad"),
    StoryParams(place="attic", mystery="lamp_glow", name="Ada", gender="girl", partner="grandma"),
]


def resolve_all_samples() -> list[StoryParams]:
    return CURATED


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible place/mystery combos:\n")
        for t in triples:
            print(f"  {t[0]:12} {t[1]}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in resolve_all_samples()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
