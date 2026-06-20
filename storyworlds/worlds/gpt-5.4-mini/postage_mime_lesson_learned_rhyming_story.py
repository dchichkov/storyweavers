#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/postage_mime_lesson_learned_rhyming_story.py
=============================================================================

A tiny standalone storyworld for a rhyming, lesson-learned tale about postage
and a mime.

Premise
-------
A child wants to send a letter by themselves. They see a mime at the post office
who seems to be helping without words, but a stamp-less envelope and a windy
mailbox cause a little trouble. A careful grown-up shows the child the proper
steps, and the child learns that postage matters.

This world keeps the story small and classical:
- typed entities with physical meters and emotional memes
- a simple causal model that drives the prose
- a safe, sensible turn into lesson learned
- Q&A grounded in world state rather than rendered English

The style aims for short, child-facing rhymes. It is not full poetry, but it
keeps a steady rhyme echo across lines and ends with a clear lesson image.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0, "lost": 0.0}
        if not self.memes:
            self.memes = {"hope": 0.0, "worry": 0.0, "pride": 0.0, "lesson": 0.0}

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
    rhyme: str
    has_wind: bool = False
    has_counter: bool = False

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
class Item:
    id: str
    label: str
    phrase: str
    type: str
    needs_postage: bool = True
    can_stay_put: bool = False

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
class Helper:
    id: str
    label: str
    phrase: str
    silent: bool = True

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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

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


PLACES = {
    "post_office": Place("post_office", "the post office", "glow and show", has_wind=False, has_counter=True),
    "corner_store": Place("corner_store", "the corner store", "bright and right", has_wind=False, has_counter=False),
    "mailbox": Place("mailbox", "the mailbox by the lane", "sway and play", has_wind=True, has_counter=False),
}

ITEMS = {
    "letter": Item("letter", "letter", "a little letter", "letter"),
    "card": Item("card", "postcard", "a bright postcard", "card"),
    "parcel": Item("parcel", "parcel", "a small parcel", "parcel"),
}

HELPERS = {
    "mime": Helper("mime", "mime", "a mime in a striped suit", silent=True),
    "clerk": Helper("clerk", "clerk", "the postal clerk", silent=False),
}

GROWNUPS = {
    "mom": {"type": "mother", "label": "mom"},
    "dad": {"type": "father", "label": "dad"},
}

CHILD_NAMES = ["Mina", "Noah", "Lena", "Theo", "Ari", "Ivy", "Owen", "Nia"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES.values():
        for item in ITEMS.values():
            for helper in HELPERS.values():
                if item.needs_postage and (place.has_counter or place.id == "post_office"):
                    combos.append((place.id, item.id, helper.id))
    return combos


@dataclass
@dataclass
class StoryParams:
    place: str
    item: str
    helper: str
    child: str
    child_gender: str
    grownup: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming postage-and-mime storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--grownup", choices=GROWNUPS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
              if (args.place is None or c[0] == args.place)
              and (args.item is None or c[1] == args.item)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, item, helper = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.name or rng.choice(CHILD_NAMES)
    grownup = args.grownup or rng.choice(list(GROWNUPS))
    return StoryParams(place, item, helper, child, gender, grownup)


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child"))
    grown = world.add(Entity(id="grownup", kind="character", type=GROWNUPS[params.grownup]["type"], label=GROWNUPS[params.grownup]["label"], role="grownup"))
    place = PLACES[params.place]
    item = ITEMS[params.item]
    helper = HELPERS[params.helper]
    mail = world.add(Entity(id="mail", type="mail", label=item.label))
    box = world.add(Entity(id="box", type="box", label="the mailbox"))
    child.memes["hope"] += 1

    world.say(
        f"{child.id} had a note to send with care, / at {place.label} with sunlight in the air."
    )
    world.say(
        f"There stood a {helper.label}, still and neat, / with painted white gloves and dancing feet."
    )
    world.para()
    world.say(
        f'{child.id} said, "I want this {item.label} to fly, / but I do not know the reason why."'
    )
    if place.id == "mailbox":
        world.say(
            f"The wind went whish and gave a puff, / and the mailbox looked a little rough."
        )
    else:
        world.say(
            f"The counter gleamed in a tidy row, / but the stamp was missing, oh no, oh no."
        )
    world.say(f"The mime just smiled and gave a wink, / then pointed where the postage should stick in ink.")
    child.memes["worry"] += 1

    world.para()
    world.say(
        f"{grown.label_word.capitalize()} came along with a gentle grin, / and said, "
        f'"First postage, then the mail goes in."'
    )
    mail.meters["lost"] += 1
    world.say(
        f"{child.id} found the stamp, and softly took aim, / and pressed it on straight, just the same."
    )
    child.memes["lesson"] += 1
    child.memes["pride"] += 1
    world.say(
        f"The mime tipped a hat, so quiet and sly, / as the letter went off with a do-or-die try."
    )
    world.say(
        f"Now {child.id} knew the lesson quite well: / no postage means pause, but with postage it sails."
    )

    world.facts.update(
        child=child, grownup=grown, place=place, item=item, helper=helper, mail=mail, box=box,
        outcome="learned", postage_used=True, missing_postage=True, wind=place.has_wind
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story for a young child that includes the words "{f["item"].label}" and "mime".',
        f"Tell a gentle lesson-learned rhyme where {f['child'].id} learns that postage matters before a letter can go.",
        f"Write a child-facing story in rhyme with a mime, a post office, and a clear lesson about sending mail.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    item = f["item"]
    place = f["place"]
    return [
        QAItem(
            question=f"What did {child.id} want to send?",
            answer=f"{child.id} wanted to send {item.phrase}. It was a small piece of mail, and it needed postage before it could go."
        ),
        QAItem(
            question="What did the child learn?",
            answer="The child learned that postage matters. A letter needs the stamp first, or it cannot properly begin its trip."
        ),
        QAItem(
            question=f"Who helped the child notice the mistake?",
            answer=f"A mime helped by pointing and acting it out. Then the grown-up explained the rule in a calm way."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is postage?",
            answer="Postage is the stamp or payment that lets mail be sent. It tells the post office the letter is ready for its trip."
        ),
        QAItem(
            question="What is a mime?",
            answer="A mime is a performer who tells a story with gestures and no words. Mimes often wear striped clothes and white face paint."
        ),
        QAItem(
            question="Why does mail need a stamp?",
            answer="Mail needs a stamp so the postal service knows it can be carried. The stamp is a tiny sign that the sending step is complete."
        ),
    ]


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
        print("--- world model state ---")
        for e in sample.list(world.entities.values()):
            print(f"  {e.id}: {e.type} meters={dict(e.meters)} memes={dict(e.memes)}")
    if qa:
        print()
        print("== (1) Generation prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== (2) Story questions ==")
        for q in sample.story_qa:
            print(f"Q: {q.question}\nA: {q.answer}")
        print("\n== (3) World questions ==")
        for q in sample.world_qa:
            print(f"Q: {q.question}\nA: {q.answer}")


ASP_RULES = r"""
valid(Place, Item, Helper) :- place(Place), item(Item), helper(Helper), needs_postage(Item), counter_place(Place).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.has_counter:
            lines.append(asp.fact("counter_place", pid))
    for iid, it in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if it.needs_postage:
            lines.append(asp.fact("needs_postage", iid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, item=None, helper=None, grownup=None, name=None, gender=None), random.Random(777)))
        assert sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        curated = [
            StoryParams("post_office", "letter", "mime", "Mina", "girl", "mom"),
            StoryParams("corner_store", "card", "mime", "Theo", "boy", "dad"),
            StoryParams("mailbox", "parcel", "clerk", "Ivy", "girl", "mom"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
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

    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
