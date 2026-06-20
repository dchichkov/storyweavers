#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/dejected_magic_rhyme_pirate_tale.py
===================================================================

A standalone story world for a tiny pirate tale with magic and rhyme.

Premise:
A young pirate feels dejected when their rhyming spell does not work, then
finds the right words, rescues a tiny treasure from a tidepool, and ends with a
bright, rhyming victory on the deck.

This world is deliberately small and state-driven:
- typed entities with meters and memes
- a forward-causal world model
- a reasonableness gate
- an ASP twin for parity checks
- three Q&A sets grounded in world state
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
MAGIC_MIN = 1
RHYME_MIN = 1


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
        return self.label or self.type



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    scene: str
    dark_spot: str
    deck_image: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
    chant: str
    rhyme: str
    glow: str
    power: int
    sense: int

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Treasure:
    id: str
    label: str
    phrase: str
    sparkle: str
    lost_in: str
    fragile: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def _r_magic_fades(world: World) -> list[str]:
    out: list[str] = []
    bard = world.get("bard")
    if bard.meters["spell"] < THRESHOLD:
        return out
    sig = ("magic_fades",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bard.memes["dejected"] += 1
    bard.memes["doubt"] += 1
    out.append("__magic__")
    return out


def _r_treasure_shimmers(world: World) -> list[str]:
    out: list[str] = []
    treasure = world.get("treasure")
    if treasure.meters["wet"] < THRESHOLD:
        return out
    sig = ("treasure_shimmers",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    treasure.meters["sparkle"] += 1
    out.append("__sparkle__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("magic_fades", "social", _r_magic_fades),
    Rule("treasure_shimmers", "physical", _r_treasure_shimmers),
]


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


def reasonableness_ok(place: Place, spell: Spell, treasure: Treasure) -> bool:
    return spell.sense >= SENSE_MIN and treasure.fragile


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid in PLACES:
        for sid in SPELLS:
            for tid in TREASURES:
                if reasonableness_ok(PLACES[pid], SPELLS[sid], TREASURES[tid]):
                    combos.append((pid, sid, tid))
    return combos


def predict(world: World, treasure_id: str) -> dict:
    sim = world.copy()
    _cast_spell(sim, sim.get("bard"), SPELLS[sim.facts["spell"].id], narrate=False)
    return {
        "dejected": sim.get("bard").memes["dejected"] >= THRESHOLD,
        "treasure_wet": sim.get(treasure_id).meters["wet"] >= THRESHOLD,
    }


def _cast_spell(world: World, bard: Entity, spell: Spell, narrate: bool = True) -> None:
    bard.meters["spell"] += 1
    propagate(world, narrate=narrate)


def open_scene(world: World, bard: Entity, mate: Entity, place: Place) -> None:
    bard.memes["hope"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"On a windy quay, {bard.id} and {mate.id} stood on the pirate ship's deck. "
        f"{place.scene}"
    )


def start_dejected(world: World, bard: Entity, spell: Spell, place: Place) -> None:
    bard.memes["dejected"] += 1
    world.say(
        f"{bard.id} tried a magic rhyme, but the words came out wrong. "
        f'{bard.id} looked at the dark water and felt dejected by the rail.'
    )
    world.say(
        f'"I must find the right rhyme," {bard.id} whispered, "to make the moonlit {place.dark_spot} shine."'
    )


def warn_mate(world: World, mate: Entity, bard: Entity, treasure: Treasure) -> None:
    mate.memes["care"] += 1
    world.say(
        f'{mate.id} pointed to {treasure.lost_in}. "{bard.id}, your spell might splash the little prize,'
        f' and that would be a shame."'
    )


def fail_cast(world: World, bard: Entity, spell: Spell) -> None:
    bard.memes["frustration"] += 1
    world.say(
        f'{bard.id} spoke again: "{spell.chant}!" But the rhyme only made a puff of blue smoke and a tiny sneeze of sparks.'
    )


def find_rhyme(world: World, bard: Entity, spell: Spell) -> None:
    bard.memes["brave"] += 1
    bard.memes["dejected"] = 0.0
    world.say(
        f'Then {bard.id} tried a clearer line: "{spell.rhyme}!" The lantern glow grew warm, bright, and kind.'
    )


def rescue_treasure(world: World, bard: Entity, treasure: Treasure, spell: Spell) -> None:
    treasure.meters["wet"] += 1
    _cast_spell(world, bard, spell)
    world.say(
        f"The magic tipped a silver shellboat back to the deck and lifted {treasure.phrase} from {treasure.lost_in}."
    )
    world.say(
        f'It flashed with {treasure.sparkle}, and {bard.id} grinned as the spell finished in a tidy ring of light.'
    )


def ending(world: World, bard: Entity, mate: Entity, place: Place) -> None:
    bard.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"By the last wave, {bard.id} was no longer dejected. {place.deck_image} "
        f"shone under the stars, and the two pirates laughed in rhyme."
    )


def tell(place: Place, spell: Spell, treasure: Treasure, bard_name: str = "Pip",
         mate_name: str = "Mira") -> World:
    world = World()
    bard = world.add(Entity(id=bard_name, kind="character", type="boy", role="bard"))
    mate = world.add(Entity(id=mate_name, kind="character", type="girl", role="mate"))
    tre = world.add(Entity(id="treasure", type="thing", label=treasure.label))
    world.facts["spell"] = spell
    world.facts["treasure"] = treasure
    world.facts["place"] = place

    open_scene(world, bard, mate, place)
    world.para()
    start_dejected(world, bard, spell, place)
    warn_mate(world, mate, bard, treasure)
    fail_cast(world, bard, spell)
    world.para()
    find_rhyme(world, bard, spell)
    rescue_treasure(world, bard, tre, spell)
    ending(world, bard, mate, place)

    world.facts.update(bard=bard, mate=mate, treasure_ent=tre)
    return world


PLACES = {
    "quay": Place("quay", "The ship creaked at the quay, and the sea made silver whiskers on the dark water.", "little tidepool", "The deck now gleamed like a brave little stage."),
    "cove": Place("cove", "The ship bobbed in a hidden cove, with gulls peeking over the rigging.", "moonlit cove", "The deck lanterns blinked like friendly stars."),
    "reef": Place("reef", "The ship rested near a reef where the waves sang under the planks.", "shallow reef pool", "The deck looked painted with moonshine."),
}

SPELLS = {
    "lullaby": Spell("lullaby", "Sparkle, twirl, and shine tonight", "Glow and flow, little light below", "soft blue", power=2, sense=2),
    "seasong": Spell("seasong", "Rhyme, tide, and starry sky", "Sing, ring, and let the treasure fly", "golden", power=2, sense=3),
    "mooncall": Spell("mooncall", "Moonbeams bright, please rise and play", "Rhyme, climb, and lead the way", "pearly", power=3, sense=3),
}

TREASURES = {
    "pearl": Treasure("pearl", "a pearl coin", "a pearl coin", "tiny stars", "the tidepool"),
    "shell": Treasure("shell", "a shell charm", "a shell charm", "little sparkles", "the tidepool"),
    "key": Treasure("key", "a brass key", "a brass key", "bright glints", "the cove"),
}


@dataclass
@dataclass
class StoryParams:
    place: str
    spell: str
    treasure: str
    bard: str
    mate: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


KNOWLEDGE = {
    "magic": [("What is magic in stories?", "Magic in stories is pretend power that can change things in a surprising way."),],
    "rhyme": [("What is a rhyme?", "A rhyme is when words sound alike at the end, like light and night.")],
    "pirate": [("What is a pirate?", "A pirate is a sea adventurer who sails a ship and looks for treasure.")],
    "dejected": [("What does dejected mean?", "Dejected means feeling sad, low, or let down after something goes wrong.")],
    "treasure": [("What is treasure?", "Treasure is something special and valuable, like a coin, a jewel, or a charm.")],
}
KNOWLEDGE_ORDER = ["magic", "rhyme", "pirate", "dejected", "treasure"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale for a small child that includes the word "dejected" and a magic rhyme.',
        f"Tell a story where {f['bard'].id} feels dejected, then finds the right rhyme and saves {f['treasure'].label}.",
        f'Write a short sea story with magic words, a rhyme, and a happy ending on the ship deck.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    bard = f["bard"]
    mate = f["mate"]
    spell = f["spell"]
    treasure = f["treasure"]
    place = f["place"]
    qa = [
        ("Who is the story about?",
         f"It is about {bard.id}, a little pirate who tried to use magic on the deck. {mate.id} stays beside {bard.pronoun('object')} and helps through the trouble."),
        ("Why was {0} dejected?".format(bard.id),
         f"{bard.id} was dejected because the first magic rhyme did not work. The wrong words made only smoke, so the treasure stayed stuck in {treasure.lost_in}."),
        ("What fixed the problem?",
         f"{bard.id} found the right rhyme, {spell.rhyme.lower()}. That made the magic bright enough to lift {treasure.phrase} safely."),
        ("How did the story end?",
         f"It ended with the deck shining and both pirates smiling in rhyme. The old sadness was gone, and the little treasure was back on board."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"magic", "rhyme", "pirate", "dejected", "treasure"}
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("quay", "seasong", "pearl", "Pip", "Mira"),
    StoryParams("cove", "mooncall", "shell", "Ned", "Luna"),
    StoryParams("reef", "lullaby", "key", "Finn", "Tara"),
]


def explain_rejection(spell: Spell, treasure: Treasure) -> str:
    if spell.sense < SENSE_MIN:
        return f"(No story: the spell is too weak to count as a sensible pirate fix.)"
    if not treasure.fragile:
        return f"(No story: that treasure is not delicate enough for the tiny rescue.)"
    return "(No story: this combination does not fit the little magic tale.)"


def valid_story(params: StoryParams) -> bool:
    return reasonableness_ok(PLACES[params.place], SPELLS[params.spell], TREASURES[params.treasure])


ASP_RULES = r"""
valid(P, S, T) :- place(P), spell(S), treasure(T), sense(S, N), N >= sense_min(M), fragile(T).
dejected(B) :- cast_fail(B).
shines(T) :- treasure(T), wet(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for sid, s in SPELLS.items():
        lines.append(asp.fact("spell", sid))
        lines.append(asp.fact("sense", sid, s.sense))
    for tid in TREASURES:
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("fragile", tid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, spell=None, treasure=None, bard=None, mate=None, seed=None), random.Random(7)))
        _ = sample.story
        print("OK: generate smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale with magic, rhyme, and a dejected turn.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--bard")
    ap.add_argument("--mate")
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
              and (args.spell is None or c[1] == args.spell)
              and (args.treasure is None or c[2] == args.treasure)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, spell, treasure = rng.choice(sorted(combos))
    return StoryParams(place, spell, treasure,
                       args.bard or rng.choice(["Pip", "Ned", "Finn", "Jory"]),
                       args.mate or rng.choice(["Mira", "Luna", "Tara", "Saila"]),
                       seed=None)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], SPELLS[params.spell], TREASURES[params.treasure], params.bard, params.mate)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for p, s, t in asp_valid_combos():
            print(f"  {p:6} {s:8} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
