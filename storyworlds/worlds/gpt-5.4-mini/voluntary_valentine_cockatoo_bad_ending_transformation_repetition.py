#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/voluntary_valentine_cockatoo_bad_ending_transformation_repetition.py
===================================================================================================

A standalone story world for a tiny Tall Tale style domain: a child makes a
voluntary valentine gift for a cockatoo, the bird transforms the gift in repeated
steps, and the story can end badly if the wrong choice is made.

The world is built from typed entities with physical meters and emotional memes,
a small forward-chained rule engine, a reasonableness gate, and an inline ASP
twin for parity checks.
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


@dataclass
class Place:
    id: str
    label: str
    bright: bool = True
    has_table: bool = True
    has_window: bool = False


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    color: str
    transform: str
    repeated: str
    fragile: bool = True
    bad_if: str = ""


@dataclass
class Bird:
    id: str
    label: str
    phrase: str
    mimic: str
    flutter: str
    proud: str
    can_spoil: bool = True


@dataclass
class Ending:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str


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
    tag: str
    apply: Callable[[World], list[str]]


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    gift = world.get("gift")
    bird = world.get("bird")
    if gift.meters["changed"] < 1:
        return out
    sig = ("repeat", gift.id, int(gift.meters["changed"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bird.memes["delight"] += 1
    gift.meters["changed"] += 1
    out.append("__repeat__")
    return out


def _r_spoil(world: World) -> list[str]:
    out: list[str] = []
    gift = world.get("gift")
    bird = world.get("bird")
    if gift.meters["changed"] < 2:
        return out
    sig = ("spoil", gift.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if gift.meters["stuck"] >= 1:
        return out
    gift.meters["spoiled"] += 1
    bird.memes["alarm"] += 1
    out.append("__spoil__")
    return out


CAUSAL_RULES = [Rule("repeat", "transform", _r_repeat), Rule("spoil", "bad", _r_spoil)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def sensible_endings() -> list[Ending]:
    return [e for e in ENDINGS.values() if e.sense >= SENSE_MIN]


def hazard(gift: Gift, bird: Bird, place: Place) -> bool:
    return gift.fragile and bird.can_spoil and place.bright


def end_power(end: Ending, repeated: int) -> int:
    return end.power + repeated


def outcome_of(params: "StoryParams") -> str:
    if params.avoid:
        return "avoided"
    if params.ending == "tame":
        return "transformed"
    return "bad"


def _do_offer(world: World, gift: Gift) -> None:
    world.get("gift").meters["shared"] += 1
    world.say(
        f"{world.get('child').id} made a voluntary valentine and laid {gift.phrase} "
        f"on the porch rail."
    )


def _bird_notice(world: World, bird: Bird, gift: Gift) -> None:
    world.say(
        f"A cockatoo with a snowy crest came strutting by, as bold as a parade. "
        f"{bird.phrase.capitalize()} paused, eyed the valentine, and gave it a curious tilt of the head."
    )


def _repeat_turn(world: World, bird: Bird, gift: Gift) -> None:
    bird.memes["curious"] += 1
    world.say(
        f'The cockatoo said "{bird.mimic}" and tapped the bow once, then again, then again. '
        f"{gift.repeated.capitalize()}."
    )


def _transform(world: World, bird: Bird, gift: Gift) -> None:
    gift.meters["changed"] += 1
    gift.label = "sparkly valentine"
    world.say(
        f"With a little fluff and a flurry, the valentine transformed. "
        f"{gift.phrase.capitalize()} turned into {gift.transform}."
    )


def _bad_turn(world: World, bird: Bird, gift: Gift) -> None:
    gift.meters["stuck"] += 1
    gift.meters["spoiled"] += 1
    bird.memes["trouble"] += 1
    world.say(
        f"The cockatoo chewed the ribbon, and the darling card tore in the wind. "
        f"At last the valentine was ruined, and the morning lost its shine."
    )


def _repair_lesson(world: World, child: Entity, adult: Entity, bird: Bird, gift: Gift) -> None:
    child.memes["sadness"] += 1
    adult.memes["comfort"] += 1
    world.say(
        f"{adult.label_word.capitalize()} came out kindly and said, "
        f'"Some gifts are for looking, not for leaving where a clever bird can reach them."'
    )
    world.say(
        f"{child.id} nodded, picked up the torn valentine, and promised to make a safer one next time."
    )


def _bright_finish(world: World, child: Entity, bird: Bird, gift: Gift) -> None:
    child.memes["joy"] += 1
    bird.memes["pride"] += 1
    world.say(
        f"Before long the child made a new valentine with thicker paper and a ribbon tied inside the kitchen. "
        f"The cockatoo watched from the fence, all proper and proud, while the new card stayed safe."
    )


def tell(place: Place, gift: Gift, bird: Bird, ending: Ending, avoid: bool = False) -> World:
    world = World()
    child = world.add(Entity("Rae", kind="character", type="girl", role="child"))
    adult = world.add(Entity("Aunt June", kind="character", type="woman", role="adult", label="Aunt June"))
    world.add(Entity("porch", type="place", label=place.label))
    world.add(Entity("gift", type="thing", label=gift.label))
    world.add(Entity("bird", type="bird", label=bird.label))

    _do_offer(world, gift)
    _bird_notice(world, bird, gift)

    if avoid:
        world.para()
        world.say(
            f"Rae heard the warning in the cockatoo's bright eyes and carried the valentine inside instead."
        )
        world.say("There the gift stayed neat, and the bird only admired it from the window.")
        child.memes["relief"] += 1
        bird.memes["admire"] += 1
        world.say(
            f"In the end, Rae and the cockatoo traded friendly bows through the glass, and the card stayed whole."
        )
        outcome = "avoided"
    else:
        world.para()
        _repeat_turn(world, bird, gift)
        _transform(world, bird, gift)
        propagate(world, narrate=True)
        if ending.id == "tame":
            world.say(
                f"The feathers brushed the card three times more, but the ribbon held and the valentines only got brighter."
            )
            _bright_finish(world, child, bird, gift)
            outcome = "transformed"
        else:
            _bad_turn(world, bird, gift)
            _repair_lesson(world, child, adult, bird, gift)
            world.say(
                f"By supper time the torn valentine lay in the basket, a sad little remnant of the morning's proud start."
            )
            outcome = "bad"

    world.facts.update(
        child=child,
        adult=adult,
        place=place,
        gift=gift,
        bird=bird,
        ending=ending,
        avoid=avoid,
        outcome=outcome,
        repeated=int(gift.meters["changed"]),
    )
    return world


PLACES = {
    "porch": Place("porch", "the porch", bright=True, has_table=True, has_window=True),
    "yard": Place("yard", "the yard", bright=True, has_table=False, has_window=False),
    "garden": Place("garden", "the garden gate", bright=True, has_table=False, has_window=False),
}

GIFTS = {
    "card": Gift("card", "a homemade valentine", "a homemade valentine with a red heart", "red", "a glittery paper bird", "the same card, then a brighter card, then a glitterier card", fragile=True, bad_if="left out where a cockatoo can peck it"),
    "cup": Gift("cup", "a painted valentine cup", "a painted valentine cup with a ribbon", "pink", "a bright little trinket", "the cup kept changing its look", fragile=True, bad_if="set beside seed and straw"),
    "flag": Gift("flag", "a stitched valentine flag", "a stitched valentine flag with gold thread", "gold", "a shining banner", "the flag kept getting fancier", fragile=False, bad_if="left in the wind"),
}

BIRDS = {
    "cockatoo": Bird("cockatoo", "cockatoo", "a cockatoo with a snowy crest", "cock-a-doodle-woo!", "flutter", "proud"),
    "corella": Bird("corella", "corella", "a white corella with a jaunty step", "squawk-spark!", "flutter", "proud"),
}

ENDINGS = {
    "tame": Ending("tame", 3, 3, "the bird transformed the gift, but kindly enough that it survived", "the bird transformed it too much", "The bird transformed the gift, but the new shape stayed safe."),
    "bad": Ending("bad", 2, 2, "the bird transformed the gift until it was ruined", "the gift stayed safe", "The gift changed too much and ended up ruined."),
}

GIRL_NAMES = ["Rae", "Mina", "June", "Ivy", "Nell", "Luna", "Molly", "Ada"]
TRAITS = ["voluntary", "bold", "gentle", "sunny", "patient"]


@dataclass
class StoryParams:
    place: str
    gift: str
    bird: str
    ending: str
    name: str
    trait: str
    avoid: bool = False
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for gid, gift in GIFTS.items():
            for bid, bird in BIRDS.items():
                if not hazard(gift, bird, place):
                    continue
                for eid, end in ENDINGS.items():
                    if end.sense >= SENSE_MIN:
                        combos.append((pid, gid, bid, eid))
    return combos


def explain_rejection(gift: Gift, bird: Bird, place: Place) -> str:
    return (
        f"(No story: {gift.label} would not have a lively bad ending there. "
        f"The cockatoo needs a bright, reachable gift in a bright place so the repeated transformation can matter.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world: a voluntary valentine, a cockatoo, and a transformation with a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--bird", choices=BIRDS)
    ap.add_argument("--ending", choices=ENDINGS)
    ap.add_argument("--name", choices=GIRL_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--avoid", action="store_true")
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
              and (args.gift is None or c[1] == args.gift)
              and (args.bird is None or c[2] == args.bird)
              and (args.ending is None or c[3] == args.ending)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, gift, bird, ending = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        gift=gift,
        bird=bird,
        ending=ending,
        name=args.name or rng.choice(GIRL_NAMES),
        trait=args.trait or rng.choice(TRAITS),
        avoid=args.avoid,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story that includes the words "voluntary", "valentine", and "cockatoo".',
        f"Tell a story where {f['child'].id} makes a voluntary valentine for a cockatoo and the gift changes again and again.",
        f"Write a child-friendly tall tale about a valentine, a cockatoo, and a repeated transformation that ends badly.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, bird, gift = f["child"], f["bird"], f["gift"]
    return [
        ("Who made the valentine?",
         f"{child.id} made it voluntarily, as a gift just because she wanted to. That is what started the whole tall-tale morning."),
        ("What kind of bird was it?",
         f"It was a cockatoo with a snowy crest. The bird was curious, loud, and ready to transform the gift by pecking and fluffing it."),
        ("What happened to the gift?",
         f"It changed over and over, and in the bad ending it got torn and spoiled. The repeated transformation made the first gift end up ruined."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a valentine?",
         "A valentine is a card or little gift made to show affection on Valentine’s Day. People often decorate it with hearts, ribbons, or sweet words."),
        ("What is a cockatoo?",
         "A cockatoo is a large parrot with a crest on its head. Cockatoos can be noisy, clever, and very eager to investigate shiny things."),
        ("What does voluntary mean?",
         "Voluntary means you choose to do something on your own, without being forced. It is something done because you want to."),
        ("What is a transformation?",
         "A transformation is a change from one form to another. Something can look different after it has been transformed."),
        ("What is repetition?",
         "Repetition means doing something again and again. In stories, repetition can make a rhythm or show a habit."),
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    gift = GIFTS[params.gift]
    bird = BIRDS[params.bird]
    ending = ENDINGS[params.ending]
    world = tell(place, gift, bird, ending, avoid=params.avoid)
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


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for gid, gift in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        if gift.fragile:
            lines.append(asp.fact("fragile", gid))
    for bid in BIRDS:
        lines.append(asp.fact("bird", bid))
        lines.append(asp.fact("can_spoil", bid))
    for eid, end in ENDINGS.items():
        lines.append(asp.fact("ending", eid))
        lines.append(asp.fact("sense", eid, end.sense))
        lines.append(asp.fact("power", eid, end.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
hazard(P,G,B) :- place(P), gift(G), bird(B), fragile(G), can_spoil(B).
sensible(E) :- ending(E), sense(E,S), sense_min(M), S >= M.
valid(P,G,B,E) :- hazard(P,G,B), sensible(E).
outcome(avoided) :- voluntary_choice.
outcome(transformed) :- not voluntary_choice, tame_ending.
outcome(bad) :- not voluntary_choice, not tame_ending.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(e for (e,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("voluntary_choice") if params.avoid else "",
        asp.fact("tame_ending") if params.ending == "tame" else "",
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    if set(asp_sensible()) == {e for e, v in ENDINGS.items() if v.sense >= SENSE_MIN}:
        print("OK: sensible endings match.")
    else:
        rc = 1
        print("MISMATCH in sensible endings.")
    for p in [StoryParams(*c, name="Rae", trait="bold") for c in valid_combos()[:3]]:
        if asp_outcome(p) != outcome_of(p):
            rc = 1
            print("MISMATCH in outcome for", p)
            break
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, gift=None, bird=None, ending=None, name=None, trait=None, avoid=False), random.Random(0)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


CURATED = [
    StoryParams("porch", "card", "cockatoo", "bad", "Rae", "voluntary"),
    StoryParams("yard", "cup", "corella", "tame", "Mina", "bold"),
    StoryParams("garden", "flag", "cockatoo", "bad", "June", "gentle", avoid=True),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show sensible/1.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible endings: {', '.join(asp_sensible())}\n")
        for t in asp_valid_combos():
            print(" ", t)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
