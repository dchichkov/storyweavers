#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/scape_bravery_bad_ending_teamwork_fairy_tale.py
==============================================================================

A standalone story world for a tiny fairy-tale domain:
a brave child and a helper try to fix a problem together, but the tale can end
badly if the danger grows faster than their plan.

Core ingredients:
- fairy-tale style
- bravery
- teamwork
- a bad ending
- the seed word "scape" woven into the prose/world
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "princess", "mother", "woman"}
        male = {"boy", "king", "prince", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    dark: str
    wind: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Threat:
    id: str
    label: str
    danger: str
    spread: int
    makes_smoke: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Ally:
    id: str
    label: str
    action: str
    help_text: str
    power: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class StoryParams:
    place: str
    threat: str
    ally: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    ruler: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World()
        w.entities = {k: v for k, v in self.entities.items()}
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_smoke(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["burning"] < THRESHOLD:
            continue
        sig = ("smoke", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("castle").meters["danger"] += 1
        world.get("hero").memes["fear"] += 1
        world.get("helper").memes["fear"] += 1
        out.append("__smoke__")
    return out


CAUSAL_RULES = [Rule("smoke", _r_smoke)]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    out: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            produced = rule.apply(world)
            if produced:
                changed = True
                out.extend(x for x in produced if not x.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)


def hazard_risk(place: Place, threat: Threat) -> bool:
    return threat.makes_smoke and "dry" in place.tags


def can_teamwork(ally: Ally) -> bool:
    return ally.power >= 2


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for tid, threat in THREATS.items():
            for aid, ally in ALLIES.items():
                if hazard_risk(place, threat) and can_teamwork(ally):
                    combos.append((pid, tid, aid))
    return combos


def _do_danger(world: World, target_id: str, threat: Threat, narrate: bool = True) -> None:
    tgt = world.get(target_id)
    tgt.meters["burning"] += 1
    tgt.meters["soot"] += 1
    propagate(world, narrate=narrate)


def tell(place: Place, threat: Threat, ally: Ally, params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    ruler = world.add(Entity(id="ruler", kind="character", type=params.ruler, label="the queen"))
    castle = world.add(Entity(id="castle", label=place.label, kind="thing"))
    scape = world.add(Entity(id="scape", label="the moon-scape beyond the tower", kind="thing"))
    crown = world.add(Entity(id="crown", label=threat.label, kind="thing"))
    world.facts.update(hero=hero, helper=helper, ruler=ruler, castle=castle, scape=scape, crown=crown,
                        place=place, threat=threat, ally=ally)

    hero.memes["bravery"] += 1
    helper.memes["teamwork"] += 1

    world.say(
        f"Once upon a time, in {place.label}, {hero.id} and {helper.id} lived by a tall castle "
        f"where the moon-scape shone silver at dusk."
    )
    world.say(
        f"{hero.id} was brave, and {helper.id} was quick with helping hands. Together they hoped to "
        f"keep the royal hall safe."
    )

    world.para()
    world.say(
        f"One night, a {threat.label} crept close and left {threat.danger}. The hall grew dark, and "
        f"{hero.id} whispered, \"We must act now.\""
    )
    world.say(
        f"{helper.id} nodded. \"If we work together, we can {ally.action}.\""
    )

    _do_danger(world, "castle", threat, narrate=False)
    if world.get("castle").meters["danger"] >= 1:
        world.say(
            f"{hero.id} ran to the door while {helper.id} hurried for help, and the two of them tried "
            f"to stop the trouble before it spread."
        )

    world.para()
    if ally.power >= threat.spread:
        world.get("castle").meters["burning"] = 0
        hero.memes["bravery"] += 1
        helper.memes["teamwork"] += 1
        world.say(
            f"They managed to {ally.help_text}, and for a little while the castle grew quiet again."
        )
        world.say(
            f"But the {threat.label} had already whispered to the dry beams, and smoke curled up toward "
            f"the rafters."
        )
        world.say(
            f"At last the queen came, but the fire had done its worst. The hall was lost, yet {hero.id} "
            f"and {helper.id} stood together, holding hands in the cold ash."
        )
        outcome = "bad"
    else:
        world.say(
            f"They tried to {ally.help_text}, but the danger was stronger than their plan."
        )
        world.say(
            f"The {threat.label} raced through the hall, and the brave pair had to scape out through "
            f"the side gate before the whole castle went black with smoke."
        )
        world.say(
            f"When morning came, the queen found only soot, a broken crown, and two tired children who "
            f"had learned that courage is not always enough."
        )
        outcome = "bad"

    world.facts["outcome"] = outcome
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story that includes the word "scape", bravery, and teamwork, and ends in a bad ending.',
        f"Tell a fairy tale where {f['hero'].id} and {f['helper'].id} try to help each other, but the danger wins in the end.",
        f"Write a short story about a brave child and a helper who try to save {f['place'].label}, but the ending is sad and smoky.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, ruler, place, threat, ally = f["hero"], f["helper"], f["ruler"], f["place"], f["threat"], f["ally"]
    return [
        QAItem(
            question="Who are the main characters?",
            answer=f"The main characters are {hero.id} and {helper.id}. They are the two children who try to help the castle together."
        ),
        QAItem(
            question="What problem do they face?",
            answer=f"A {threat.label} brings {threat.danger}, and it threatens {place.label}. That is why the children hurry to act."
        ),
        QAItem(
            question="Why is the ending bad?",
            answer=(
                f"Their plan was not strong enough to stop the danger. Even though they were brave and worked together, "
                f"the castle was lost and only smoke and soot were left behind."
            )
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does bravery mean in a fairy tale?",
            answer="Bravery means facing a scary problem and still trying to do what is right. A brave character may feel afraid, but keeps going anyway."
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help one another and use their different strengths together. When teamwork works well, the group can do more than one person could alone."
        ),
        QAItem(
            question="What does scape mean in this world?",
            answer="In this story world, scape points to escaping from danger. The word reminds us that the children had to run for safety when their plan failed."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


THEMES = {
    "castle": Place(id="castle", label="the silver castle", dark="the hall went dark", wind="the wind rose"),
    "keep": Place(id="keep", label="the old keep", dark="the keep darkened", wind="the wind rose"),
    "tower": Place(id="tower", label="the moonlit tower", dark="the tower darkened", wind="the wind sighed"),
}

THREATS = {
    "candle_spill": Threat(id="candle_spill", label="spilled candle", danger="a ribbon of flame on the floor", spread=2),
    "torch_fall": Threat(id="torch_fall", label="fallen torch", danger="sparks on the dry boards", spread=3),
}

ALLIES = {
    "bucket_team": Ally(id="bucket_team", label="bucket teamwork", action="bring water and blankets", help_text="bring buckets and blankets", power=2),
    "wall_team": Ally(id="wall_team", label="wall teamwork", action="pull the curtain down", help_text="pull the curtain down and smother the fire", power=3),
    "gate_team": Ally(id="gate_team", label="gate teamwork", action="open the gate and call the guards", help_text="open the gate and call the guards", power=1),
}

HERO_NAMES = ["Ari", "Mina", "Ivo", "Nell", "Finn", "Tia"]
HELPER_NAMES = ["Pip", "Joss", "Luna", "Bram", "Rae", "Oren"]


@dataclass
class StoryParams:
    place: str
    threat: str
    ally: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    ruler: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


CURATED = [
    StoryParams(place="castle", threat="torch_fall", ally="bucket_team", hero="Ari", hero_gender="boy", helper="Luna", helper_gender="girl", ruler="queen"),
    StoryParams(place="keep", threat="candle_spill", ally="wall_team", hero="Mina", hero_gender="girl", helper="Pip", helper_gender="boy", ruler="queen"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.threat is None or c[1] == args.threat)
              and (args.ally is None or c[2] == args.ally)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, threat, ally = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != hero])
    ruler = args.ruler or "queen"
    return StoryParams(place=place, threat=threat, ally=ally, hero=hero, hero_gender=hero_gender,
                       helper=helper, helper_gender=helper_gender, ruler=ruler)


def generate(params: StoryParams) -> StorySample:
    if params.place not in THEME_CHOICES or params.threat not in THREAT_CHOICES or params.ally not in ALLY_CHOICES:
        raise StoryError("Invalid story parameters.")
    world = tell(THEME_CHOICES[params.place], THREAT_CHOICES[params.threat], ALLY_CHOICES[params.ally], params)
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


ASP_RULES = r"""
place(P) :- theme(P).
threat(T) :- danger(T).
ally(A) :- helper(A).
valid(P,T,A) :- place(P), threat(T), ally(A), hazard(P,T), teamwork(A).
bad_end :- valid(_,_,_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in THEME_CHOICES:
        lines.append(asp.fact("theme", pid))
    for tid, t in THREAT_CHOICES.items():
        lines.append(asp.fact("danger", tid))
        lines.append(asp.fact("spread", tid, t.spread))
        lines.append(asp.fact("makes_smoke", tid))
    for aid, a in ALLY_CHOICES.items():
        lines.append(asp.fact("helper", aid))
        lines.append(asp.fact("power", aid, a.power))
    lines.append(asp.fact("sense", "story", 1))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python:")
        print("  only in ASP:", sorted(cl - py))
        print("  only in Python:", sorted(py - cl))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test produced a story.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale story world with bravery, teamwork, and a bad ending.")
    ap.add_argument("--place", choices=THEME_CHOICES)
    ap.add_argument("--threat", choices=THREAT_CHOICES)
    ap.add_argument("--ally", choices=ALLY_CHOICES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--ruler", choices=["queen", "king"])
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


THEME_CHOICES = THEMES
THREAT_CHOICES = THREATS
ALLY_CHOICES = ALLIES


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
