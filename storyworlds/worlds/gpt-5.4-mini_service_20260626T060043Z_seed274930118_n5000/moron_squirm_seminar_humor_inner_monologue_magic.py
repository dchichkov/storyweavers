#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/moron_squirm_seminar_humor_inner_monologue_magic.py
================================================================================

A tiny whodunit-style story world about a school seminar, a mildly magical clue,
a squirmy suspect, and a funny detective whose inner monologue keeps them one
step ahead.

Premise seed:
- moron
- squirm
- seminar

Style target:
- whodunit
- humor
- inner monologue
- magic
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
    caretaker: Optional[str] = None
    role: str = ""
    plural: bool = False
    magical: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the school seminar room"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class PlotDevice:
    id: str
    label: str
    phrase: str
    clue_kind: str
    reveal_kind: str
    kind: str = "thing"


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    look: str
    guilty_by_default: bool = False


@dataclass
class StoryParams:
    setting: str
    device: str
    suspect: str
    hero_name: str
    hero_type: str
    sidekick: str
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


def _r_squirm(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.memes.get("nervous", 0) < THRESHOLD:
            continue
        if e.meters.get("squirm", 0) >= THRESHOLD:
            continue
        sig = ("squirm", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["squirm"] = e.meters.get("squirm", 0) + 1
        out.append(f"{e.label} kept squirming in {e.pronoun('possessive')} seat.")
    return out


def _r_magic_reveal(world: World) -> list[str]:
    out: list[str] = []
    lamp = world.entities.get("lamp")
    device = world.entities.get("device")
    if not lamp or not device:
        return out
    if lamp.meters.get("glow", 0) < THRESHOLD:
        return out
    if device.meters.get("hidden", 0) < THRESHOLD:
        return out
    sig = ("reveal", device.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    device.meters["hidden"] = 0
    device.meters["seen"] = 1
    out.append(f"The glow from the lamp made the {device.label} appear in a blink.")
    return out


RULES = [
    _r_squirm,
    _r_magic_reveal,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            got = rule(world)
            if got:
                changed = True
                out.extend(got)
    if narrate:
        for s in out:
            world.say(s)
    return out


SETTINGS = {
    "seminar_room": Setting(place="the school seminar room", indoors=True, affords={"seminar"}),
    "library_corner": Setting(place="the library corner", indoors=True, affords={"seminar"}),
}


DEVICES = {
    "golden_pointer": PlotDevice(
        id="device",
        label="golden pointer",
        phrase="a tiny golden pointer",
        clue_kind="glitter",
        reveal_kind="glow",
    ),
    "magnetic_note": PlotDevice(
        id="device",
        label="magnetic note",
        phrase="a magnetic note card",
        clue_kind="ink",
        reveal_kind="glow",
    ),
}

SUSPECTS = {
    "moron": Suspect(
        id="suspect",
        label="Mr. Moron",
        type="man",
        look="a very serious man with a crooked tie",
        guilty_by_default=True,
    ),
    "coach": Suspect(
        id="suspect",
        label="Coach Clover",
        type="man",
        look="a cheerful coach with sticky hands",
    ),
    "librarian": Suspect(
        id="suspect",
        label="Mrs. Reed",
        type="woman",
        look="a neat librarian with a calm smile",
    ),
}

HERO_NAMES = ["Mia", "Nora", "Eli", "Theo", "Ava", "Ruby", "Leo", "Sam"]
SIDEKICKS = ["a talking paperclip", "a tiny chalk ghost", "a squeaky notebook", "a toy magnifier"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for d in DEVICES:
            for sus in SUSPECTS:
                if s == "seminar_room" and d == "golden_pointer":
                    combos.append((s, d, sus))
                if s == "library_corner":
                    combos.append((s, d, sus))
    return combos


def explain_rejection(setting: str, device: str) -> str:
    return f"(No story: the {setting} and {device} do not make a clean seminar mystery here.)"


def explain_suspect(suspect: str) -> str:
    return f"(No story: {suspect} does not fit the whodunit tone for this little seminar mystery.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit seminar storyworld with humor and magic.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--device", choices=DEVICES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--sidekick")
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
    if args.setting and args.device and (args.setting, args.device, args.suspect or "moron") not in combos:
        raise StoryError(explain_rejection(args.setting, args.device))
    pick = rng.choice(combos)
    setting = args.setting or pick[0]
    device = args.device or pick[1]
    suspect = args.suspect or rng.choice(list(SUSPECTS))
    if suspect not in SUSPECTS:
        raise StoryError(explain_suspect(suspect))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    sidekick = args.sidekick or rng.choice(SIDEKICKS)
    return StoryParams(setting=setting, device=device, suspect=suspect, hero_name=hero_name, hero_type=hero_type, sidekick=sidekick)


def setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name, role="detective"))
    suspect_def = SUSPECTS[params.suspect]
    suspect = world.add(Entity(id="suspect", kind="character", type=suspect_def.type, label=suspect_def.label, role="suspect"))
    sidekick = world.add(Entity(id="sidekick", kind="thing", type="thing", label=params.sidekick, role="helper"))
    lamp = world.add(Entity(id="lamp", kind="thing", type="thing", label="magic lamp", magical=True))
    device_def = DEVICES[params.device]
    device = world.add(Entity(id="device", kind="thing", type="thing", label=device_def.label, phrase=device_def.phrase, magical=False))
    device.meters["hidden"] = 1
    suspect.memes["nervous"] = 1 if suspect_def.guilty_by_default else 0
    world.facts.update(hero=hero, suspect=suspect, sidekick=sidekick, lamp=lamp, device=device, device_def=device_def, suspect_def=suspect_def)
    return world


def intro(world: World) -> None:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    world.say(f"{hero.label} arrived at {world.setting.place} with {sidekick.label} tucked under one arm.")
    world.say(f"Today's event was a seminar about lost things, and {hero.label} already felt like a detective in a funny story.")


def clue_seen(world: World) -> None:
    f = world.facts
    hero = f["hero"]
    device_def = f["device_def"]
    world.say(f"On the table sat {device_def.phrase}, and that was odd because the speaker had just called it missing.")
    world.say(f"{hero.label} thought, \"If something is missing at a seminar, it usually hides where nobody looks.\"")


def suspect_act(world: World) -> None:
    f = world.facts
    suspect = f["suspect"]
    world.say(f"{suspect.label} kept clearing {suspect.pronoun('possessive')} throat and smiling too fast.")
    world.say(f"{world.facts['hero'].label} thought, \"Hmm. That smile is wobbling like jelly.\"")
    suspect.memes["nervous"] = 1
    propagate(world, narrate=True)


def magic_reveal(world: World) -> None:
    f = world.facts
    lamp = f["lamp"]
    device = f["device"]
    hero = f["hero"]
    lamp.meters["glow"] = 1
    world.say(f"{hero.label} lifted the magic lamp and whispered, \"Show me the clue.\"")
    propagate(world, narrate=True)
    if device.meters.get("seen"):
        world.say(f"The hidden clue glittered, and {hero.label} grinned because the answer had been there all along.")
    else:
        world.say(f"Nothing changed, which made {hero.label}'s eyebrows climb higher.")


def reveal_solution(world: World) -> None:
    f = world.facts
    hero = f["hero"]
    suspect = f["suspect"]
    device = f["device"]
    world.say(f"{hero.label} looked from the lamp to {suspect.label} and then back to the little golden pointer.")
    world.say(f"\"Aha,\" {hero.label} thought. \"The moron joke was just a sloppy cover. The real clue was the glow.\"")
    world.say(f"{suspect.label} finally squirmed and admitted {suspect.pronoun('subject')} had hidden the {device.label} by mistake while tidying up the seminar table.")
    world.say(f"{hero.label} laughed, because the great mystery ended up being a mix-up, not a mean trick.")
    world.say(f"By the end of the seminar, the missing {device.label} was back on the table, and everyone was smiling instead of squirming.")


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    intro(world)
    world.para()
    clue_seen(world)
    suspect_act(world)
    world.para()
    magic_reveal(world)
    reveal_solution(world)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit for a child set at {world.setting.place} with a funny seminar mystery and a magic lamp.',
        f"Tell a humorous detective story where {f['hero'].label} notices a missing seminar clue and suspects {f['suspect'].label}.",
        f'Write a tiny mystery story that includes the words "moron", "squirm", and "seminar" and ends with a magical reveal.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    suspect = f["suspect"]
    device = f["device"]
    return [
        QAItem(
            question=f"Where did {hero.label} go to solve the mystery?",
            answer=f"{hero.label} went to {world.setting.place} for a seminar about lost things.",
        ),
        QAItem(
            question=f"What missing thing did the detective find?",
            answer=f"{hero.label} found the {device.label} and put the missing seminar clue back where it belonged.",
        ),
        QAItem(
            question=f"Who squirmed when the clue was revealed?",
            answer=f"{suspect.label} squirmed and admitted the mix-up after the magic lamp made the clue appear.",
        ),
        QAItem(
            question=f"Why did {hero.label} think the answer was funny?",
            answer=f"{hero.label} realized the mystery was not a scary crime at all. It was a silly mistake with a hidden clue, so the ending felt funny instead of mean.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a seminar?",
            answer="A seminar is a meeting or lesson where people gather to learn about one topic and listen to a speaker.",
        ),
        QAItem(
            question="What does it mean to squirm?",
            answer="To squirm means to wiggle a little because you feel nervous, uncomfortable, or excited.",
        ),
        QAItem(
            question="What does magic do in a story?",
            answer="Magic can make impossible things happen, like making a hidden clue glow or appear.",
        ),
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.magical:
            bits.append("magical=True")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
entity(hero). entity(suspect). entity(lamp). entity(device).
can_squirm(X) :- nervous(X).
squirms(X) :- can_squirm(X).
can_reveal(lamp, device) :- glow(lamp), hidden(device).
revealed(device) :- can_reveal(lamp, device).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for did in DEVICES:
        lines.append(asp.fact("device", did))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show revealed/1. #show squirms/1."))
    got = set((sym.name, tuple(a.string if a.type == a.type.String else a.number if a.type == a.type.Number else a.name for a in sym.arguments)) for sym in model)
    want = {("squirms", ("suspect",)), ("revealed", ("device",))}
    if got == want:
        print("OK: ASP twin matches the Python reasonableness gate.")
        return 0
    print("MISMATCH:", got, want)
    return 1


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


def build_sample(params: StoryParams) -> StorySample:
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
    StoryParams(setting="seminar_room", device="golden_pointer", suspect="moron", hero_name="Mia", hero_type="girl", sidekick="a tiny chalk ghost"),
    StoryParams(setting="library_corner", device="magnetic_note", suspect="librarian", hero_name="Eli", hero_type="boy", sidekick="a talking paperclip"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show revealed/1. #show squirms/1."))
        return
    if args.asp:
        print(f"{len(valid_story_combos())} compatible seminar story combos.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [build_sample(p) for p in CURATED]
    else:
        seen = set()
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
            sample = build_sample(params)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.setting} / {p.device} / {p.suspect}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
