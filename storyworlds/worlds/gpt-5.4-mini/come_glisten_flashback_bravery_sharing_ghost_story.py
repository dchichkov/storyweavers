#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/come_glisten_flashback_bravery_sharing_ghost_story.py
=====================================================================================

A standalone story world for a small ghost-story domain: a child, a glimmering
haunting, a remembered flashback, a brave choice, and a sharing act that turns
fear into warmth.

Seed words:
- come
- glisten

Features:
- Flashback
- Bravery
- Sharing

Style:
- Ghost Story

This world builds a tiny simulation where a child notices a strange glimmer in a
quiet old place, remembers an earlier lonely moment, gathers bravery, and shares
light or comfort with a scared friend/ghost. The ending image proves the change:
the place is still eerie, but it is no longer lonely or frightening.
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

# Make the shared result containers importable when this script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"          # child, ghost, elder, lantern, blanket, room
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""               # seeker | watcher | helper
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"child", "boy", "son"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "daughter"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    echo: str


@dataclass
class Haunting:
    id: str
    thing: str
    glimmer: str
    cause: str
    lonely_note: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Comfort:
    id: str
    thing: str
    glow: str
    share_line: str
    tags: set[str] = field(default_factory=set)


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


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["fear"] < THRESHOLD:
            continue
        sig = ("fear", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["stillness"] += 1
        out.append("")
    return out


CAUSAL_RULES = [Rule("fear", "social", _r_fear)]


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


def valid_combo(setting: Setting, haunting: Haunting, comfort: Comfort) -> bool:
    return "glisten" in haunting.thing or "glisten" in haunting.glimmer


def echo_after_flashback(world: World, child: Entity, haunting: Haunting) -> None:
    child.memes["memory"] += 1
    world.say(
        f"Years before, {child.id} had once lost {child.pronoun('possessive')} way "
        f"in a dark hall and heard only the house breathe. That old memory came "
        f"back now, and it made {child.pronoun('possessive')} heart knock harder."
    )
    world.say(
        f"But the glisten at the end of the hall did not look mean. It waited, as "
        f"if it wanted someone to come closer."
    )


def brave_step(world: World, child: Entity) -> None:
    child.memes["bravery"] += 1
    world.say(
        f'{child.id} swallowed hard, held up a small steady hand, and took one '
        f'brave step forward.'
    )


def reveal(world: World, ghost: Entity, haunting: Haunting) -> None:
    ghost.meters["visible"] += 1
    world.say(
        f"The glisten belonged to {ghost.id}, a little ghost with a soft shine "
        f"on {ghost.pronoun('possessive')} face. {haunting.lonely_note}"
    )


def share(world: World, child: Entity, ghost: Entity, comfort: Comfort) -> None:
    child.memes["kindness"] += 1
    ghost.memes["relief"] += 1
    world.say(
        f'{child.id} remembered that being scared was easier when somebody shared '
        f'with you. So {child.pronoun()} said, "{comfort.share_line}"'
    )
    world.say(
        f"Then {child.id} moved {comfort.thing} closer, and its gentle glow came "
        f"between them like a tiny moon."
    )


def ending(world: World, child: Entity, ghost: Entity, setting: Setting, comfort: Comfort) -> None:
    child.memes["joy"] += 1
    ghost.memes["joy"] += 1
    world.say(
        f"After that, the old {setting.place} still creaked, but it did not feel "
        f"lonely anymore. The glisten stayed soft, the darkness stayed quiet, and "
        f"{child.id} and {ghost.id} sat together in the gentle light, sharing the "
        f"small bright room as if they had always been friends."
    )


def tell(setting: Setting, haunting: Haunting, comfort: Comfort,
         child_name: str = "Mia", child_gender: str = "girl") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender,
                             role="seeker", traits=["careful", "curious"]))
    ghost = world.add(Entity(id="Ghost", kind="character", type="ghost",
                             label="the ghost", role="watcher"))
    world.add(Entity(id="room", type="room", label=setting.place))
    world.add(Entity(id="comfort", type="thing", label=comfort.thing))
    world.facts.update(setting=setting, haunting=haunting, comfort=comfort,
                       child=child, ghost=ghost)

    world.say(
        f"On a quiet night, {child.id} went into {setting.place}. The air had a "
        f"{setting.mood} hush, and every board seemed to listen."
    )
    world.say(
        f"At the far end, something began to {haunting.glimmer}. It was a thin "
        f"silver glow that made the old shadows look deeper."
    )

    world.para()
    echo_after_flashback(world, child, haunting)
    brave_step(world, child)
    reveal(world, ghost, haunting)

    world.para()
    share(world, child, ghost, comfort)
    ending(world, child, ghost, setting, comfort)

    world.facts.update(outcome="shared", brave=child.memes["bravery"] >= THRESHOLD,
                       shared=True)
    return world


SETTINGS = {
    "attic": Setting("attic", "the attic", "dusty", "whisper"),
    "hall": Setting("hall", "the long hall", "cold", "creak"),
    "garden": Setting("garden", "the moonlit garden", "silver", "rustle"),
}

HAUNTINGS = {
    "lantern": Haunting("lantern", "glisten like a lantern", "glisten", "moonlight on glass",
                        "It was not a scary ghost at all; it just looked lonely.",
                        tags={"glisten", "ghost"}),
    "window": Haunting("window", "glisten on the window", "glisten", "rain on glass",
                       "It had been waiting for someone to notice it.",
                       tags={"glisten", "ghost"}),
    "bowl": Haunting("bowl", "glisten in a bowl", "glisten", "polished water",
                     "It had a sad, waiting shine.",
                     tags={"glisten", "ghost"}),
}

COMFORTS = {
    "blanket": Comfort("blanket", "a warm blanket", "a soft warm glow",
                       "You can share my blanket and sit with me."),
    "candle": Comfort("candle", "a little candle lantern", "a tiny steady glow",
                      "I can share this little light with you."),
    "lamp": Comfort("lamp", "a small lamp", "a cozy little glow",
                    "You do not have to stay in the dark with me."),
}

GIRL_NAMES = ["Mia", "Luna", "Iris", "Nora", "Ava", "Ruby"]
BOY_NAMES = ["Noah", "Finn", "Eli", "Leo", "Theo", "Ben"]


@dataclass
class StoryParams:
    setting: str
    haunting: str
    comfort: str
    name: str
    gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for hid, h in HAUNTINGS.items():
            for cid, c in COMFORTS.items():
                if valid_combo(s, h, c):
                    combos.append((sid, hid, cid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Ghost-story world: a glisten, a flashback, bravery, and sharing."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--haunting", choices=HAUNTINGS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.haunting is None or c[1] == args.haunting)
              and (args.comfort is None or c[2] == args.comfort)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, haunting, comfort = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    names = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(names)
    return StoryParams(setting, haunting, comfort, name, gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a ghost story for a 3-to-5-year-old that includes the words "come" and "glisten".',
        f"Tell a gentle ghost story where {f['child'].id} sees something glisten in {f['setting'].place} and comes closer bravely.",
        f"Write a story about flashback, bravery, and sharing, where a lonely glistening ghost becomes a friend.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, ghost, setting, haunting = f["child"], f["ghost"], f["setting"], f["haunting"]
    comfort = f["comfort"]
    return [
        QAItem(
            question="What did the child notice in the dark place?",
            answer=f"{child.id} noticed a soft glisten in {setting.place}. It belonged to {ghost.id}, who had been waiting to be seen."
        ),
        QAItem(
            question="Why did the child feel brave?",
            answer=f"{child.id} remembered an old scary time in a flashback, but instead of running away, {child.pronoun()} took a brave step closer. That courage helped turn the fear into kindness."
        ),
        QAItem(
            question="How did sharing change the ending?",
            answer=f"{child.id} shared {comfort.thing} and its gentle glow, so {ghost.id} was no longer lonely. The shared light made the old place feel warm and friendly."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean when something glistens?",
            answer="When something glistens, it shines softly, usually with a little wet or shiny sparkle."
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing the right thing even when you feel scared. A brave person can feel fear and still take a careful step forward."
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting someone else use or enjoy something with you. It can make a sad or lonely moment feel kinder."
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], HAUNTINGS[params.haunting],
                 COMFORTS[params.comfort], params.name, params.gender)
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


ASP_RULES = r"""
valid(S, H, C) :- setting(S), haunting(H), comfort(C), glisteny(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid, h in HAUNTINGS.items():
        lines.append(asp.fact("haunting", hid))
        if "glisten" in h.tags:
            lines.append(asp.fact("glisteny", hid))
    for cid in COMFORTS:
        lines.append(asp.fact("comfort", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in valid combos.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


CURATED = [
    StoryParams("attic", "lantern", "blanket", "Mia", "girl"),
    StoryParams("hall", "window", "lamp", "Noah", "boy"),
    StoryParams("garden", "bowl", "candle", "Luna", "girl"),
]


def outcome_of(params: StoryParams) -> str:
    return "shared"


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
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
            header = f"### {p.name}: {p.setting} / {p.haunting} / {p.comfort} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
