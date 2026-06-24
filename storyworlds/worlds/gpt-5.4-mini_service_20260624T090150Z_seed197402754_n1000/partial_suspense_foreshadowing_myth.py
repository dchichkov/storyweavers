#!/usr/bin/env python3
"""
storyworlds/worlds/partial_suspense_foreshadowing_myth.py
==========================================================

A small mythic storyworld about a partial omen, a growing hush, and a
foreshadowed rescue.

The seed image behind this world:
---
A village keeps a moon-drum in a stone shrine. Each year, when the moon turns
only partly dark, the elders say the river giant is waking. A young child hears
the omen, follows the clues, and learns that the giant is not angry at all: it
is trapped under a cracked bridge and needs help to breathe again.

World model:
---
Physical meters:
    - glow, shadow, flood, crack, smoke, fatigue, calm

Emotional memes:
    - awe, fear, hope, trust, suspense, courage, relief

Narrative instruments:
---
    - suspense rises when an omen is partial and the cause is not yet known
    - foreshadowing is carried by recurring clues (drum, river hush, cracked stone)
    - the ending resolves when the hidden cause is revealed and acted on

This script is standalone and keeps the story domain deliberately small and
constraint-checked.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "mother", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "father", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the river shrine"
    river: str = "the river"
    sky: str = "the sky"


@dataclass
class Omen:
    name: str
    partialness: str
    clue: str
    effect: str
    shadow_gain: float
    suspense_gain: float


@dataclass
class Hero:
    name: str
    gender: str
    trait: str
    age: str = "young"


@dataclass
class SacredThing:
    label: str
    phrase: str
    type: str
    important: bool = True


@dataclass
class Relic:
    label: str
    phrase: str
    type: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.night: bool = False

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
        clone.night = self.night
        return clone


def _r_shadow_grows(world: World) -> list[str]:
    out: list[str] = []
    omen = world.facts.get("omen")
    if not omen:
        return out
    moon = world.entities["moon_drum"]
    if moon.meters.get("shadow", 0.0) < THRESHOLD:
        sig = ("shadow", omen.name)
        if sig not in world.fired:
            world.fired.add(sig)
            moon.meters["shadow"] = world.facts["shadow_level"]
            out.append("The omen made the shrine feel half-lit and half-hidden.")
    return out


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("mystery") and not world.facts.get("reveal"):
        sig = ("suspense")
        if sig not in world.fired:
            world.fired.add(sig)
            hero = world.get("hero")
            hero.memes["suspense"] = hero.memes.get("suspense", 0.0) + 1
            out.append("The unanswered clue kept everyone listening closely.")
    return out


def _r_reveal_calm(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("reveal") and not world.facts.get("calmed"):
        sig = ("calm")
        if sig not in world.fired:
            world.fired.add(sig)
            giant = world.get("giant")
            giant.meters["flood"] = 0.0
            giant.memes["calm"] = giant.memes.get("calm", 0.0) + 1
            out.append("The hidden cause was named at last, and the river grew gentle.")
    return out


CAUSAL_RULES = [
    _r_shadow_grows,
    _r_suspense,
    _r_reveal_calm,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "shrine": Setting(place="the river shrine", river="the river", sky="the sky"),
    "bridge": Setting(place="the cracked bridge", river="the river", sky="the night sky"),
    "bank": Setting(place="the river bank", river="the river", sky="the moonlit sky"),
}

OMENS = {
    "partial_moon": Omen(
        name="partial moon",
        partialness="only half the moon darkened",
        clue="the drum sounded from the shrine",
        effect="the elders whispered that something was not yet finished",
        shadow_gain=1.0,
        suspense_gain=1.0,
    ),
    "half_eclipse": Omen(
        name="half eclipse",
        partialness="the moon wore a dark bite across its face",
        clue="the river went quiet under the stars",
        effect="the lamps seemed to blink as if they were worried",
        shadow_gain=1.0,
        suspense_gain=1.0,
    ),
}

HEROS = [
    Hero(name="Nia", gender="girl", trait="curious"),
    Hero(name="Taro", gender="boy", trait="careful"),
    Hero(name="Mina", gender="girl", trait="brave"),
]

SACRED_THINGS = {
    "moon_drum": SacredThing(
        label="moon drum",
        phrase="a carved moon drum with a silver strap",
        type="drum",
    ),
    "river_lantern": SacredThing(
        label="river lantern",
        phrase="a small lantern for the river path",
        type="lantern",
    ),
}

RELICS = {
    "cracked_stone": Relic(
        label="cracked stone",
        phrase="a cracked stone from the bridge",
        type="stone",
    ),
    "reed_key": Relic(
        label="reed key",
        phrase="a reed key tied with red thread",
        type="key",
    ),
}


@dataclass
class StoryParams:
    setting: str
    omen: str
    hero: str
    relic: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [
        (s, o, h.name, r)
        for s in SETTINGS
        for o in OMENS
        for h in HEROS
        for r in RELICS
    ]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic story world of partial omen and foreshadowed rescue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--omen", choices=OMENS)
    ap.add_argument("--hero", choices=[h.name for h in HEROS])
    ap.add_argument("--relic", choices=RELICS)
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
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.omen:
        combos = [c for c in combos if c[1] == args.omen]
    if args.hero:
        combos = [c for c in combos if c[2] == args.hero]
    if args.relic:
        combos = [c for c in combos if c[3] == args.relic]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    s, o, h, r = rng.choice(sorted(combos))
    return StoryParams(setting=s, omen=o, hero=h, relic=r)


def make_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = next(h for h in HEROS if h.name == params.hero)
    omen = OMENS[params.omen]
    relic = RELICS[params.relic]

    hero_ent = world.add(Entity(id="hero", kind="character", type=hero.gender, label=hero.name, phrase=f"{hero.name}, the {hero.trait} child"))
    drum = world.add(Entity(id="moon_drum", type="drum", label="moon drum", phrase=SACRED_THINGS["moon_drum"].phrase))
    giant = world.add(Entity(id="giant", kind="character", type="giant", label="river giant", phrase="the river giant"))
    relic_ent = world.add(Entity(id="relic", type=relic.type, label=relic.label, phrase=relic.phrase, owner=hero_ent.id))

    world.facts.update(hero=hero_ent, omen=omen, relic=relic_ent, giant=giant, drum=drum)
    return world


def story_intro(world: World) -> None:
    hero = world.facts["hero"]
    omen = world.facts["omen"]
    world.say(f"{hero.label} was a {hero.phrase} who listened when old stories drifted through {world.setting.place}.")
    world.say(f"On the night of the {omen.name}, the sky showed that {omen.partialness}, and everyone knew a tale was beginning.")


def story_foreshadow(world: World) -> None:
    omen = world.facts["omen"]
    world.facts["shadow_level"] = omen.shadow_gain
    world.facts["mystery"] = True
    world.say(f"The elders pointed to the drum because {omen.clue}, and that was the first clue.")
    world.say(f"{omen.effect}, which made the air feel full of waiting.")
    propagate(world, narrate=True)


def story_turn(world: World) -> None:
    hero = world.facts["hero"]
    giant = world.facts["giant"]
    relic = world.facts["relic"]
    world.para()
    world.say(f"{hero.label} followed the hush to the {world.setting.place} and found {relic.phrase} tucked beside the stones.")
    world.say(f"Near the cracked place in the bridge, the river giant was not roaring at all; {giant.pronoun('subject')} was breathing in short, worried pulls.")
    hero.memes["awe"] = hero.memes.get("awe", 0.0) + 1
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    world.say(f"{hero.label} felt awe, a little fear, and a bright thread of hope at once.")
    world.facts["mystery"] = True


def story_reveal(world: World) -> None:
    hero = world.facts["hero"]
    giant = world.facts["giant"]
    relic = world.facts["relic"]
    world.para()
    world.say(f"{hero.label} set the {relic.label} into the crack, and the missing piece fit like a remembered word.")
    world.facts["reveal"] = True
    giant.meters["flood"] = 0.0
    giant.memes["trust"] = giant.memes.get("trust", 0.0) + 1
    hero.memes["courage"] = hero.memes.get("courage", 0.0) + 1
    propagate(world, narrate=True)
    world.say(f"Then the giant could breathe out, and the river stopped pressing hard against the stones.")


def story_resolution(world: World) -> None:
    hero = world.facts["hero"]
    giant = world.facts["giant"]
    world.para()
    world.say(f"{hero.label} and the river giant watched the moon together, and the shadow no longer felt like a threat.")
    world.say(f"The old omen had not meant anger after all; it had been a warning to look closely.")
    world.say(f"By the end, {hero.label} carried courage in {hero.pronoun('possessive')} hands, and the giant carried calm in {giant.pronoun('possessive')} chest.")


def tell(params: StoryParams) -> World:
    world = make_world(params)
    story_intro(world)
    story_foreshadow(world)
    story_turn(world)
    story_reveal(world)
    story_resolution(world)
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    omen = world.facts["omen"]
    relic = world.facts["relic"]
    return [
        f"Write a short myth for children about {hero.label}, a {hero.phrase}, who notices a {omen.name}.",
        f"Tell a suspenseful story with foreshadowing where a partial omen at {world.setting.place} leads to the discovery of {relic.label}.",
        f"Write a gentle myth in which a child follows clues from the sky and helps a river giant."
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    omen = world.facts["omen"]
    relic = world.facts["relic"]
    giant = world.facts["giant"]
    return [
        QAItem(
            question=f"Who listened to the old stories and followed the clue at {world.setting.place}?",
            answer=f"{hero.label} did. {hero.label} was the child who noticed the omen and went to look closely.",
        ),
        QAItem(
            question=f"What was strange about the sky during the {omen.name}?",
            answer=f"Only part of the moon was darkened, so the omen felt unfinished and mysterious instead of complete.",
        ),
        QAItem(
            question=f"What helped solve the problem with the river giant?",
            answer=f"The {relic.label} helped. {hero.label} placed it into the crack, and that let the giant breathe more easily.",
        ),
        QAItem(
            question=f"Why did the story feel suspenseful before the end?",
            answer="Because the signs were clear but the cause was still hidden, so everyone had to wait and listen before the truth was revealed.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The fear turned into calm. The giant was no longer trapped, and the river stopped pressing hard against the bridge.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an omen?",
            answer="An omen is a sign that people think points toward something important that may happen soon.",
        ),
        QAItem(
            question="What does foreshadowing do in a story?",
            answer="Foreshadowing gives small clues early so the reader can guess that something important will happen later.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of not knowing what will happen next, which can make a story feel tense and exciting.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}}")
        if e.memes:
            bits.append(f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
partial_omen(O) :- omen(O), partial(O).
foreshadow(C) :- clue(C), omen(O), partial_omen(O).
suspense_up(H) :- hero(H), mystery.
reveal_done :- rescue, calm.
valid_story(S,O,H,R) :- setting(S), omen(O), hero(H), relic(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for o in OMENS:
        lines.append(asp.fact("omen", o))
    for o, val in OMENS.items():
        lines.append(asp.fact("partial", o))
        lines.append(asp.fact("clue", val.clue))
    for h in HEROS:
        lines.append(asp.fact("hero", h.name))
    for r in RELICS:
        lines.append(asp.fact("relic", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    clingo_set = set(asp.atoms(asp.one_model(asp_program("#show valid_story/4.")), "valid_story"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams(setting="shrine", omen="partial_moon", hero="Nia", relic="cracked_stone"),
    StoryParams(setting="bridge", omen="half_eclipse", hero="Taro", relic="reed_key"),
    StoryParams(setting="bank", omen="partial_moon", hero="Mina", relic="cracked_stone"),
]


def explain_rejection() -> str:
    return "(No story: this myth needs a partial omen, a child who notices it, and a relic that can complete the broken place.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.omen:
        combos = [c for c in combos if c[1] == args.omen]
    if args.hero:
        combos = [c for c in combos if c[2] == args.hero]
    if args.relic:
        combos = [c for c in combos if c[3] == args.relic]
    if not combos:
        raise StoryError(explain_rejection())
    s, o, h, r = rng.choice(sorted(combos))
    return StoryParams(setting=s, omen=o, hero=h, relic=r)


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


def build_asp_modes() -> str:
    return asp_program("#show valid_story/4.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(build_asp_modes())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible (setting, omen, hero, relic) combos:\n")
        for s, o, h, r in stories:
            print(f"  {s:8} {o:14} {h:8} {r}")
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
            header = f"### {p.hero}: {p.omen} at {p.setting} (relic: {p.relic})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
