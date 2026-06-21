#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gamma_drum_tremble_suspense_mystery_to_solve.py
=================================================================================

A tiny nursery-rhyme storyworld about a missed drumbeat, a trembling trail,
and a little mystery solved by a child with a bright gamma lamp.

The seed words are woven into a child-facing, suspenseful rhyme:
- gamma
- drum
- tremble

The premise is simple: a child hears a drum go missing, follows a trembling clue,
and solves the mystery by noticing where the sound was hiding. The world model
tracks physical meters and emotional memes so the turn and ending are state-driven,
not just swapped nouns in a frozen paragraph.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Drum:
    id: str
    label: str
    sound: str
    hiding: str
    clue: str
    rattle: str
    makes_noise: bool = True
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
class Lamp:
    id: str
    label: str
    glow: str
    phrase: str
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
class Place:
    id: str
    label: str
    shadow: str
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
    drum: str
    lamp: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
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


def _r_tremble(world: World) -> list[str]:
    out: list[str] = []
    if world.get("drum").meters["hidden"] < THRESHOLD:
        return out
    if "child" in world.entities:
        child = world.get("child")
        if child.memes["worry"] < THRESHOLD:
            child.memes["worry"] += 1
            world.get("place").meters["mystery"] += 1
            out.append("__tremble__")
    return out


def _r_answer(world: World) -> list[str]:
    out: list[str] = []
    drum = world.get("drum")
    if drum.meters["found"] >= THRESHOLD and "lamp" in world.entities:
        lamp = world.get("lamp")
        if lamp.meters["glow"] < THRESHOLD:
            lamp.meters["glow"] += 1
            out.append("__glow__")
    return out


RULES = [Rule("tremble", _r_tremble), Rule("answer", _r_answer)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonable_combo(place: Place, drum: Drum, lamp: Lamp) -> bool:
    return "shadowy" in place.tags and "noise" in drum.tags and "light" in lamp.tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for did, drum in DRUMS.items():
            for lid, lamp in LAMPS.items():
                if reasonable_combo(place, drum, lamp):
                    combos.append((pid, did, lid))
    return combos


def explain_rejection(place: Place, drum: Drum, lamp: Lamp) -> str:
    return (
        f"(No story: this place and clue set does not make a real mystery. "
        f"The rhyme needs a shadowy place, a noisy drum clue, and a light to help solve it.)"
    )


def tell(place: Place, drum: Drum, lamp: Lamp, hero_name: str, hero_gender: str,
         friend_name: str, friend_gender: str) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    place_ent = world.add(Entity(id="place", kind="thing", type="place", label=place.label))
    drum_ent = world.add(Entity(id="drum", kind="thing", type="drum", label=drum.label))
    lamp_ent = world.add(Entity(id="lamp", kind="thing", type="lamp", label=lamp.label))
    world.facts["place"] = place
    world.facts["drum_cfg"] = drum
    world.facts["lamp_cfg"] = lamp

    hero.memes["curiosity"] += 1
    friend.memes["caution"] += 1

    world.say(
        f"In {place.label}, where the soft dark waited, {hero.id} and {friend.id} went to play."
    )
    world.say(
        f'But hush-aby-hush, the {drum.label} was gone. "Where can the {drum.label} hide?" said {hero.id}.'
    )
    world.para()
    world.say(
        f"{friend.id} heard a tiny {drum.clue}, a little {drum.rattle} in the shadow. "
        f"{friend.id} began to tremble, for the clue felt secret and small."
    )
    hero.memes["worry"] += 1
    world.get("drum").meters["hidden"] = 1
    propagate(world, narrate=False)

    world.say(
        f'{hero.id} held up a {lamp.label} and let it {lamp.glow}. '
        f'"A gamma glow can guide us," {hero.id} said, and tiptoed near the hushy wall.'
    )

    world.para()
    world.say(
        f"They looked high, they looked low, they looked under a chair and behind a show."
    )
    world.say(
        f"Then {hero.id} saw the answer at last: the {drum.label} was tucked in {drum.hiding}."
    )
    world.get("drum").meters["found"] = 1
    world.get("drum").meters["hidden"] = 0
    propagate(world, narrate=False)

    world.say(
        f'{friend.id} gave a little laugh, and the trembling went away. '
        f'The {drum.label} went "boom-boom-boom," and the room felt bright and sweet.'
    )
    world.say(
        f"Now the mystery was solved, and the gamma lamp shone warm while the {drum.label} sang in time."
    )

    world.facts.update(
        hero=hero, friend=friend, place_ent=place_ent, drum_ent=drum_ent, lamp_ent=lamp_ent,
        outcome="solved", hidden=bool(drum_ent.meters["hidden"] >= THRESHOLD),
    )
    return world


PLACES = {
    "hall": Place(id="hall", label="the shadowy hall", shadow="soft shadows", tags={"shadowy"}),
    "attic": Place(id="attic", label="the shadowy attic", shadow="dusty shadows", tags={"shadowy"}),
    "garden_shed": Place(id="shed", label="the shadowy shed", shadow="long shadows", tags={"shadowy"}),
}

DRUMS = {
    "toy_drum": Drum(
        id="toy_drum", label="toy drum", sound="boom-boom", hiding="a wooden crate",
        clue="tap-tap", rattle="tap-tap", tags={"noise", "drum"},
    ),
    "little_drum": Drum(
        id="little_drum", label="little drum", sound="rat-a-tat", hiding="a basket of scarves",
        clue="rat-a-tat", rattle="rat-a-tat", tags={"noise", "drum"},
    ),
}

LAMPS = {
    "gamma_lamp": Lamp(
        id="gamma_lamp", label="gamma lamp", glow="glow like a star", phrase="a gamma lamp", tags={"light", "gamma"}
    ),
    "night_lamp": Lamp(
        id="night_lamp", label="night lamp", glow="shine like honey", phrase="a night lamp", tags={"light"}
    ),
}


CURATED = [
    StoryParams(place="hall", drum="toy_drum", lamp="gamma_lamp", hero_name="Lily", hero_gender="girl", friend_name="Milo", friend_gender="boy"),
    StoryParams(place="attic", drum="little_drum", lamp="gamma_lamp", hero_name="Nora", hero_gender="girl", friend_name="Pip", friend_gender="boy"),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme mystery story in {f["place"].label} that includes the words gamma, drum, and tremble.',
        f"Tell a suspenseful child story where {f['hero'].id} follows a clue to find the missing {f['drum_cfg'].label}.",
        "Write a gentle rhyme about a hidden drum, a trembling clue, and a bright lamp that helps solve the mystery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    drum = f["drum_cfg"]
    place = f["place"]
    return [
        QAItem(
            question="What was the mystery?",
            answer=f"The mystery was where the {drum.label} had gone. It was hidden in {drum.hiding}, so the children had to follow the clue carefully."
        ),
        QAItem(
            question="Why did the friend tremble?",
            answer=f"{friend.id} trembled because the clue felt secret and spooky in {place.label}. The dark made the search feel suspenseful until the lamp shone."
        ),
        QAItem(
            question="How was the mystery solved?",
            answer=f"{hero.id} used the gamma lamp to look through the shadows and found the {drum.label}. After that, the drum could make its happy sound again."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a lamp do in the dark?",
            answer="A lamp gives light so people can see shapes, corners, and clues in the dark."
        ),
        QAItem(
            question="What is a drum for?",
            answer="A drum makes a beat when you tap it. People use drums to keep time and make music."
        ),
        QAItem(
            question="Why does a mystery feel suspenseful?",
            answer="A mystery feels suspenseful when you do not know the answer yet. The waiting makes every clue feel important."
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
shadowy(P) :- place(P).
mystery_possible(P,D,L) :- shadowy(P), drum(D), lamp(L).
solve :- mystery_possible(P,D,L), place(P), drum(D), lamp(L).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for did in DRUMS:
        lines.append(asp.fact("drum", did))
    for lid in LAMPS:
        lines.append(asp.fact("lamp", lid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python combo checks differ.")
    else:
        print(f"OK: ASP and Python combo checks match ({len(valid_combos())} combos).")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: smoke test story generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"MISMATCH: smoke test failed: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a nursery-rhyme mystery about gamma, drum, and tremble."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--drum", choices=DRUMS)
    ap.add_argument("--lamp", choices=LAMPS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
              and (args.drum is None or c[1] == args.drum)
              and (args.lamp is None or c[2] == args.lamp)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, drum, lamp = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero_name = args.hero_name or rng.choice(["Lily", "Nora", "Mia", "Ava", "Rose"])
    friend_name = args.friend_name or rng.choice(["Pip", "Milo", "Ben", "Theo", "Finn"])
    return StoryParams(
        place=place, drum=drum, lamp=lamp,
        hero_name=hero_name, hero_gender=hero_gender,
        friend_name=friend_name, friend_gender=friend_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.drum not in DRUMS or params.lamp not in LAMPS:
        raise StoryError("(Invalid story params.)")
    world = tell(PLACES[params.place], DRUMS[params.drum], LAMPS[params.lamp],
                 params.hero_name, params.hero_gender, params.friend_name, params.friend_gender)
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
        print(f"{len(combos)} compatible (place, drum, lamp) combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
