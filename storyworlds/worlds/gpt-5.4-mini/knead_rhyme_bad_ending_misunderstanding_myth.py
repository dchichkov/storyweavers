#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/knead_rhyme_bad_ending_misunderstanding_myth.py
==============================================================================

A small myth-flavored storyworld about a child who kneads sacred dough, a rhyme
that is heard the wrong way, and a misunderstanding that leads to a bad ending.

Domain sketch
-------------
In a little village near an old stone shrine, a child prepares festival dough
for a moon offering. A short rhyme is meant to guide the kneading, but the words
get misunderstood: someone thinks the rhythm is a command to hurry, and the dough
is overworked until it tears. The offering fails, the moonlight fades from the
bowl, and the child learns that old sayings can be dangerous when they are heard
wrong.

This world is intentionally small and constraint-checked. It uses typed entities
with physical meters and emotional memes, a forward-chained rule engine, a
reasonableness gate, QA grounded in world state, and an inline ASP twin for
parity checks.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/knead_rhyme_bad_ending_misunderstanding_myth.py
    python storyworlds/worlds/gpt-5.4-mini/knead_rhyme_bad_ending_misunderstanding_myth.py --all
    python storyworlds/worlds/gpt-5.4-mini/knead_rhyme_bad_ending_misunderstanding_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/knead_rhyme_bad_ending_misunderstanding_myth.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Site:
    id: str
    place: str
    old: str
    shrine: str
    sky: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Dough:
    id: str
    label: str
    phrase: str
    kneadable: bool = True
    fragile: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Rhyme:
    id: str
    verse: str
    meaning: str
    rhythm: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Misunderstanding:
    id: str
    heard_as: str
    mistake: str
    harm: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
            value = defaultdict(float)
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


def _r_overknead(world: World) -> list[str]:
    out: list[str] = []
    kid = world.entities.get("child")
    dough = world.entities.get("dough")
    if not kid or not dough:
        return out
    if kid.memes["hurt"] < THRESHOLD or dough.meters["torn"] < THRESHOLD:
        return out
    sig = ("overknead", dough.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    house = world.entities.get("house")
    if house:
        house.meters["doom"] += 1
    kid.memes["fear"] += 1
    out.append("__ending__")
    return out


def _r_misread(world: World) -> list[str]:
    out: list[str] = []
    singer = world.entities.get("elder")
    child = world.entities.get("child")
    if not singer or not child:
        return out
    if singer.memes["warning"] < THRESHOLD or child.memes["confused"] < THRESHOLD:
        return out
    sig = ("misread", singer.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["panic"] += 1
    out.append("__misunderstanding__")
    return out


CAUSAL_RULES = [
    Rule("misread", "social", _r_misread),
    Rule("overknead", "physical", _r_overknead),
]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            for sent in rule.apply(world):
                changed = True
                if not sent.startswith("__"):
                    produced.append(sent)
    for sent in produced:
        world.say(sent)
    return produced


def reasonableness_gate(site: Site, dough: Dough, rhyme: Rhyme, mis: Misunderstanding) -> bool:
    return dough.kneadable and rhyme.rhythm == "steady" and mis.mistake in {"hurry", "shout", "rush"}


def outcome_of(params: "StoryParams") -> str:
    return "bad_ending" if params.misunderstanding else "safe"


def make_bread(world: World, child: Entity, dough: Dough) -> None:
    child.memes["hope"] += 1
    dough_entity = world.get("dough")
    dough_entity.meters["kneaded"] += 1
    dough_entity.meters["warm"] += 1


def warn(world: World, elder: Entity, child: Entity, rhyme: Rhyme, mis: Misunderstanding) -> None:
    elder.memes["warning"] += 1
    child.memes["confused"] += 1
    world.say(
        f'{elder.id} recited an old rhyme: "{rhyme.verse}" '
        f"but the words were easy to hear wrong. {mis.harm.capitalize()} could follow."
    )


def misunderstand(world: World, child: Entity, mis: Misunderstanding) -> None:
    child.memes["confused"] += 1
    child.memes["hurt"] += 1
    world.say(
        f'{child.id} thought the rhyme meant "{mis.heard_as}". '
        f"So {child.id} {mis.mistake}ed the dough until it {mis.harm}."
    )


def ruin(world: World, child: Entity, dough: Dough, site: Site) -> None:
    child.meters["tears"] += 1
    dough_ent = world.get("dough")
    dough_ent.meters["torn"] += 1
    dough_ent.meters["lost"] += 1
    site_entity = world.get("site")
    site_entity.meters["dim"] += 1
    world.say(
        f"The dough split like a dry leaf. The moon bowl stayed empty, and the shrine at {site.place} went quiet."
    )


def ending(world: World, elder: Entity, child: Entity, site: Site) -> None:
    world.say(
        f"For a while nobody spoke. Then {elder.id} knelt by {child.id} and said that a song must be heard with care."
    )
    world.say(
        f"The next dawn, {child.id} looked at the cracked dough on the stone and remembered the lesson: old words can guide the hands, or mislead them."
    )
    world.say(
        f"The village still sang the rhyme, but never as a rush again."
    )


def tell(site: Site, dough: Dough, rhyme: Rhyme, mis: Misunderstanding,
         child_name: str = "Mina", child_gender: str = "girl",
         elder_name: str = "Aunt Sera", elder_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_gender, role="elder"))
    site_ent = world.add(Entity(id="site", type="place", label=site.place))
    dough_ent = world.add(Entity(id="dough", type="thing", label=dough.label, attrs={"phrase": dough.phrase}))
    world.add(Entity(id="house", type="place", label="the house"))

    child.memes["hope"] = 1
    world.say(
        f"At {site.place}, under {site.sky}, {child.id} brought {dough.phrase} to the old shrine."
    )
    world.say(
        f"{site.old.capitalize()} stones circled the place, and the lanterns made the air seem almost holy."
    )
    world.say(
        f"{child.id} had come to knead the festival dough for the moon offering."
    )

    world.para()
    warn(world, elder, child, rhyme, mis)
    misunderstand(world, child, mis)
    make_bread(world, child, dough)
    propagate(world)

    world.para()
    ruin(world, child, dough, site)
    ending(world, elder, child, site)

    world.facts.update(
        child=child, elder=elder, site=site, dough=dough, rhyme=rhyme, misunderstanding=mis,
        outcome="bad_ending"
    )
    return world


SITES = {
    "shrine_hill": Site("shrine_hill", "the shrine hill", "old", "shrine", "a silver sky", {"myth"}),
    "temple_gate": Site("temple_gate", "the temple gate", "ancient", "temple", "a quiet sky", {"myth"}),
    "river_stone": Site("river_stone", "the river stones", "weathered", "river altar", "a blue dusk", {"myth"}),
}

DOUGHS = {
    "moonbread": Dough("moonbread", "moon dough", "soft moon flour and water", True, False, {"dough", "moon"}),
    "giftbread": Dough("giftbread", "offering dough", "sweet grain dough", True, True, {"dough", "offering"}),
}

RHYMES = {
    "steady": Rhyme("steady", "Knead it slow, let the moonlight grow", "careful hands make good bread", "steady", {"rhyme"}),
    "soft": Rhyme("soft", "Turn it, fold it, let it rest and hold", "gentle work keeps dough whole", "steady", {"rhyme"}),
}

MISUNDERSTANDINGS = {
    "hurry": Misunderstanding("hurry", "hurry", "hurr", "the dough would break", {"misunderstanding"}),
    "rush": Misunderstanding("rush", "rush", "rush", "the offering would fail", {"misunderstanding"}),
}


@dataclass
@dataclass
class StoryParams:
    site: str
    dough: str
    rhyme: str
    misunderstanding: str
    child_name: str
    child_gender: str
    elder_name: str
    elder_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, site in SITES.items():
        for did, dough in DOUGHS.items():
            for rid, rhyme in RHYMES.items():
                for mid, mis in MISUNDERSTANDINGS.items():
                    if reasonableness_gate(site, dough, rhyme, mis):
                        combos.append((sid, did, rid, mid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a myth-like story for a young child about kneading sacred dough, an old rhyme, and a mistake that spoils the offering.",
        f"Tell a story where {f['child'].id} kneads {f['dough'].label} while an elder speaks a rhyme, but the words are misunderstood.",
        "Write a small myth with a rhyme in it, a child who kneads dough, and a sad ending that teaches careful listening.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, elder, dough, rhyme, mis = f["child"], f["elder"], f["dough"], f["rhyme"], f["misunderstanding"]
    return [
        QAItem(
            question="What was the child trying to do?",
            answer=f"{child.id} was trying to knead the festival dough for the moon offering. The child wanted the old shrine to receive something worthy.",
        ),
        QAItem(
            question="What went wrong with the rhyme?",
            answer=f"The rhyme was heard the wrong way. {elder.id} meant to warn {child.id} to be careful, but the words sounded like a command to hurry.",
        ),
        QAItem(
            question="Why did the ending become sad?",
            answer=f"The dough was worked too hard and tore, so the offering could not be finished. That left the shrine quiet and the child disappointed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to knead dough?",
            answer="To knead dough means to press, fold, and squeeze it with your hands so it becomes smooth and ready to bake.",
        ),
        QAItem(
            question="Why can misunderstandings cause trouble?",
            answer="A misunderstanding happens when someone hears or thinks the wrong thing. Then they may do the wrong action, even if they meant to help.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a short verse with words that sound alike at the ends. People often use rhymes to remember old sayings.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("shrine_hill", "moonbread", "steady", "hurry", "Mina", "girl", "Aunt Sera", "woman"),
    StoryParams("temple_gate", "giftbread", "soft", "rush", "Kai", "boy", "Uncle Nilo", "man"),
]


ASP_RULES = r"""
valid(S,D,R,M) :- site(S), dough(D), rhyme(R), misunderstanding(M),
                  kneadable(D), steady_rhyme(R), bad_mis(M).

bad_ending :- misunderstanding_happens, dough_torn, shrine_dim.
misunderstanding_happens :- warning_given, child_confused.
dough_torn :- confusion, kneadable_dough.
shrine_dim :- bad_ending.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SITES:
        lines.append(asp.fact("site", sid))
    for did, d in DOUGHS.items():
        lines.append(asp.fact("dough", did))
        if d.kneadable:
            lines.append(asp.fact("kneadable", did))
    for rid, r in RHYMES.items():
        lines.append(asp.fact("rhyme", rid))
        if r.rhythm == "steady":
            lines.append(asp.fact("steady_rhyme", rid))
    for mid, m in MISUNDERSTANDINGS.items():
        lines.append(asp.fact("misunderstanding", mid))
        lines.append(asp.fact("bad_mis", mid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid_combos differ.")
    else:
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic storyworld about kneading dough, a rhyme, and a misunderstanding.")
    ap.add_argument("--site", choices=SITES)
    ap.add_argument("--dough", choices=DOUGHS)
    ap.add_argument("--rhyme", choices=RHYMES)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--name")
    ap.add_argument("--elder")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder-gender", choices=["woman", "man"])
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
              if (args.site is None or c[0] == args.site)
              and (args.dough is None or c[1] == args.dough)
              and (args.rhyme is None or c[2] == args.rhyme)
              and (args.misunderstanding is None or c[3] == args.misunderstanding)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    site, dough, rhyme, mis = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    elder_gender = args.elder_gender or rng.choice(["woman", "man"])
    name = args.name or rng.choice(["Mina", "Lio", "Anya", "Taro", "Suri", "Ivo"])
    elder = args.elder or rng.choice(["Aunt Sera", "Uncle Nilo", "Grandma Ila", "Old Vesh"])
    return StoryParams(site, dough, rhyme, mis, name, gender, elder, elder_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SITES[params.site], DOUGHS[params.dough], RHYMES[params.rhyme], MISUNDERSTANDINGS[params.misunderstanding], params.child_name, params.child_gender, params.elder_name, params.elder_gender)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible stories:")
        for item in asp_valid_combos():
            print(" ", item)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
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
