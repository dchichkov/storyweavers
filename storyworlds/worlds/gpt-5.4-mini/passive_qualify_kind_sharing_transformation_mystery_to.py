#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/passive_qualify_kind_sharing_transformation_mystery_to.py
=======================================================================================

A tiny, self-contained storyworld for a tall-tale-style mystery about
sharing, a curious transformation, and a kind discovery.

Premise:
- A child notices a puzzling change in a shared place.
- The change looks strange, but the children are kind and share what they know.
- They gather clues, solve the mystery, and the transformation ends up helping
  everyone.

This world is designed to satisfy the storyworld contract:
- stdlib only
- typed entities with meters and memes
- state-driven prose
- story-grounded QA and world-knowledge QA
- a Python reasonableness gate plus an inline ASP twin
- default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
    kind: str
    can_share: bool = True
    mystery: bool = True
    transformation: bool = True
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
class Change:
    id: str
    label: str
    cause: str
    reveal: str
    help_text: str
    solved_by: str
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
class Response:
    id: str
    sense: int
    text: str
    fail: str
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
@dataclass
class StoryParams:
    place: str
    change: str
    response: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    adult: str
    adult_gender: str
    trait: str
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


PLACES = {
    "orchard": Place("orchard", "the apple orchard", "outdoors", can_share=True, mystery=True, transformation=True, tags={"orchard", "apple"}),
    "barn": Place("barn", "the big red barn", "outdoors", can_share=True, mystery=True, transformation=True, tags={"barn"}),
    "dock": Place("dock", "the old river dock", "outdoors", can_share=True, mystery=True, transformation=True, tags={"dock", "river"}),
    "fair": Place("fair", "the county fair", "outdoors", can_share=True, mystery=True, transformation=True, tags={"fair"}),
}

CHANGES = {
    "golden_leaves": Change(
        "golden_leaves",
        "the leaves turning gold all at once",
        "the wind and sun",
        "The leaves had turned gold like coins in a storybook chest.",
        "the children shared their clues and looked up at the trees",
        "the orchard was ready for autumn",
        tags={"leaves", "gold", "autumn"},
    ),
    "singing_water": Change(
        "singing_water",
        "the river making a singing sound",
        "the stones under the water",
        "The water sang because it rushed over a shelf of smooth stones.",
        "the children shared the clues and followed the sound",
        "a hidden stone lip made a little waterfall",
        tags={"water", "river", "sound"},
    ),
    "sleepy_apple": Change(
        "sleepy_apple",
        "the apples changing from hard to sweet",
        "the warm days and cool nights",
        "The apples had changed from sour and hard to sweet and red.",
        "the children shared the fruit and watched the trees",
        "the orchard's apples were ripe at last",
        tags={"apple", "fruit", "sweet"},
    ),
    "bright_stripes": Change(
        "bright_stripes",
        "the barn boards growing bright stripes",
        "a spilled pail of paint",
        "The boards had been brushed with bright paint by mistake.",
        "the children shared the story and followed the wet tracks",
        "the old barn had been painted by a helpful neighbor",
        tags={"paint", "barn", "bright"},
    ),
}

RESPONSES = {
    "ask_kindly": Response(
        "ask_kindly",
        3,
        "asked the nearest grown-up in a kind voice and listened to the answer",
        "asked, but nobody nearby knew the trick",
        tags={"kind", "ask"},
    ),
    "share_clues": Response(
        "share_clues",
        3,
        "shared the clues with each other, then pieced the mystery together",
        "shared the clues, but they still could not solve the mystery",
        tags={"share", "clues"},
    ),
    "follow_tracks": Response(
        "follow_tracks",
        2,
        "followed the tracks and found the secret source of the change",
        "followed the tracks, but the trail ended too soon",
        tags={"tracks"},
    ),
}

GIRL_NAMES = ["Lily", "Mina", "June", "Ada", "Rose", "Nora", "Ivy", "Maya"]
BOY_NAMES = ["Tom", "Eli", "Noah", "Ben", "Max", "Theo", "Leo", "Sam"]
TRAITS = ["kind", "curious", "gentle", "brave", "thoughtful", "patient"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in PLACES.values():
        if not (place.can_share and place.mystery and place.transformation):
            continue
        for change_id, change in CHANGES.items():
            if place.kind == "outdoors" and ("barn" in change.tags and place.id != "barn"):
                continue
            combos.append((place.id, change_id))
    return combos


def default_response_id() -> str:
    return "share_clues"


def reasonableness_gate(place: Place, change: Change, response: Response) -> bool:
    return place.can_share and place.mystery and place.transformation and response.sense >= 2


def outcome_of(params: StoryParams) -> str:
    return "solved" if RESPONSES[params.response].sense >= 2 else "unsolved"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.can_share:
            lines.append(asp.fact("can_share", pid))
        if p.mystery:
            lines.append(asp.fact("mystery", pid))
        if p.transformation:
            lines.append(asp.fact("transformation", pid))
    for cid, c in CHANGES.items():
        lines.append(asp.fact("change", cid))
        for t in sorted(c.tags):
            lines.append(asp.fact("tag", cid, t))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, C) :- place(P), change(C), can_share(P), mystery(P), transformation(P).
solved(R) :- response(R), sense(R, S), S >= 2.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show solved/1."))
    return sorted(r for (r,) in asp.atoms(model, "solved"))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale mystery world about sharing and transformation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--change", choices=CHANGES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
    ap.add_argument("--adult")
    ap.add_argument("--trait", choices=TRAITS)
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid] or pool
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError("That response is too weak for this mystery.")
    combos = [c for c in valid_combos()
              if args.place in (None, c[0]) and args.change in (None, c[1])]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place_id, change_id = rng.choice(sorted(combos))
    response = args.response or default_response_id()
    g1 = rng.choice(["girl", "boy"])
    g2 = "boy" if g1 == "girl" and rng.random() < 0.5 else ("girl" if g1 == "boy" and rng.random() < 0.5 else rng.choice(["girl", "boy"]))
    adult_gender = rng.choice(["girl", "boy"])
    return StoryParams(
        place=place_id,
        change=change_id,
        response=response,
        child1=args.name1 or _pick_name(rng, g1),
        child1_gender=g1,
        child2=args.name2 or _pick_name(rng, g2, avoid=args.name1 or ""),
        child2_gender=g2,
        adult=args.adult or rng.choice(["Grandma", "Uncle Ben", "Aunt June", "Papa", "Mama"]),
        adult_gender=adult_gender,
        trait=args.trait or rng.choice(TRAITS),
    )


def _do_mystery(world: World, place: Entity, change: Change) -> None:
    place.meters["mystery"] += 1
    if change.id == "golden_leaves":
        place.meters["autumn"] += 1
    elif change.id == "singing_water":
        place.meters["sound"] += 1
    elif change.id == "sleepy_apple":
        place.meters["ripe"] += 1
    elif change.id == "bright_stripes":
        place.meters["painted"] += 1


def tell(params: StoryParams) -> World:
    world = World()
    place = world.add(Entity(params.place, kind="place", type="place", label=PLACES[params.place].label))
    c1 = world.add(Entity(params.child1, kind="character", type=params.child1_gender, role="solver", traits=[params.trait, "kind"]))
    c2 = world.add(Entity(params.child2, kind="character", type=params.child2_gender, role="helper", traits=["kind", "curious"]))
    adult = world.add(Entity(params.adult, kind="character", type=params.adult_gender, role="adult"))
    change = CHANGES[params.change]
    response = RESPONSES[params.response]

    c1.memes["curiosity"] += 1
    c2.memes["kindness"] += 1

    world.say(
        f"Down at {place.label}, {c1.id} and {c2.id} found something strange. "
        f"It was {change.label}, and nobody in the tall grass could quite explain it."
    )
    world.say(
        f"'{c1.id}!' said {c2.id}. 'Let's be kind and share what we notice before we guess.'"
    )
    world.para()
    world.say(
        f"The two children shared the clues like a pair of trail scouts sharing a lantern. "
        f"{change.reveal}"
    )
    _do_mystery(world, place, change)

    if response.id == "ask_kindly":
        world.say(
            f"{c1.id} asked {adult.id} in a kind voice, and {adult.id} smiled as if the whole valley had whispered the answer."
        )
        world.say(
            f"{adult.id} explained that {change.help_text} That kind answer turned the mystery into a neat little story."
        )
        solved = True
    elif response.id == "share_clues":
        world.say(
            f"The children shared every clue they had, and together they saw what had been hiding in plain sight."
        )
        world.say(
            f"{change.help_text} By sharing, they qualified as the sort of helpers who can solve a riddle without making a fuss."
        )
        solved = True
    else:
        world.say(
            f"They followed the tracks past the fence posts and the blackberry bushes, and the trail led straight to the answer."
        )
        world.say(
            f"{change.help_text} The mystery was solved because they kept their eyes open and walked on kindly."
        )
        solved = True

    world.para()
    c1.memes["joy"] += 1
    c2.memes["joy"] += 1
    place.meters["shared"] += 1
    if change.id == "bright_stripes":
        world.say(
            f"It turned out the barn's bright stripes were not a trick at all. A helpful neighbor had painted them for a fair sign, and the barn shone in the sun like it had learned a new song."
        )
    elif change.id == "singing_water":
        world.say(
            f"It turned out the river was singing because the stones taught it a tune, and the children could hear it from the dock clear as a bell."
        )
    elif change.id == "golden_leaves":
        world.say(
            f"It turned out the leaves were changing as autumn marched in on soft boots, and the orchard looked golden enough to make the moon blink."
        )
    else:
        world.say(
            f"It turned out the apples were simply ripening, sweetening in the warm days and cool nights, until the branches looked like they were holding red lanterns."
        )
    world.say(
        f"The children went home kind, happy, and wiser, with the mystery solved and the place changed in a way they could finally understand."
    )

    world.facts.update(
        place=place,
        children=(c1, c2),
        adult=adult,
        change=change,
        response=response,
        solved=solved,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c = f["change"]
    return [
        f'Write a tall-tale-style story about sharing clues, a strange transformation, and a mystery at {PLACES[f["place"].id].label}. Include the word "kind".',
        f"Tell a story where two children notice {c.label} and solve the mystery by sharing what they know.",
        f'Write a gentle mystery for children that includes the words "passive", "qualify", and "kind" in a natural way.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c1, c2 = f["children"]
    place: Entity = f["place"]
    change: Change = f["change"]
    response: Response = f["response"]
    items = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {c1.id} and {c2.id}, two kind children who noticed a strange change at {place.label}. They worked together instead of keeping the mystery to themselves.",
        ),
        QAItem(
            question="What was the mystery?",
            answer=f"The mystery was {change.label}. At first it looked puzzling, but the children shared clues and learned what had really happened.",
        ),
        QAItem(
            question="How did they solve it?",
            answer=f"They solved it by using {response.id.replace('_', ' ')} and by sharing what they saw with each other and with {f['adult'].id}. That kind teamwork let the answer come out plainly.",
        ),
    ]
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    change: Change = f["change"]
    place: Entity = f["place"]
    qa = []
    if "apple" in change.tags:
        qa.append(QAItem("What happens when apples ripen?", "Ripening apples change from hard and sour to sweet and ready to eat. They often grow redder or fuller as they ripen."))
    if "river" in change.tags or place.id == "dock":
        qa.append(QAItem("Why can a river sound different near rocks?", "Water can sing or gurgle when it rushes over rocks and shallow places. The stones change the way the water moves and sounds."))
    if "leaves" in change.tags:
        qa.append(QAItem("Why do leaves change color in autumn?", "In autumn, trees stop making as much green color, so other colors show through. That is why leaves can turn gold, orange, or red."))
    if "paint" in change.tags:
        qa.append(QAItem("Why can paint make boards look different?", "Paint coats the wood and gives it a new color. If someone paints boards, they can look bright and fresh."))
    qa.append(QAItem("What does it mean to be kind?", "Being kind means helping, sharing, and using gentle words and actions. Kind people try to make things better for others."))
    qa.append(QAItem("What does it mean to share clues?", "Sharing clues means telling the things you noticed so everyone can think together. It often helps solve puzzles faster."))
    return qa


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:12} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("orchard", "golden_leaves", "share_clues", "Lily", "girl", "Tom", "boy", "Grandma", "girl", "kind"),
    StoryParams("dock", "singing_water", "follow_tracks", "Eli", "boy", "Maya", "girl", "Uncle Ben", "boy", "curious"),
    StoryParams("barn", "bright_stripes", "ask_kindly", "Nora", "girl", "Sam", "boy", "Aunt June", "girl", "thoughtful"),
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def explain_rejection() -> str:
    return "(No story: that combination does not make a good sharing-and-transformation mystery.)"


def asp_verify() -> int:
    import asp
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH in valid_combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        rc = 1
    sens = set(asp_sensible())
    if sens == {r.id for r in RESPONSES.values() if r.sense >= 2}:
        print("OK: response sensibility matches.")
    else:
        print("MISMATCH in response sensibility.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, change) combos:")
        for p, c in combos:
            print(f"  {p:10} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child1} and {p.child2}: {p.change} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
