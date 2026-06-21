#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pus_rhyme_fairy_tale.py
========================================================

A small fairy-tale storyworld with rhyme, a tiny medical worry, and a kind,
careful fix. The seed word is "pus"; the domain is a child in a fairy-tale
garden or woodland who gets a little sore with pus, then a gentle helper cleans
it, soothes the fear, and the day ends in a bright, safe image.

The world is intentionally small:
- a child explores a fairy-tale place,
- a prick or scrape can turn into an infected little wound,
- the child notices pus and feels worried,
- a healer or parent cleans the wound and adds salve and a bandage,
- the ending proves the change with relief and care.

It also supports a lightweight ASP twin, story-grounded QA, and JSON/trace
output in the shared Storyweavers style.
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
SOOTHE_MIN = 1.0
CLEAN_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "princess", "fairy"}
        male = {"boy", "father", "dad", "man", "prince", "wizard", "knight"}
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
    scene: str
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
class Wound:
    id: str
    label: str
    phrase: str
    source: str
    can_pus: bool = False
    severity: int = 1
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Remedy:
    id: str
    label: str
    phrase: str
    action: str
    power: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


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


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    wound = world.entities.get("wound")
    if not child or not wound:
        return out
    if wound.meters["infected"] >= THRESHOLD and ("fear",) not in world.fired:
        world.fired.add(("fear",))
        child.memes["fear"] += 1
        out.append("__fear__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if child and child.memes["healed"] >= THRESHOLD and ("relief",) not in world.fired:
        world.fired.add(("relief",))
        child.memes["relief"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("fear", _r_fear), Rule("relief", _r_relief)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def danger_at_risk(place: Place, wound: Wound) -> bool:
    return "garden" in place.tags or "woodland" in place.tags or wound.can_pus


def remedy_works(remedy: Remedy, wound: Wound) -> bool:
    return wound.can_pus and remedy.power >= wound.severity


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for wound_id, wound in WOUNDS.items():
            if not danger_at_risk(place, wound):
                continue
            for remedy_id, remedy in REMEDIES.items():
                if remedy_works(remedy, wound):
                    combos.append((place_id, wound_id, remedy_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale rhyme storyworld about a sore that needs care.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--wound", choices=WOUNDS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--name")
    ap.add_argument("--title", choices=["princess", "prince", "child"], default=None)
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


@dataclass
class StoryParams:
    place: str
    wound: str
    remedy: str
    name: str
    title: str
    seed: Optional[int] = None
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


def explain_rejection(place: Place, wound: Wound) -> str:
    return f"(No story: {place.label} does not give a fitting fairy-tale worry for the wound.)"


def explain_remedy(remedy: Remedy) -> str:
    return f"(Refusing remedy '{remedy.id}': it is too weak to clean the sore well enough.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.remedy and REMEDIES[args.remedy].power < 1:
        raise StoryError(explain_remedy(REMEDIES[args.remedy]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.wound is None or c[1] == args.wound)
              and (args.remedy is None or c[2] == args.remedy)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, wound, remedy = rng.choice(sorted(combos))
    title = args.title or rng.choice(["princess", "prince", "child"])
    name = args.name or rng.choice(["Mira", "Pip", "Lina", "Jasper", "Nell", "Tobin"])
    return StoryParams(place=place, wound=wound, remedy=remedy, name=name, title=title)


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def tell(place: Place, wound: Wound, remedy: Remedy, title: str = "child", name: str = "Mira") -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=title, label=name, role="hero", traits=["gentle"]))
    helper = world.add(Entity(id="helper", kind="character", type="fairy", label="the kindly healer", role="healer"))
    wound_ent = world.add(Entity(id="wound", kind="thing", type="wound", label=wound.label, attrs={"source": wound.source}))
    world.facts["place"] = place
    world.facts["wound_cfg"] = wound
    world.facts["remedy"] = remedy
    world.facts["child"] = child
    world.facts["helper"] = helper
    world.facts["wound"] = wound_ent

    child.memes["wonder"] += 1
    world.say(f"In {place.label}, where roses leaned and moonbeams swayed, {name} walked where bright bees played.")
    world.say(f"{name} sang a little fairy song, for every path was silver-bright and every bird could trill along.")
    world.say(f"But near a thorn of briar and rose, a tiny prick hurt {child.pronoun('possessive')} toes.")
    world.say(f"{name} looked down and saw a sore; the little place had pus, and that meant it needed care once more.")

    world.para()
    wound_ent.meters["infected"] += 1
    child.memes["worry"] += 1
    propagate(world, narrate=False)
    world.say(f'"Oh dear," said {name}, "this spot is sore; I do not like this pus at all, or what it means for sure."')
    world.say(f"The child called out in voice so clear, and soon the kindly healer came near and near.')

    world.para()
    if remedy_works(remedy, wound):
        wound_ent.meters["clean"] += 1
        wound_ent.meters["infected"] = 0
        child.memes["healed"] += 1
        world.say(f"The healer washed the hurt with care, and brushed away the pus with warm water and gentle air.")
        world.say(f"{helper.label_word.capitalize()} dabbed on {remedy.phrase}, then tied a little bandage snug and fair.")
        world.say(f'"There now," the healer said with cheer, "small hurts can fade when hands are kind and clear."')
        world.para()
        world.say(f"{name} smiled and skipped back light; the sore grew calm, and the bandage gleamed in morning light.")
        world.say(f"In {place.label}, the petals swayed, and {name} went home feeling brave and stayed unafraid.")
    else:
        world.say(f"The healer tried, but could not mend the sore, and worried that the pus would only bring more.")
        world.say(f"{name} had to rest and keep the wound dry, while the fairy lantern blinked like a watchful eye.")
        world.para()
        world.say(f"So the lesson came: when a hurt turns red, call a grown-up fast and care for it in bed.")

    world.facts["outcome"] = "healed" if wound_ent.meters["clean"] else "rested"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c, w, r, p = f["child"], f["wound_cfg"], f["remedy"], f["place"]
    return [
        f'Write a fairy-tale story in rhyme for a child named {c.label} in {p.label} that includes the word "pus".',
        f"Tell a gentle rhyming story where {c.label} finds a sore with pus and a kindly helper uses {r.label} to help.",
        f'Write a small fairy tale about a sore, a healer, and the word "pus", ending with a safe, bright feeling.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c, w, r, p = f["child"], f["wound_cfg"], f["remedy"], f["place"]
    qa = [
        QAItem(question="Who is the story about?", answer=f"It is about {c.label} in {p.label}, a little fairy-tale traveler who needs help with a sore."),
        QAItem(question="What did the child notice?", answer=f"{c.label} noticed a sore that had pus, so the child knew it needed gentle care. That was the turning point that brought the healer to the scene."),
        QAItem(question="How did the helper fix the problem?", answer=f"The kindly healer washed the sore and used {r.label}. That cleaned the hurt and helped the child feel safe again."),
        QAItem(question="How did the story end?", answer=f"It ended with calm and comfort: the sore was cleaned, the bandage was on, and {c.label} could go on smiling."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(question="What is pus?", answer="Pus is a thick sign that a sore may be infected. It means a hurt should be cleaned and watched by a grown-up."),
        QAItem(question="What does a bandage do?", answer="A bandage covers a small hurt and helps keep it clean while it heals."),
        QAItem(question="What should you do when a sore looks infected?", answer="Tell a grown-up or healer right away, so the wound can be cleaned and cared for before it gets worse."),
    ]
    return out


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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


PLACES = {
    "rose_garden": Place(id="rose_garden", label="the rose garden", scene="roses and dew", tags={"garden"}),
    "moon_wood": Place(id="moon_wood", label="the moonlit wood", scene="silver trees", tags={"woodland"}),
    "castle_hall": Place(id="castle_hall", label="the castle hall", scene="golden banners", tags={"castle"}),
}

WOUNDS = {
    "thorn_prick": Wound(id="thorn_prick", label="a thorn prick", phrase="a tiny thorn prick", source="a briar thorn", can_pus=True, severity=1, tags={"pus", "hurt"}),
    "scrape": Wound(id="scrape", label="a scrape", phrase="a little scrape", source="a rough stone", can_pus=True, severity=1, tags={"pus", "hurt"}),
    "festered_spot": Wound(id="festered_spot", label="a festered spot", phrase="a festered spot", source="a scratch left alone", can_pus=True, severity=2, tags={"pus", "hurt"}),
}

REMEDIES = {
    "wash": Remedy(id="wash", label="warm water", phrase="warm water", action="wash", power=1, tags={"clean"}),
    "salve": Remedy(id="salve", label="healing salve", phrase="healing salve", action="dab", power=2, tags={"heal"}),
    "honey": Remedy(id="honey", label="sweet honey salve", phrase="sweet honey salve", action="smooth", power=2, tags={"heal"}),
}

CURATED = [
    StoryParams(place="rose_garden", wound="thorn_prick", remedy="salve", name="Mira", title="princess"),
    StoryParams(place="moon_wood", wound="scrape", remedy="wash", name="Pip", title="child"),
    StoryParams(place="castle_hall", wound="festered_spot", remedy="honey", name="Nell", title="princess"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for wid, w in WOUNDS.items():
        lines.append(asp.fact("wound", wid))
        if w.can_pus:
            lines.append(asp.fact("can_pus", wid))
        lines.append(asp.fact("severity", wid, w.severity))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("power", rid, r.power))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,W,R) :- place(P), wound(W), remedy(R), can_pus(W), power(R, Pow), severity(W, Sev), Pow >= Sev.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    a = set(asp_valid_combos())
    b = set(valid_combos())
    rc = 0
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and Python valid_combos():")
        if a - b:
            print("  only in clingo:", sorted(a - b))
        if b - a:
            print("  only in python:", sorted(b - a))
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, wound=None, remedy=None, name=None, title=None), random.Random(7)))
        _ = sample.story
        print("OK: normal generation smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def generate(params: StoryParams) -> StorySample:
    for key, table in (("place", PLACES), ("wound", WOUNDS), ("remedy", REMEDIES)):
        if getattr(params, key) not in table:
            raise StoryError(f"Invalid {key}: {getattr(params, key)!r}")
    world = tell(PLACES[params.place], WOUNDS[params.wound], REMEDIES[params.remedy], params.title, params.name)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
