#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/passey_plenty_happy_ending_suspense_quest_fable.py
===================================================================================

A tiny standalone storyworld for a fable-like quest story with suspense and a
happy ending.  The world is built around a child, a careful guide, and a small
quest for a lost "passey" pouch that holds plenty of seeds for the village.

This script is self-contained and uses only the standard library plus the shared
story result containers from ``storyworlds/results.py``.
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SUSPENSE_RISE = 1.0


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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
class Place:
    id: str
    label: str
    dark: bool = False
    risky: bool = False
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
class QuestItem:
    id: str
    label: str
    phrase: str
    plenty: int
    useful_for: str
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
class Guide:
    id: str
    label: str
    calm: bool = True
    wisdom: int = 3
    text: str = ""
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
        self.path_seen: int = 0

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
        c.path_seen = self.path_seen
        return c


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


@dataclass
class Rule:
    name: str
    apply: callable

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


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["worry"] < THRESHOLD:
            continue
        sig = ("suspense", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["suspense"] += 1
        out.append("__suspense__")
    return out


def _r_plenty(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("quest_done") and not world.facts.get("plenty_spoken"):
        world.facts["plenty_spoken"] = True
        for k in list(world.entities.values()):
            if k.kind == "character":
                k.memes["joy"] += 1
        out.append("The pouch held plenty of seeds for the village gardens.")
    return out


CAUSAL_RULES = [
    Rule("suspense", _r_suspense),
    Rule("plenty", _r_plenty),
]


def reasonableness_gate(place: Place, item: QuestItem, guide: Guide) -> bool:
    return place.dark and item.plenty >= 1 and guide.wisdom >= 2


def predict_choice(world: World, place_id: str, item_id: str) -> dict:
    sim = world.copy()
    place = PLACES[place_id]
    item = ITEMS[item_id]
    sim.facts["place"] = place
    sim.facts["item"] = item
    sim.facts["quest_done"] = False
    _enter_path(sim, narrate=False)
    return {
        "lost": sim.path_seen >= 2 and place.dark,
        "found": sim.facts.get("quest_done", False),
    }


def _enter_path(world: World, narrate: bool = True) -> None:
    world.path_seen += 1
    hero = world.facts["hero"]
    guide = world.facts["guide"]
    place = world.facts["place"]
    hero.memes["worry"] += 1
    guide.memes["care"] += 1
    if narrate:
        world.say(
            f"{hero.id} and {guide.id} stepped into {place.label}, where the trees "
            f"stood close and the path grew quiet."
        )
    propagate(world, narrate=narrate)


def tell(place: Place, item: QuestItem, guide: Guide, hero_name: str, hero_type: str,
         guide_name: str, guide_type: str) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="quester"))
    helper = world.add(Entity(id=guide_name, kind="character", type=guide_type, role="guide"))
    pouch = world.add(Entity(id="pouch", kind="thing", type="pouch", label=item.label))
    world.facts.update(hero=hero, guide=helper, place=place, item=item, pouch=pouch)
    hero.memes["hope"] += 1
    helper.memes["calm"] += 1

    world.say(
        f"In a small village, {hero.id} heard a wise old tale: somewhere near "
        f"{place.label}, a lost {item.label} waited for the one brave enough to find it."
    )
    world.say(
        f"The little {hero.type} carried a {item.useful_for} in {item.phrase}, "
        f"and the old guide said there was plenty to share if the quest could be finished."
    )

    world.para()
    world.say(
        f"That evening, the sky went dim. {hero.id} looked at {guide.id} and asked, "
        f'"Will the way be hard?"'
    )
    hero.memes["worry"] += 1
    guide.memes["calm"] += 1
    predict = predict_choice(world, place.id, item.id)
    if predict["lost"]:
        world.say(
            f'{guide.id} nodded. "Only if you hurry and forget the markers. Stay close, '
            f'and we will not be lost."'
        )
    else:
        world.say(
            f'{guide.id} smiled. "We will watch for the markers and listen to the birds."'
        )
    world.facts["predict"] = predict

    world.para()
    _enter_path(world)
    world.say(
        f"The path turned past a brook, then under a thorny arch. For a moment, the "
        f"wind went still, and even the crickets seemed to hold their breath."
    )
    hero.memes["worry"] += 1
    helper.meters["watchfulness"] += 1
    propagate(world, narrate=False)

    world.say(
        f"At last, {hero.id} found the {item.label} tucked beside a root. "
        f"It was small, but it was safe, and it carried plenty."
    )
    world.facts["quest_done"] = True
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"{hero.id} carried the {item.label} home with {guide.id} beside {hero.pronoun()}."
    )
    world.say(
        f"That night the village shared the seeds, and the garden beds woke green in the morning light."
    )
    world.say(
        f"From then on, the people told the tale of {hero.id} and the passey pouch with plenty inside, "
        f"a quest that ended well because patience and care led the way."
    )

    world.facts["outcome"] = "happy"
    return world


PLACE_REGISTRY = {
    "woods": Place("woods", "the whispering woods", dark=True, risky=True, tags={"woods", "dark"}),
    "hill": Place("hill", "the moonlit hill", dark=True, risky=False, tags={"hill", "dark"}),
    "garden": Place("garden", "the garden path", dark=False, risky=False, tags={"garden"}),
}

ITEM_REGISTRY = {
    "passey": QuestItem("passey", "passey pouch", "a passey pouch", 3, "carry seeds", tags={"passey", "pouch", "quest"}),
    "plenty": QuestItem("plenty", "plenty basket", "a basket with plenty of room", 5, "carry gifts", tags={"plenty", "basket", "quest"}),
    "map": QuestItem("map", "little map", "a little map folded neatly", 2, "find the way", tags={"map", "quest"}),
}

GUIDE_REGISTRY = {
    "owl": Guide("owl", "old owl", True, 4, "wise and patient", tags={"owl", "wise"}),
    "grandmother": Guide("grandmother", "grandmother", True, 3, "kind and calm", tags={"family", "wise"}),
}

GIRL_NAMES = ["Mira", "Lina", "Tessa", "Nora", "Ava"]
BOY_NAMES = ["Perry", "Jules", "Milo", "Robin", "Theo"]


@dataclass
@dataclass
class StoryParams:
    place: str
    item: str
    guide: str
    hero: str
    hero_gender: str
    guide_name: str
    guide_gender: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (p, i, g)
        for p, place in PLACE_REGISTRY.items()
        for i, item in ITEM_REGISTRY.items()
        for g, guide in GUIDE_REGISTRY.items()
        if reasonableness_gate(place, item, guide)
    ]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like quest with suspense and a happy ending.")
    ap.add_argument("--place", choices=PLACE_REGISTRY)
    ap.add_argument("--item", choices=ITEM_REGISTRY)
    ap.add_argument("--guide", choices=GUIDE_REGISTRY)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--guide-name")
    ap.add_argument("--guide-gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.item is None or c[1] == args.item)
              and (args.guide is None or c[2] == args.guide)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, item, guide = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    guide_gender = args.guide_gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    guide_name = args.guide_name or rng.choice(GIRL_NAMES if guide_gender == "girl" else BOY_NAMES)
    return StoryParams(place, item, guide, hero, hero_gender, guide_name, guide_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable-like story that includes the words "passey" and "plenty".',
        f"Tell a suspenseful quest story where {f['hero'].id} goes to {f['place'].label} with a careful guide and finds something that brings plenty to the village.",
        f"Write a short happy-ending adventure about a lost passey pouch and a child who follows a wise guide instead of rushing ahead.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    guide = f["guide"]
    place = f["place"]
    item = f["item"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to find?",
            answer=f"{hero.id} was trying to find the {item.label}. It was the prize of the quest, and it mattered because it held plenty of seeds for the village."
        ),
        QAItem(
            question=f"Why was the story suspenseful?",
            answer=f"It felt suspenseful because the path into {place.label} was dark and quiet, so {hero.id} had to keep calm and stay close to {guide.id}. The silence made everyone wonder whether the way would be safe."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily. {hero.id} brought the passey pouch home, and the village shared the plenty inside it."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey to find something important or to finish a task. In stories, quests often involve brave choices and a goal to reach."
        ),
        QAItem(
            question="What does plenty mean?",
            answer="Plenty means a lot or more than enough. If there is plenty of something, people do not need to worry that it will run out quickly."
        ),
        QAItem(
            question="Why do careful guides help on a journey?",
            answer="Careful guides help because they notice the safe way and warn about danger. Their calm choices can keep a quest from turning into trouble."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for q in sample.prompts:
        lines.append(f"- {q}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    parts = ["--- world model state ---"]
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
        parts.append(f"  {e.id}: {' '.join(bits)}")
    parts.append(f"  fired={sorted(world.fired)}")
    return "\n".join(parts)


ASP_RULES = r"""
valid(P, I, G) :- place(P), item(I), guide(G), dark(P), plenty_item(I), wise(G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACE_REGISTRY.items():
        lines.append(asp.fact("place", pid))
        if p.dark:
            lines.append(asp.fact("dark", pid))
    for iid, i in ITEM_REGISTRY.items():
        lines.append(asp.fact("item", iid))
        if i.plenty >= 1:
            lines.append(asp.fact("plenty_item", iid))
    for gid, g in GUIDE_REGISTRY.items():
        lines.append(asp.fact("guide", gid))
        if g.wisdom >= 2:
            lines.append(asp.fact("wise", gid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


CURATED = [
    StoryParams("woods", "passey", "owl", "Mira", "girl", "Olive", "girl"),
    StoryParams("hill", "plenty", "grandmother", "Perry", "boy", "June", "girl"),
]


def asp_verify() -> int:
    import asp
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        return 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            print("MISMATCH: smoke test produced empty story.")
            return 1
    except Exception as exc:
        print(f"MISMATCH: generate/emit smoke test failed: {exc}")
        return 1
    print("OK: ASP parity and generate() smoke test passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACE_REGISTRY[params.place],
        ITEM_REGISTRY[params.item],
        GUIDE_REGISTRY[params.guide],
        params.hero,
        params.hero_gender,
        params.guide_name,
        params.guide_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q.question, q.answer) for q in story_qa(world)],
        world_qa=[QAItem(q.question, q.answer) for q in world_knowledge_qa(world)],
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
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible stories:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {idx+1}" if len(samples) > 1 else ""))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
