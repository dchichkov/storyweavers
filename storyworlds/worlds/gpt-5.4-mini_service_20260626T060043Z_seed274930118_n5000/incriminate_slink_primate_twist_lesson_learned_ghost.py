#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/incriminate_slink_primate_twist_lesson_learned_ghost.py
===============================================================================================================================

A small ghost-story world with a twist: a child hears spooky bumps in an old house,
a ghost seems to be the cause, and a sneaky primate is the real culprit.

Story seed imagined from the prompt:
- A child is scared by eerie sounds in a dim house.
- The child spots a ghost, but the ghost turns out to be harmless.
- A primate has been slinking around, making the noise and causing the problem.
- The story turns on a Twist and ends with a Lesson Learned: do not incriminate the wrong creature before looking closely.

The world is intentionally narrow and constraint-checked:
- A story is only generated if the chosen setting can plausibly host the haunting.
- The twist is only valid if the primate's actions can explain the spooky event.
- The lesson is only valid if the story resolves from fear to understanding.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    moved_by: Optional[str] = None
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters.setdefault("mood", 0.0)
        self.meters.setdefault("noise", 0.0)
        self.meters.setdefault("mischief", 0.0)
        self.meters.setdefault("evidence", 0.0)
        self.meters.setdefault("dust", 0.0)
        self.memes.setdefault("fear", 0.0)
        self.memes.setdefault("curiosity", 0.0)
        self.memes.setdefault("relief", 0.0)
        self.memes.setdefault("trust", 0.0)
        self.memes.setdefault("guilt", 0.0)

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
    shadowy: bool
    affords_ghost: bool = True


@dataclass
class StoryParams:
    setting: str
    name: str
    gender: str
    guardian: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_spook(world: World) -> list[str]:
    out: list[str] = []
    child = world.get(world.facts["child"])
    ghost = world.get("ghost")
    if child.memes["fear"] < THRESHOLD or ghost.hidden:
        return out
    sig = ("spook",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["curiosity"] += 1
    out.append("The room felt spooky, but the light kept glowing near the curtains.")
    return out


def _r_twist(world: World) -> list[str]:
    child = world.get(world.facts["child"])
    primate = world.get("primate")
    if primate.meters["evidence"] < THRESHOLD or primate.hidden:
        return []
    sig = ("twist",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] = max(0.0, child.memes["fear"] - 1.0)
    child.memes["trust"] += 1
    primate.memes["guilt"] += 1
    return ["__twist__"]


def _r_lesson(world: World) -> list[str]:
    child = world.get(world.facts["child"])
    ghost = world.get("ghost")
    primate = world.get("primate")
    if child.memes["trust"] < THRESHOLD or primate.memes["guilt"] < THRESHOLD:
        return []
    sig = ("lesson",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ghost.memes["relief"] += 1
    child.memes["relief"] += 1
    return ["__lesson__"]


RULES = [_r_spook, _r_twist, _r_lesson]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            bits = rule(world)
            if bits:
                changed = True
                produced.extend(x for x in bits if x not in {"__twist__", "__lesson__"})
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "old_house": Setting(place="the old house", shadowy=True, affords_ghost=True),
    "attic": Setting(place="the attic", shadowy=True, affords_ghost=True),
    "porch": Setting(place="the porch", shadowy=False, affords_ghost=False),
}

NAMES = {
    "girl": ["Mia", "Lena", "Nora", "Ivy", "Zoe"],
    "boy": ["Finn", "Eli", "Theo", "Noah", "Ben"],
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id, s in SETTINGS.items():
        if not s.affords_ghost:
            continue
        for gender in ("girl", "boy"):
            for name in NAMES[gender]:
                combos.append((setting_id, gender, name))
    return combos


def explain_rejection(setting: Setting) -> str:
    return (
        f"(No story: {setting.place} is not shadowy enough for a believable ghostly "
        f"mistake, so the primate would not plausibly be incriminated there.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Ghost-story world with a primate twist and a lesson learned."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--guardian", choices=["mother", "father"])
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
    combos = valid_combos()
    if args.setting and not SETTINGS[args.setting].affords_ghost:
        raise StoryError(explain_rejection(SETTINGS[args.setting]))
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.gender:
        combos = [c for c in combos if c[1] == args.gender]
    if not combos:
        raise StoryError("(No valid ghost-story combination matches the given options.)")
    setting, gender, name = rng.choice(sorted(combos))
    if args.name:
        name = args.name
    guardian = args.guardian or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, name=name, gender=gender, guardian=guardian)


def tell(setting: Setting, name: str, gender: str, guardian: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender, traits=["little", "brave"]))
    guard = world.add(Entity(id="guardian", kind="character", type=guardian, label=f"the {guardian}"))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label="the ghost"))
    primate = world.add(Entity(id="primate", kind="character", type="primate", label="a small primate"))

    child.memes["fear"] += 1
    ghost.hidden = False
    primate.hidden = True

    world.facts.update(child=child.id, guardian=guard.id, ghost=ghost.id, primate=primate.id)

    world.say(
        f"{child.id} was a little {gender} who stayed close to {guard.label} whenever the house went quiet."
    )
    world.say(
        f"At {setting.place}, {child.id} heard a bump-bump in the dark and saw a pale shape by the window."
    )
    world.say(
        f'"It is a ghost," {child.id} whispered, and {child.pronoun("possessive")} heart thumped fast.'
    )

    world.para()
    child.memes["fear"] += 1
    child.memes["curiosity"] += 1
    ghost.memes["trust"] += 1
    world.say(
        f"{guard.label} lifted a lamp, and the room glowed gold. The ghost did not lunge or roar."
    )
    world.say(
        f"Instead, the ghost pointed toward the curtain, where something tiny had been trying to slink away."
    )

    primate.hidden = False
    primate.meters["noise"] += 1
    primate.meters["mischief"] += 1
    primate.meters["evidence"] += 1
    primate.meters["dust"] += 1

    world.say(
        f"It was a primate, and it had been trying to slink past the shelves with a stolen cookie tin."
    )
    world.say(
        f"The muddy prints and the wobbling tin would incriminate the primate, not the ghost."
    )

    propagate(world, narrate=False)

    world.para()
    world.say(
        f"Twist: the spooky bump had only been the primate bumping the tin against the steps."
    )
    world.say(
        f"{child.id} blinked, then laughed softly when the ghost bowed its head and the primate looked ashamed."
    )
    world.say(
        f"Lesson Learned: it is wise to look closely before blaming a shadow, because a quiet ghost is not always the trouble."
    )
    world.say(
        f"By the end, {child.id} was calm, {ghost.label} was understood, and the primate was helping put the cookie tin back."
    )

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        f"Write a short ghost story for young children where {child} hears spooky sounds in a shadowy house and learns not to blame the wrong creature.",
        "Tell a gentle story with a Twist and a Lesson Learned, where a ghost seems scary at first but a primate is the real cause.",
        "Write a child-friendly spooky tale that includes the words incriminate, slink, and primate.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    qa = [
        QAItem(
            question=f"Why did {child} think the house was scary at first?",
            answer=f"{child} thought the house was scary because it was quiet, dark, and the child heard strange bumps near the window.",
        ),
        QAItem(
            question="Who did the child blame before the twist?",
            answer="The child first blamed the ghost, because the pale shape in the dark looked spooky.",
        ),
        QAItem(
            question="What made the twist happen?",
            answer="The twist happened when the lamp shone on the curtain and revealed that a small primate had been making the noise and trying to slink away.",
        ),
        QAItem(
            question="What lesson was learned at the end?",
            answer="The lesson was to look closely before accusing someone, because a shadow or a spooky sound can make the wrong creature seem guilty.",
        ),
    ]
    if world.facts.get("resolved"):
        qa.append(
            QAItem(
                question="How did the story end?",
                answer="It ended with the child calm, the ghost understood, and the primate helping put the cookie tin back where it belonged.",
            )
        )
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a ghost story usually try to do?",
            answer="A ghost story usually tries to make ordinary places feel spooky for a moment, while still staying safe and interesting.",
        ),
        QAItem(
            question="What does it mean to slink?",
            answer="To slink means to move quietly and carefully, often as if you do not want anyone to notice you.",
        ),
        QAItem(
            question="What does it mean to incriminate someone?",
            answer="To incriminate someone means to make them seem responsible for a wrong action or a problem.",
        ),
        QAItem(
            question="What is a primate?",
            answer="A primate is an animal group that includes monkeys, apes, and humans.",
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(old_house).
setting(attic).
setting(porch).

shadowy(old_house).
shadowy(attic).

affords_ghost(old_house).
affords_ghost(attic).

valid_story(S,G,N) :- setting(S), shadowy(S), affords_ghost(S), gender(G), name_for(G,N).
"""

ASP_FALLBACK_FACTS = """
gender(girl).
gender(boy).

name_for(girl,mia).
name_for(girl,lena).
name_for(girl,nora).
name_for(girl,ivy).
name_for(girl,zoe).
name_for(boy,finn).
name_for(boy,eli).
name_for(boy,theo).
name_for(boy,noah).
name_for(boy,ben).
"""


def asp_facts() -> str:
    import asp
    lines = [ASP_FALLBACK_FACTS.strip()]
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.shadowy:
            lines.append(asp.fact("shadowy", sid))
        if s.affords_ghost:
            lines.append(asp.fact("affords_ghost", sid))
    for gender, names in NAMES.items():
        lines.append(asp.fact("gender", gender))
        for n in names:
            lines.append(asp.fact("name_for", gender, n.lower()))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_asp_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    clingo = set(valid_asp_stories())
    clingo_normalized = {(s, g, n.capitalize() if n else n) for (s, g, n) in clingo}
    if py == clingo_normalized:
        print(f"OK: ASP and Python agree on {len(py)} valid story combinations.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("python:", sorted(py))
    print("asp:", sorted(clingo_normalized))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], params.name, params.gender, params.guardian)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(setting="old_house", name="Mia", gender="girl", guardian="mother"),
    StoryParams(setting="attic", name="Finn", gender="boy", guardian="father"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = valid_asp_stories()
        print(f"{len(stories)} compatible story seeds:")
        for s, g, n in stories:
            print(f"  {s:10} {g:5} {n}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
