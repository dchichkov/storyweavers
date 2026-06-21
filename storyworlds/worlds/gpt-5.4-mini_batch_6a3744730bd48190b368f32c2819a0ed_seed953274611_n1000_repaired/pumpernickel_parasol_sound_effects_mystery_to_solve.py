#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pumpernickel_parasol_sound_effects_mystery_to_solve.py
=======================================================================================

A tiny whodunit-style storyworld about a bakery mystery:
someone hears odd sound effects, a pumpernickel loaf goes missing, and a child
detective solves it by following a parasol-shaped clue.

The world is deliberately small and classical:
- typed entities with meters and memes
- simulated state drives the prose
- a reasonableness gate keeps the mystery plausible
- QA comes from world state, not by parsing rendered English
- an inline ASP twin mirrors the Python gate and ending logic
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
DETECTIVE_MIN = 3
CLUE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: {"found": 0.0, "mystery": 0.0})
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    smell: str
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
class Item:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)
    hidden: bool = False
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
class SoundCue:
    id: str
    sound: str
    source: str
    effect: str
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
    clue: str
    sound: str
    thief: str
    detective: str
    sidekick: str
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
        return c


def _mark_mystery(world: World) -> list[str]:
    out: list[str] = []
    loaf = world.get("loaf")
    if loaf.meters["missing"] >= THRESHOLD and ("mystery", "raised") not in world.fired:
        world.fired.add(("mystery", "raised"))
        for e in list(world.entities.values()):
            if e.kind == "character":
                e.memes["curiosity"] = e.memes.get("curiosity", 0.0) + 1
        out.append("A little mystery hung over the room.")
    return out


def _resolve(world: World) -> list[str]:
    out: list[str] = []
    loaf = world.get("loaf")
    clue = world.get("clue")
    if loaf.meters["missing"] < THRESHOLD or clue.meters["found"] < THRESHOLD:
        return out
    if ("mystery", "solved") not in world.fired:
        world.fired.add(("mystery", "solved"))
        out.append("__solve__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for fn in (_mark_mystery, _resolve):
            s = fn(world)
            if s:
                changed = True
                produced.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def clue_is_plausible(clue: Item, sound: SoundCue) -> bool:
    return "parasol" in clue.tags and "sound" in sound.tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for clue in ITEMS:
            for sound in SOUNDS:
                if clue_is_plausible(ITEMS[clue], SOUNDS[sound]):
                    combos.append((place, clue, sound))
    return combos


def solve_mystery(world: World, detective: Entity, sidekick: Entity, clue: Item, sound: SoundCue) -> None:
    detective.memes["thinking"] = detective.memes.get("thinking", 0.0) + 1
    sidekick.memes["nervous"] = sidekick.memes.get("nervous", 0.0) + 1
    world.say(
        f"In the bakery, {detective.id} and {sidekick.id} listened to the odd little "
        f"{sound.sound} sound echoing off the counter."
    )
    world.say(
        f'“{sound.sound}!” whispered {sidekick.id}. “That does not sound like a loaf that walked away.”'
    )
    world.say(
        f'{detective.id} frowned and looked at the floor. The clue was a {clue.phrase}, '
        f'left right beside the flour sack.'
    )
    clue.meters["found"] += 1
    propagate(world, narrate=False)
    world.say(
        f'The clue fit the strange trail at once, and {detective.id} knew the mystery '
        f'wasn't a thief at all.'
    )


def reveal(world: World, thief: Entity, clue: Item, sound: SoundCue) -> None:
    loaf = world.get("loaf")
    parasol = world.get("parasol")
    loaf.meters["found"] += 1
    thief.memes["embarrassed"] = thief.memes.get("embarrassed", 0.0) + 1
    thief.attrs["caught"] = True
    world.say(
        f"Then the answer popped out with a soft {sound.effect}: the missing pumpernickel "
        f"had been tucked under {thief.id}'s {parasol.label}, safe from the drizzle from the open door."
    )
    world.say(
        f"{thief.id} blinked, then laughed. “I carried it inside so it would not get soggy,” "
        f"{thief.pronoun()} admitted."
    )
    world.say(
        f'{detective_name(world)} smiled. “Next time, just tell us. A clue like that makes a perfect case.”'
    )


def detective_name(world: World) -> str:
    return world.facts["detective"].id


def tell(params: StoryParams) -> World:
    world = World()
    place = world.add(Entity(id="bakery", kind="place", type="room", label=PLACES[params.place].label, tags=set(PLACES[params.place].tags)))
    detective = world.add(Entity(id=params.detective, kind="character", type="girl", role="detective", traits=["sharp"], memes={"curiosity": 1.0, "confidence": 1.0}))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="boy", role="sidekick", traits=["helpful"], memes={"nerves": 1.0}))
    thief = world.add(Entity(id=params.thief, kind="character", type="woman", role="thief", traits=["careful"], memes={"guilt": 0.0}))
    loaf = world.add(Entity(id="loaf", kind="thing", type="food", label="pumpernickel loaf", tags={"pumpernickel", "bread"}))
    clue = world.add(Entity(id="clue", kind="thing", type="clue", label=ITEMS[params.clue].label, tags=set(ITEMS[params.clue].tags)))
    parasol = world.add(Entity(id="parasol", kind="thing", type="thing", label="parasol", tags={"parasol"}))
    sound = SOUNDS[params.sound]
    world.add(Entity(id="sound", kind="thing", type="sound", label=sound.sound, tags={"sound"}))
    world.facts.update(detective=detective, sidekick=sidekick, thief=thief, loaf=loaf, clue=clue, parasol=parasol, sound=sound, place=place)

    world.say(
        f"At the little bakery, {PLACES[params.place].smell}, and everyone froze when a {sound.sound} went by the shelf."
    )
    world.say(
        f"The mystery began with one missing thing: the pumpernickel loaf."
    )
    loaf.meters["missing"] = 1
    propagate(world, narrate=False)
    world.para()
    solve_mystery(world, detective, sidekick, clue, sound)
    world.para()
    reveal(world, thief, clue, sound)
    world.say(
        f"In the end, the bakery was quiet again, and the pumpernickel sat back on the counter while the parasol leaned harmlessly by the door."
    )
    world.facts["solved"] = True
    return world


PLACES = {
    "bakery": Place(id="bakery", label="the bakery", smell="warm bread smelled sweet", tags={"bakery"}),
    "shop": Place(id="shop", label="the little shop", smell="fresh rolls warmed the air", tags={"shop"}),
}

ITEMS = {
    "parasol": Item(id="parasol_clue", label="parasol", phrase="parasol-shaped streak", tags={"parasol", "sound"}),
    "ribbon": Item(id="ribbon_clue", label="ribbon", phrase="bright ribbon", tags={"ribbon"}),
}

SOUNDS = {
    "tap": SoundCue(id="tap", sound="tap-tap-tap", source="counter", effect="tap", tags={"sound"}),
    "shuffle": SoundCue(id="shuffle", sound="shuff-shuff", source="floor", effect="shuffle", tags={"sound"}),
    "whisper": SoundCue(id="whisper", sound="whisper-whisper", source="door", effect="whisper", tags={"sound"}),
}

CURATED = [
    StoryParams(place="bakery", clue="parasol", sound="tap", thief="Mina", detective="Pip", sidekick="Ben", seed=None),
    StoryParams(place="shop", clue="parasol", sound="shuffle", thief="June", detective="Kit", sidekick="Ollie", seed=None),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a whodunit for a young child that includes the words "pumpernickel" and "parasol", and uses sound effects like {f["sound"].sound}.',
        f"Tell a small mystery story where {f['detective'].id} follows a parasol clue to find the missing pumpernickel loaf.",
        f"Write a gentle bakery mystery with a sound effect, a clue, and a clear answer at the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    det = f["detective"].id
    side = f["sidekick"].id
    thief = f["thief"].id
    sound = f["sound"].sound
    return [
        ("What was missing from the bakery?",
         "The pumpernickel loaf was missing. That is the mystery that made everyone look closely at the floor and the counter."),
        ("Who solved the mystery?",
         f"{det} solved it with help from {side}. {det} followed the parasol clue and figured out where the loaf had gone."),
        ("What sound did everyone hear?",
         f"They heard {sound}. It made the room feel mysterious, but it also gave the detective a moment to listen carefully."),
        ("Why was the loaf under the parasol?",
         f"{thief} had tucked the pumpernickel under the parasol so it would not get soggy near the open door. That explains the clue and the missing loaf at the same time."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is pumpernickel?",
         "Pumpernickel is a dark, hearty kind of bread. It can be sliced and shared like other loaves."),
        ("What is a parasol?",
         "A parasol is a light umbrella that helps keep off sun or rain. People can carry it by hand."),
        ("Why do detectives listen for clues?",
         "Detectives listen for clues so they can figure out what happened. A sound, a mark, or an odd object can help solve a mystery."),
        ("What do sound effects do in a story?",
         "Sound effects help you imagine what is happening. They can make a scene feel lively, spooky, or funny."),
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection(place: str, clue: str, sound: str) -> str:
    return "(No story: this mystery would not be plausible enough to solve cleanly.)"


ASP_RULES = r"""
plausible(P,C,S) :- place(P), clue(C), sound(S), parasol_clue(C), sound_fx(S).
mystery_raised :- loaf_missing, plausible(_,_,_).
solved :- mystery_raised, clue_found, thief_caught.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for cid, c in ITEMS.items():
        lines.append(asp.fact("clue", cid))
        if "parasol" in c.tags:
            lines.append(asp.fact("parasol_clue", cid))
    for sid in SOUNDS:
        lines.append(asp.fact("sound", sid))
        lines.append(asp.fact("sound_fx", sid))
    lines.append(asp.fact("loaf_missing"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show plausible/3."))
    return sorted(set(asp.atoms(model, "plausible")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in ASP gate.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: normal generation smoke test passed.")
    except Exception as exc:  # pragma: no cover
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld about pumpernickel, a parasol clue, and sound effects.")
    ap.add_argument("--place", choices=list(PLACES))
    ap.add_argument("--clue", choices=list(ITEMS))
    ap.add_argument("--sound", choices=list(SOUNDS))
    ap.add_argument("--thief")
    ap.add_argument("--detective")
    ap.add_argument("--sidekick")
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
    if args.clue and args.clue != "parasol":
        raise StoryError("No story: the clue must be parasol-shaped for this mystery.")
    if args.sound and args.sound not in SOUNDS:
        raise StoryError("No story: unknown sound effect.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.sound is None or c[2] == args.sound)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, sound = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        clue=clue,
        sound=sound,
        thief=args.thief or rng.choice(["Mina", "June", "Iris", "Nora"]),
        detective=args.detective or rng.choice(["Pip", "Kit", "Ada", "Bea"]),
        sidekick=args.sidekick or rng.choice(["Ben", "Ollie", "Max", "Toby"]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.clue not in ITEMS or params.sound not in SOUNDS:
        raise StoryError("Invalid story parameters.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show plausible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} plausible combos:")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
                params = resolve_params(args, random.Random(seed))
            except StoryError as exc:
                print(exc)
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
