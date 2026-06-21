#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/dandruff_dice_bad_ending_inner_monologue_lesson.py
===================================================================================

A tiny, self-contained storyworld about a folk-tale mistake: a child finds
dandruff on an old cloak, toys with a pair of dice, ignores a wiser warning,
and learns too late that superstition is not a safe plan.

Seed words:
- dandruff
- dice

Seed features:
- Bad Ending
- Inner Monologue
- Lesson Learned

Style:
- Folk Tale

This world is intentionally small and constraint-driven: it generates only
plausible combinations, renders state changes into prose, and includes an ASP
twin for parity checking.
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)
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
    field_name: str
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
class Temptation:
    id: str
    label: str
    phrase: str
    risky: bool
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
class Keeper:
    id: str
    label: str
    phrase: str
    wisdom: int
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


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


def _r_spread(self_world: World) -> list[str]:
    out: list[str] = []
    child = self_world.entities.get("child")
    cloak = self_world.entities.get("cloak")
    if not child or not cloak:
        return out
    if child.meters["scratching"] < THRESHOLD:
        return out
    sig = ("spread",)
    if sig in self_world.fired:
        return out
    self_world.fired.add(sig)
    cloak.meters["ruffled"] += 1
    child.memes["embarrassment"] += 1
    out.append("__spread__")
    return out


CAUSAL_RULES = [Rule("spread", _r_spread)]


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


def folk_intro(world: World, child: Entity, place: Place) -> None:
    world.say(
        f"Long ago, in {place.label}, there lived a little {child.type} named {child.id}."
    )
    world.say(
        f"{child.id} wore a weathered cloak and liked to listen for small secrets in the wind."
    )


def notice_dandruff(world: World, child: Entity, cloak: Entity) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"One morning {child.id} brushed {child.pronoun('possessive')} sleeve and found dandruff on {cloak.label}."
    )
    world.say(
        f'“That looks like snow,” {child.id} thought, “but snow indoors is never a good sign.”'
    )


def tempt_with_dice(world: World, child: Entity, dice: Temptation) -> None:
    child.memes["temptation"] += 1
    world.say(
        f"In {child.id}'s pocket were two little dice, smooth as river stones."
    )
    world.say(
        f'{child.id} held them tight and wondered, “Shall I scratch, or shall I leave it be?”'
    )
    world.say(
        f'“If I throw the dice,” {child.id} thought, “perhaps the numbers will tell me what is wise.”'
    )
    if dice.risky:
        world.say(
            f'But the dice were a poor adviser; they knew chance, not care.'
        )


def warn_keeper(world: World, child: Entity, keeper: Entity, cloak: Entity) -> None:
    child.memes["warning"] += 1
    world.say(
        f'{keeper.id} looked up from the hearth and said, “Do not scratch at {cloak.label}.'
    )
    world.say(
        f'Use a comb and warm water, child; otherwise the flakes will fly and the cloth will suffer.”'
    )


def inner_monologue(world: World, child: Entity) -> None:
    worry = child.memes["temptation"] + child.memes["warning"]
    if worry > 0:
        world.say(
            f'Inside {child.id}\'s heart a small voice murmured, “I know the wise path,'
            f'but the silly path is quicker, and I am tired of waiting.”'
        )


def choose_badly(world: World, child: Entity) -> None:
    child.meters["scratching"] += 1
    child.memes["defiance"] += 1
    world.say(
        f'At last {child.id} tossed the dice, laughed at the numbers, and scratched anyway.'
    )
    world.say(
        f'The motion shook the cloak, sent the dandruff drifting, and left the cloth looking worse than before.'
    )
    propagate(world, narrate=False)


def loss_and_bad_ending(world: World, child: Entity, keeper: Entity, cloak: Entity) -> None:
    child.meters["loss"] += 1
    child.memes["regret"] += 1
    keeper.memes["sadness"] += 1
    world.say(
        f'Before long, the hearth ash caught in the air, and {child.id} sneezed so hard that the dice flew from {child.pronoun("possessive")} hand into the fire.'
    )
    world.say(
        f"{keeper.id} could save the child, but not the game: the best part of the evening was gone."
    )
    world.say(
        f"{child.id} stood with a dusty head, a ruined cloak, and no dice left to blame."
    )


def lesson_learned(world: World, child: Entity, keeper: Entity, cloak: Entity) -> None:
    child.memes["lesson"] += 1
    world.say("Then the lesson settled down like snow on a still road.")
    world.say(
        f'{keeper.id} said, “Chance is for games, not for choosing care. When your skin is itchy, ask for help and use the right tool.”'
    )
    world.say(
        f'{child.id} bowed {child.pronoun("possessive")} head and remembered that a quick wish can make a long trouble.'
    )


def tell(place: Place, temptation: Temptation, keeper: Keeper, child_name: str = "Milo", child_gender: str = "boy") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    guide = world.add(Entity(id=keeper.id, kind="character", type="grandmother", role="keeper", label=keeper.label))
    cloak = world.add(Entity(id="cloak", type="thing", label="the old cloak"))
    dice = world.add(Entity(id="dice", type="thing", label="the dice"))

    child.memes["hope"] = 1.0
    guide.memes["wisdom"] = float(keeper.wisdom)
    cloak.meters["dandruff"] = 1.0
    dice.meters["luck"] = 1.0

    folk_intro(world, child, place)
    world.para()
    notice_dandruff(world, child, cloak)
    tempt_with_dice(world, child, temptation)
    warn_keeper(world, child, guide, cloak)
    inner_monologue(world, child)
    choose_badly(world, child)
    world.para()
    loss_and_bad_ending(world, child, guide, cloak)
    lesson_learned(world, child, guide, cloak)

    world.facts.update(
        child=child,
        keeper=guide,
        cloak=cloak,
        dice=dice,
        place=place,
        temptation=temptation,
        outcome="bad",
        lesson=True,
    )
    return world


PLACES = {
    "village": Place(id="village", label="a little village", field_name="village", tags={"folk", "home"}),
    "mill": Place(id="mill", label="the old mill", field_name="mill", tags={"folk", "work"}),
    "cottage": Place(id="cottage", label="a willow cottage", field_name="cottage", tags={"folk", "home"}),
}

TEMPTATIONS = {
    "dice": Temptation(id="dice", label="dice", phrase="a pair of dice", risky=True, tags={"dice", "chance"}),
}

KEEPERS = {
    "grandma": Keeper(id="grandma", label="Grandma", phrase="a wise grandma", wisdom=3, tags={"family", "wisdom"}),
}

GIRL_NAMES = ["Nia", "Mara", "Lina", "Tess", "Bess"]
BOY_NAMES = ["Milo", "Evan", "Otto", "Jonah", "Rafi"]


@dataclass
class StoryParams:
    place: str = "village"
    temptation: str = "dice"
    keeper: str = "grandma"
    child_name: str = "Milo"
    child_gender: str = "boy"
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, t, k) for p in PLACES for t in TEMPTATIONS for k in KEEPERS if TEMPTATIONS[t].risky]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld: dandruff, dice, a bad ending, and a lesson learned.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--temptation", choices=TEMPTATIONS)
    ap.add_argument("--keeper", choices=KEEPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["boy", "girl"])
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
              and (args.temptation is None or c[1] == args.temptation)
              and (args.keeper is None or c[2] == args.keeper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, temptation, keeper = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["boy", "girl"])
    name = args.name or rng.choice(BOY_NAMES if gender == "boy" else GIRL_NAMES)
    return StoryParams(place=place, temptation=temptation, keeper=keeper, child_name=name, child_gender=gender)


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    keeper = f["keeper"]
    return [
        ("Who is the story about?", f"It is about {child.id} and {keeper.id}, told like an old folk tale."),
        ("What did the child find?", f"{child.id} found dandruff on the old cloak, which made the child uneasy."),
        ("What did the child think about the dice?", f"{child.id} thought the dice might tell a wise answer, but they could not. The dice were only for games, so they could not choose a careful path."),
        ("How did the story end?", f"It ended badly: the dice were lost in the fire, the cloak was ruined, and {child.id} learned a lesson too late."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What are dice?", answer="Dice are little cubes with dots on them. People roll them in games to get a random number."),
        QAItem(question="What is dandruff?", answer="Dandruff is tiny flakes of dry skin that can fall from the scalp or hair. It is not dangerous, but it can be itchy."),
        QAItem(question="What should you do if something feels itchy?", answer="It is best to ask a grown-up and use the right care, like a comb or clean water, instead of guessing."),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a folk tale about a child who finds dandruff on an old cloak and thinks dice can tell a wise answer.',
        'Tell a story with the words dandruff and dice, with an inner monologue, a bad ending, and a lesson learned.',
        'Write a short village tale where a child ignores Grandma, trusts dice instead of care, and learns too late.',
    ]


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        temptation = TEMPTATIONS[params.temptation]
        keeper = KEEPERS[params.keeper]
    except KeyError as exc:
        raise StoryError(f"Unknown parameter: {exc.args[0]}") from exc
    if params.child_gender not in {"boy", "girl"}:
        raise StoryError("Invalid child gender.")
    world = tell(place, temptation, keeper, params.child_name, params.child_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
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
    lines.append("== (3) World knowledge questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,T,K) :- place(P), temptation(T), keeper(K), risky(T).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for t, obj in TEMPTATIONS.items():
        lines.append(asp.fact("temptation", t))
        if obj.risky:
            lines.append(asp.fact("risky", t))
    for k in KEEPERS:
        lines.append(asp.fact("keeper", k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    # smoke test: generate a normal story before parity checking
    try:
        sample = generate(StoryParams())
        assert sample.story and sample.world is not None
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH between Python and ASP valid combos.")
        if cl - py:
            print(" only in clingo:", sorted(cl - py))
        if py - cl:
            print(" only in python:", sorted(py - cl))
        return 1
    print(f"OK: smoke test passed and ASP parity holds for {len(py)} combos.")
    return 0


CURATED = [
    StoryParams(place="village", temptation="dice", keeper="grandma", child_name="Milo", child_gender="boy"),
    StoryParams(place="mill", temptation="dice", keeper="grandma", child_name="Nia", child_gender="girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for p, t, k in combos:
            print(f"{p:10} {t:10} {k}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
