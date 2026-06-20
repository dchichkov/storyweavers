#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/jujube_macaw_peel_gerund_magic_mystery.py
=========================================================================

A small, standalone story world for a magical mystery with:
- a jujube
- a macaw
- a peel-gerund action
- a child-facing mystery turn
- a gentle magical reveal

The world is built as a causal simulation, not a frozen paragraph. State changes
drive the prose, the QA, and the verification checks.
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
SENSE_MIN = 2


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
    magical: bool = False
    clue: bool = False
    hidden: bool = False

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
    mood: str
    hiding_spot: str
    can_shuffle: bool = True

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
    role: str
    magical: bool = False
    clue: bool = False

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
class Spell:
    id: str
    label: str
    sense: int
    reveal: int
    text: str
    fail_text: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


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


def _r_mystic_shuffle(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["shuffled"] < THRESHOLD:
            continue
        sig = ("shuffle", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("room").memes["curious"] += 1
        out.append("__shuffle__")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    clue = world.entities.get("clue")
    if not clue:
        return out
    if clue.meters["revealed"] < THRESHOLD:
        return out
    sig = ("reveal", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("child").memes["wonder"] += 1
    out.append("__reveal__")
    return out


CAUSAL_RULES = [
    Rule("shuffle", "mystery", _r_mystic_shuffle),
    Rule("reveal", "magic", _r_reveal),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def spell_power(spell: Spell, delay: int) -> int:
    return spell.reveal - delay


def is_revealed(spell: Spell, delay: int) -> bool:
    return spell_power(spell, delay) >= 1


def suspicious_shuffle(place: Place, item: Item) -> bool:
    return place.can_shuffle and item.clue


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for iid, item in ITEMS.items():
            for sid, spell in SPELLS.items():
                if suspicious_shuffle(place, item) and item.magical and spell.sense >= SENSE_MIN:
                    combos.append((pid, iid, sid))
    return combos


@dataclass
@dataclass
class StoryParams:
    place: str
    item: str
    spell: str
    child: str
    child_gender: str
    parent: str
    delay: int = 0
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


def setup(world: World, child: Entity, parent: Entity, item: Entity, place: Place) -> None:
    child.memes["hope"] += 1
    world.say(
        f"On a quiet afternoon, {child.id} and {parent.label_word} searched {place.label}. "
        f"The air felt {place.mood}, and {item.label} looked like it was waiting for a secret."
    )
    world.say(
        f"{child.id} found {item.phrase} near {place.hiding_spot} and frowned. "
        f'"Something is odd," {child.id} said.'
    )


def peel_and_search(world: World, child: Entity, item: Entity, place: Place) -> None:
    child.memes["determined"] += 1
    item.meters["peeled"] += 1
    world.say(
        f"{child.id} started {place.hiding_spot.replace('the ', 'the ').rstrip()} and kept {item.role}ing, "
        f"peel-gerund by peel-gerund, until the strange little trail felt important."
    )


def warn(world: World, parent: Entity, child: Entity, item: Entity, spell: Spell) -> None:
    world.say(
        f'{parent.label_word.capitalize()} leaned close. "Do not trust the shiny trick," '
        f'{parent.id} said. "A little magic can hide a bigger clue."'
    )
    child.memes["curiosity"] += 1
    world.facts["warning"] = spell.label


def use_magic(world: World, child: Entity, item: Entity, spell: Spell, delay: int) -> None:
    child.memes["bravery"] += 1
    item.meters["shuffled"] += 1
    if is_revealed(spell, delay):
        item.meters["revealed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} whispered the spell and the room went still. "
        f"The {spell.label} shimmered like moonlight on water."
    )


def reveal_solution(world: World, child: Entity, parent: Entity, item: Entity, spell: Spell) -> None:
    item.meters["revealed"] = 1.0
    item.hidden = False
    world.say(
        f"Then the magic lifted. Under the glitter, {child.id} found the real clue: "
        f"{item.label} was not lost at all, just hidden for the game."
    )
    world.say(
        f'{parent.label_word.capitalize()} smiled. "You solved the mystery," '
        f'{parent.id} said, "by looking carefully instead of guessing too fast."'
    )
    child.memes["joy"] += 1


def ending(world: World, child: Entity, parent: Entity, item: Entity) -> None:
    world.say(
        f"In the last soft light, {child.id} held {item.label} up like a tiny treasure. "
        f"{parent.label_word.capitalize()} and {child.id} walked home together, "
        f"with the mystery solved and the evening calm again."
    )


def tell(place: Place, item_cfg: Item, spell: Spell,
         child_name: str = "Mina", child_gender: str = "girl",
         parent_type: str = "mother", delay: int = 0) -> World:
    world = World(place)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent"))
    room = world.add(Entity(id="room", type="room", label=place.label))
    item = world.add(Entity(
        id="clue", type=item_cfg.role, label=item_cfg.label, magical=item_cfg.magical, clue=item_cfg.clue
    ))
    world.facts["room"] = room

    setup(world, child, parent, item, place)
    world.para()
    peel_and_search(world, child, item, place)
    warn(world, parent, child, item, spell)
    world.para()
    use_magic(world, child, item, spell, delay)
    reveal_solution(world, child, parent, item, spell)
    world.para()
    ending(world, child, parent, item)

    world.facts.update(
        child=child,
        parent=parent,
        item=item,
        item_cfg=item_cfg,
        spell=spell,
        place=place,
        delay=delay,
        solved=True,
    )
    return world


PLACES = {
    "orchard": Place("orchard", "the orchard", "mysterious", "a low stone wall"),
    "garden": Place("garden", "the garden", "quiet", "a rose hedge"),
    "courtyard": Place("courtyard", "the courtyard", "glimmering", "a fountain shadow"),
}

ITEMS = {
    "jujube": Item("jujube", "jujube", "a warm jujube in a little bowl", "fruit", magical=True, clue=True),
    "lantern": Item("lantern", "lantern", "a small brass lantern", "object", magical=True, clue=True),
    "note": Item("note", "note", "a folded note with silver edges", "paper", magical=True, clue=True),
}

SPELLS = {
    "glow": Spell("glow", "Glow", 3, 3, "glowed softly", "flickered and failed", tags={"magic"}),
    "uncover": Spell("uncover", "Uncover", 2, 2, "uncovered the clue", "could not pull the secret loose", tags={"magic"}),
    "listen": Spell("listen", "Listen", 3, 2, "helped the room listen", "made no sense at all", tags={"magic"}),
}

GIRL_NAMES = ["Mina", "Lina", "Nora", "Ivy", "Ada"]
BOY_NAMES = ["Milo", "Theo", "Eli", "Owen", "Finn"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short magical mystery for a 3-to-5-year-old that includes the words "{f["item_cfg"].label}", "macaw", and "jujube".',
        f"Tell a story where {f['child'].id} uses a tiny bit of magic to solve a mystery in {f['place'].label}, and the clue turns out to be {f['item_cfg'].phrase}.",
        f'Write a child-friendly mystery with a gentle surprise ending, using the phrase "peel-gerund" as part of the search.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    item = f["item_cfg"]
    spell = f["spell"]
    place = f["place"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {parent.label_word}, who searched {place.label} for a mystery clue."),
        ("What was strange about the clue?",
         f"The clue looked like {item.phrase}, but it was hiding something important. That is why the search felt mysterious."),
        ("What did the magic do?",
         f"The magic made the clue glow and then helped reveal the real secret. It did not change the answer; it only uncovered it."),
        ("How did the story end?",
         f"{child.id} solved the mystery and walked home with {parent.label_word}. The final image is calm because the hidden thing was found."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a jujube?",
         "A jujube is a small fruit. It can be sweet and soft, like a little treat."),
        ("What is a macaw?",
         "A macaw is a big, colorful bird with a loud voice. It can look bright like a rainbow."),
        ("What does magic mean in a story?",
         "Magic means something unusual and wonderful can happen, like a glow, a spell, or a secret reveal."),
        ("What makes a story a mystery?",
         "A mystery has a puzzle or hidden answer. The characters look for clues and learn the truth at the end."),
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
        if e.magical:
            bits.append("magical=True")
        if e.clue:
            bits.append("clue=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place: Place, item: Item) -> str:
    if not item.clue:
        return "(No story: this item is not a real clue, so the mystery would not have anything to solve.)"
    if not place.can_shuffle:
        return "(No story: this place does not support a proper mystery search.)"
    return "(No story: that combination does not produce a child-friendly magical mystery.)"


def valid_sensible_spells() -> list[Spell]:
    return [s for s in SPELLS.values() if s.sense >= SENSE_MIN]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A magical mystery storyworld with jujube, macaw, and a peel-gerund search."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.magical:
            lines.append(asp.fact("magical", iid))
        if item.clue:
            lines.append(asp.fact("clue", iid))
    for sid, spell in SPELLS.items():
        lines.append(asp.fact("spell", sid))
        lines.append(asp.fact("sense", sid, spell.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(S) :- spell(S), sense(S, N), sense_min(M), N >= M.
valid(P, I, S) :- place(P), item(I), spell(S), clue(I), magical(I), sensible(S).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program(show="#show sensible/1."))
    return sorted(s for (s,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos().")
    if set(asp_sensible()) == {s.id for s in valid_sensible_spells()}:
        print("OK: ASP sensible spell set matches.")
    else:
        rc = 1
        print("MISMATCH in sensible spells.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: default generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.spell and SPELLS[args.spell].sense < SENSE_MIN:
        raise StoryError("(Refusing a spell that is too weak for this mystery.)")
    if args.place and args.item:
        place, item = PLACES[args.place], ITEMS[args.item]
        if not suspicious_shuffle(place, item):
            raise StoryError(explain_rejection(place, item))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.item is None or c[1] == args.item)
              and (args.spell is None or c[2] == args.spell)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, item, spell = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 1)
    return StoryParams(place, item, spell, child_name, child_gender, parent, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], ITEMS[params.item], SPELLS[params.spell],
                 params.child, params.child_gender, params.parent, params.delay)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
    StoryParams("orchard", "jujube", "glow", "Mina", "girl", "mother", 0),
    StoryParams("garden", "lantern", "uncover", "Theo", "boy", "father", 1),
    StoryParams("courtyard", "note", "listen", "Ivy", "girl", "mother", 0),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(show="#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible spells: {', '.join(asp_sensible())}\n")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            seed = base_seed + i
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
            header = f"### {p.child}: {p.place}, {p.item}, {p.spell}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
