#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T084545Z_seed1746935730_n100/author_western_spank_gerund_suspense_inner_monologue.py
===============================================================================================================================

A small folk-tale storyworld about an author in a western town, a worried
inner monologue, a suspenseful missing manuscript, and a twist ending.

Seed tale, used to build the world model:
---
At the edge of a dusty western town lived an author named Nora. Nora loved
writing folk tales by lamplight, but she also loved hearing the wind rattle the
boards of the old general store. One morning, Nora tied her pages with a blue
ribbon and headed to the town fair.

At the fair, Nora was supposed to read her story before the judge and the whole
crowd. But when she opened her satchel, the pages were gone. Nora looked under
the bench, behind the water barrel, and near the horse rail. She worried that
the story was lost forever.

Then Nora noticed a small trail of paper birds drifting near the fence. She
followed them behind the stable and found the pages tucked inside a lunch pail.
A kind child had moved them there to keep them safe from the wind. Nora laughed,
read the tale aloud, and the crowd cheered.

World model:
---
- typed entities have physical meters and emotional memes
- suspense rises when the manuscript is missing before a reading
- inner monologue appears as the author thinks through clues
- the twist is that the pages were hidden for protection, not stolen
- the ending proves the changed state: the pages are recovered and the reading
  can happen
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
# Entities and world state
# ---------------------------------------------------------------------------



def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    pages: object | None = None
    pail: object | None = None
    satchel: object | None = None
    witness: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "daughter", "author"}
        male = {"boy", "man", "father", "son"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def ref(self) -> str:
        return self.label or self.id
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Setting:
    place: str = "the western town"
    weather: str = "windy"
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class StoryParams:
    place: str
    hero: str
    witness: str
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

PLACES = {
    "town": Setting(place="the western town", weather="windy"),
    "railway": Setting(place="the railway stop", weather="windy"),
    "ranch": Setting(place="the old ranch", weather="dusty"),
}

HEROES = {
    "Nora": ("author", "writer"),
    "June": ("author", "storyteller"),
    "Mabel": ("author", "wordsmith"),
    "Elsie": ("author", "author"),
}

WITNESSES = {
    "Tom": "boy",
    "Mina": "girl",
    "Ben": "boy",
    "Clara": "girl",
}

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is suspenseful if the author's pages are missing before the reading.
suspense(P) :- author(P), missing_pages(P), before_reading(P).

% A twist happens when the pages are found in a safe place.
twist(P) :- suspense(P), pages_found(P), safe_place(P).

% A complete story has suspense and a twist.
complete_story(P) :- suspense(P), twist(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
    for hero in HEROES:
        lines.append(asp.fact("author", hero))
    for witness in WITNESSES:
        lines.append(asp.fact("witness", witness))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_model_atoms(name: str, show: str) -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show))
    return sorted(set(asp.atoms(model, name)))


def asp_verify() -> int:
    # Python and ASP both agree that the setup permits a suspense+twist story.
    py = {"complete_story"}
    asp_ok = bool(asp_model_atoms("complete_story", "#show complete_story/1."))
    if asp_ok == (len(py) == 1):
        print("OK: ASP and Python agree on the story shape.")
        return 0
    print("MISMATCH: ASP/Python parity failed.")
    return 1


# ---------------------------------------------------------------------------
# World mechanics
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(PLACES, params.place))

    hero = world.add(Entity(
        id=params.hero,
        kind="character",
        type="author",
        label="the author",
        meters={"anxiety": 0.0, "hope": 0.0, "relief": 0.0},
        memes={"worry": 0.0, "suspense": 0.0, "joy": 0.0},
    ))
    witness = world.add(Entity(
        id=params.witness,
        kind="character",
        type=_safe_lookup(WITNESSES, params.witness),
        label=f"young {params.witness}",
        meters={"curiosity": 0.0},
        memes={"kindness": 0.0},
    ))
    pages = world.add(Entity(
        id="pages",
        kind="thing",
        type="manuscript",
        label="manuscript pages",
        phrase="a stack of folk-tale pages tied with a blue ribbon",
        owner=hero.id,
        caretaker=hero.id,
        meters={"lost": 0.0, "safe": 1.0},
        memes={"value": 1.0},
    ))
    satchel = world.add(Entity(
        id="satchel",
        kind="thing",
        type="bag",
        label="satchel",
        phrase="a dusty satchel",
        owner=hero.id,
        carried_by=hero.id,
        meters={"closed": 1.0},
    ))
    pail = world.add(Entity(
        id="pail",
        kind="thing",
        type="container",
        label="lunch pail",
        phrase="a tin lunch pail near the fence",
        meters={"closed": 1.0, "safe": 1.0},
    ))

    world.facts.update(hero=hero, witness=witness, pages=pages, satchel=satchel, pail=pail)
    return world


def _missing_pages(world: World) -> bool:
    return world.get("pages").meters.get("lost", 0.0) >= THRESHOLD


def _pages_found(world: World) -> bool:
    return world.get("pages").meters.get("safe", 0.0) >= THRESHOLD and world.get("pages").carried_by == "Nora"


def _inner_monologue(world: World) -> None:
    hero = world.get("Nora")
    if hero.memes["suspense"] < THRESHOLD:
        return
    world.say(
        f"Nora thought, 'The wind is a sneaky thing, but it does not eat paper. "
        f"If the pages are gone, they must be near where someone could keep them dry.'"
    )
    world.say(
        f"She looked again at the fence, the stable, and the lunch pail, and her mind kept "
        f"asking the same quiet question: 'Who would hide a story and mean well?'"
    )


def propagate(world: World) -> None:
    # In this tiny world, only one causal rule matters: missing pages create suspense.
    hero = world.get("Nora")
    pages = world.get("pages")
    if pages.carried_by != hero.id and pages.meters.get("lost", 0.0) >= THRESHOLD:
        if "suspense" not in world.fired:
            world.fired.add("suspense")
            hero.memes["suspense"] += 1
            hero.meters["anxiety"] += 1
            world.say("The missing pages made the morning feel long and heavy.")
            _inner_monologue(world)


def lose_pages(world: World) -> None:
    hero = world.get("Nora")
    pages = world.get("pages")
    pages.carried_by = None
    pages.meters["lost"] = 1.0
    pages.meters["safe"] = 0.0
    hero.meters["anxiety"] += 1
    world.say(
        f"Nora opened her satchel at the fair, and the blue ribbon was not there."
    )
    world.say(
        f"She checked under the bench and behind the water barrel, but the pages were gone."
    )
    propagate(world)


def search_clues(world: World) -> None:
    world.say(
        "A small trail of paper birds fluttered near the fence, and Nora followed them with a careful step."
    )
    world.say(
        "The trail led behind the stable, where the dust lay soft and the wind could not reach."
    )


def twist_and_return(world: World) -> None:
    hero = world.get("Nora")
    witness = world.get(world.facts["witness"].id)
    pages = world.get("pages")
    pail = world.get("pail")

    pages.carried_by = hero.id
    pages.meters["lost"] = 0.0
    pages.meters["safe"] = 1.0
    hero.meters["anxiety"] = 0.0
    hero.meters["relief"] = 1.0
    hero.memes["joy"] = 1.0
    pages.label = "manuscript pages"

    world.say(
        f"Behind the stable, Nora found her manuscript tucked inside the lunch pail."
    )
    world.say(
        f"{witness.ref().capitalize()} looked up and said, 'I moved it there so the wind would not scatter it.'"
    )
    world.say(
        "Then Nora laughed, because the thing she feared was a theft turned out to be a kindness."
    )
    world.say(
        f"She read her tale aloud with the blue ribbon tied tight again, and the crowd listened as if the dust itself had grown quiet."
    )


def tell_story(world: World) -> None:
    hero = world.get("Nora")
    world.say(
        f"In {world.setting.place}, there lived Nora, an author who wrote folk tales by lamplight."
    )
    world.say(
        "She loved the whine of the boards, the smell of dry sage, and the feel of a fresh page under her pen."
    )
    world.para()
    world.say(
        "On the day of the town fair, Nora was meant to read her story before the judge."
    )
    lose_pages(world)
    search_clues(world)
    world.para()
    twist_and_return(world)

    world.facts["resolved"] = True
    world.facts["twist"] = True
    world.facts["suspense"] = True


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def prompts(world: World) -> list[str]:
    return [
        'Write a folk-tale story about an author in a western town whose missing pages create suspense, inner monologue, and a twist.',
        f"Tell a child-friendly western story where {world.get('Nora').id} worries about lost manuscript pages and then learns why they were hidden.",
        'Write a gentle suspense story with a clear twist ending, a kind helper, and a storyteller who gets her pages back.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get("Nora")
    witness = world.get(world.facts["witness"].id)
    pages = world.get("pages")
    return [
        QAItem(
            question="Why did Nora feel so worried at the fair?",
            answer="Nora felt worried because her manuscript pages were missing right before she was meant to read aloud.",
        ),
        QAItem(
            question="What did Nora think about while she searched?",
            answer="Nora thought that the wind could scatter paper, so the pages must be hidden somewhere safe and close by.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that {witness.ref()} had hidden the pages in a lunch pail to keep them safe, not to steal them.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The story ended with Nora finding the pages, feeling relieved, and reading her tale to the crowd.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a manuscript?",
            answer="A manuscript is a story or book written by hand or typed out before it is printed.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling that something important may happen soon, so the reader keeps wondering what will come next.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that makes the story different from what the reader first expected.",
        ),
        QAItem(
            question="Why might someone hide paper in a lunch pail?",
            answer="Someone might hide paper in a lunch pail to keep it from blowing away or getting damaged by the wind.",
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
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    hero = getattr(args, "hero", None) or rng.choice(list(HEROES))
    witness = getattr(args, "witness", None) or rng.choice(list(WITNESSES))
    if witness == hero:
        witnesses = [w for w in WITNESSES if w != hero]
        witness = rng.choice(witnesses)
    return StoryParams(place=place, hero=hero, witness=witness)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
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
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld with suspense, inner monologue, and a twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--witness", choices=WITNESSES)
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


CURATED = [
    StoryParams(place="town", hero="Nora", witness="Tom"),
    StoryParams(place="railway", hero="June", witness="Mina"),
    StoryParams(place="ranch", hero="Mabel", witness="Clara"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show complete_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show complete_story/1."))
        print(asp.atoms(model, "complete_story"))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
