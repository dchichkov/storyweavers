#!/usr/bin/env python3
"""
storyworlds/worlds/rock_n_roll_humor_dialogue_slice_of.py
=========================================================

A small slice-of-life storyworld about a child who wants to make rock'n'roll
music, a grown-up who worries about noise, and a funny compromise that lets the
music happen without upsetting the whole room.

Premise:
- A child loves loud rock'n'roll practice.
- A nearby listener wants peace and a tidy afternoon.
- The turn is a noise problem: the music is fun, but it is too loud for the
  setting.
- The resolution is a quieter setup that still feels like real rock'n'roll.

The world uses:
- physical meters: loudness, volume, clutter, vibration, battery
- emotional memes: excitement, worry, patience, pride, humor, calm
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    quiet_limit: float
    affords: set[str] = field(default_factory=set)


@dataclass
class Act:
    id: str
    verb: str
    gerund: str
    rush: str
    noise: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    reduces_noise: float
    requires: set[str] = field(default_factory=set)
    plural: bool = False


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    soundscape: float = 0.0

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.soundscape = self.soundscape
        return c


SETTINGS = {
    "apartment": Place(id="apartment", label="the apartment", quiet_limit=1.0, affords={"rock", "practice"}),
    "living_room": Place(id="living_room", label="the living room", quiet_limit=1.2, affords={"rock", "practice"}),
    "garage": Place(id="garage", label="the garage", quiet_limit=2.5, affords={"rock", "practice"}),
}

ACTIVITIES = {
    "rock": Act(
        id="rock",
        verb="play rock'n'roll",
        gerund="playing rock'n'roll",
        rush="strum as loud as a thunderclap",
        noise="loud",
        risk="the neighbors would hear every chord",
        keyword="rock'n'roll",
        tags={"rock'n'roll", "music", "guitar"},
    ),
    "practice": Act(
        id="practice",
        verb="practice a song",
        gerund="practicing a song",
        rush="bang the drum extra hard",
        noise="loud",
        risk="the room would shake",
        keyword="song",
        tags={"music", "song"},
    ),
}

GEAR = [
    Gear(
        id="headphones",
        label="big headphones",
        prep="put on big headphones",
        tail="put on the headphones and kept jamming",
        reduces_noise=1.5,
        requires={"electric"},
    ),
    Gear(
        id="mute",
        label="a tiny guitar mute",
        prep="clip on a tiny guitar mute",
        tail="clipped on the mute and kept the beat soft",
        reduces_noise=1.2,
        requires={"guitar"},
    ),
    Gear(
        id="cushion",
        label="a folded cushion",
        prep="place a folded cushion under the drum",
        tail="set the drum on a cushion and tapped a softer rhythm",
        reduces_noise=1.0,
        requires={"drum"},
    ),
]

INSTRUMENTS = {
    "guitar": Entity(id="guitar", type="thing", label="guitar", phrase="a red electric guitar", owner="child"),
    "drum": Entity(id="drum", type="thing", label="drum", phrase="a little drum", owner="child"),
    "amp": Entity(id="amp", type="thing", label="amp", phrase="a small amplifier", owner="child"),
    "headphones": Entity(id="headphones", type="thing", label="headphones", phrase="big headphones", owner="child", plural=True),
}

NAMES = ["Maya", "Noah", "Lina", "Ben", "Ivy", "Leo", "Zoe", "Finn"]
PARENTS = ["mother", "father"]
TRAITS = ["curious", "cheerful", "spirited", "playful", "silly"]


def reasonableness_gate(place: Place, act: Act) -> bool:
    return "rock" in place.affords and act.id in place.affords


def _noise(world: World, actor: Entity, act: Act) -> list[str]:
    out: list[str] = []
    if actor.meters.get("loudness", 0.0) < THRESHOLD:
        return out
    if world.soundscape > world.place.quiet_limit:
        sig = ("noise", actor.id, act.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        world.facts["too_loud"] = True
        out.append(f"The sound bounced off the walls and felt a little too big for the room.")
    return out


def _worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    grownup = world.get("grownup")
    if not world.facts.get("too_loud"):
        return out
    sig = ("worry",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    grownup.memes["worry"] = grownup.memes.get("worry", 0.0) + 1
    child.memes["humor"] = child.memes.get("humor", 0.0) + 1
    out.append(f"{grownup.label_word.capitalize()} winced, but {child.id} grinned like a little stage star.")
    return out


def _calm_fix(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if not world.facts.get("resolved"):
        return out
    sig = ("calm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["calm"] = child.memes.get("calm", 0.0) + 1
    out.append("The room grew easier to hear, and the song kept its bounce.")
    return out


RULES = [_noise, _worry, _calm_fix]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_noise(world: World, actor: Entity, act: Act, gear: Optional[Gear]) -> dict:
    sim = world.copy()
    sim.soundscape += 2.0
    if gear:
        sim.soundscape = max(0.0, sim.soundscape - gear.reduces_noise)
    sim.get("child").meters["loudness"] = sim.soundscape
    too_loud = sim.soundscape > sim.place.quiet_limit
    return {"too_loud": too_loud, "soundscape": sim.soundscape}


def select_gear(world: World, act: Act) -> Optional[Gear]:
    for gear in GEAR:
        if gear.requires <= {"guitar", "drum", "electric"}:
            pred = predict_noise(world, world.get("child"), act, gear)
            if not pred["too_loud"]:
                return gear
    return None


def intro(world: World, child: Entity, parent: Entity) -> None:
    world.say(
        f"{child.id} was a little {next(t for t in child.memes if t)} child, except the only thing "
        f"they wanted that afternoon was a song with a big rock'n'roll grin."
    )


def love_music(world: World, child: Entity, act: Act) -> None:
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    world.say(
        f"{child.id} loved {act.gerund}, because every chord sounded like a joke told by a drum."
    )


def setup_band(world: World, child: Entity) -> None:
    world.say(
        f"In {world.place.label}, {child.id} lined up the guitar, the drum, and the tiny amp like a tiny band."
    )


def start_playing(world: World, child: Entity, act: Act) -> None:
    child.meters["loudness"] = child.meters.get("loudness", 0.0) + 2.0
    world.soundscape = child.meters["loudness"]
    world.say(
        f"{child.id} tried to {act.rush}, and the first laugh-loud riff filled the room."
    )
    propagate(world, narrate=True)


def warning(world: World, parent: Entity, child: Entity, act: Act) -> None:
    if not world.facts.get("too_loud"):
        return
    parent.memes["patience"] = parent.memes.get("patience", 0.0) + 1
    world.say(
        f'"That is a very brave guitar," {parent.pronoun("subject").capitalize()} said, '
        f'"but it is also a very loud guitar."'
    )
    world.say(
        f'"If you keep that up, {act.risk}," {parent.label_word} added with a half-smile.'
    )


def joke_back(world: World, child: Entity, parent: Entity) -> None:
    child.memes["humor"] = child.memes.get("humor", 0.0) + 1
    world.say(
        f'{child.id} blinked and said, "I can be quieter. I just did not know rock stars came with volume knobs."'
    )
    world.say(
        f'{parent.label_word} snorted a laugh, which made the whole argument feel less sharp.'
    )


def offer_fix(world: World, child: Entity, parent: Entity, act: Act) -> Optional[Gear]:
    gear = select_gear(world, act)
    if gear is None:
        return None
    world.say(
        f'"How about we {gear.prep}?" {parent.label_word} asked. "Then your rock'n'roll can still sparkle."'
    )
    return gear


def accept_fix(world: World, child: Entity, parent: Entity, act: Act, gear: Gear) -> None:
    child.memes["pride"] = child.memes.get("pride", 0.0) + 1
    child.memes["calm"] = child.memes.get("calm", 0.0) + 1
    world.facts["resolved"] = True
    if gear.id == "headphones":
        world.say(
            f'{child.id} put on the headphones and laughed, "Now I sound like a secret stadium!"'
        )
    elif gear.id == "mute":
        world.say(
            f'{child.id} clipped on the mute and said, "It is still rock'n'roll. It is just rock'n'roll with good manners."'
        )
    else:
        world.say(
            f'{child.id} smiled and said, "A cushion drum! That is the funniest serious idea I have ever heard."'
        )
    world.say(
        f"After that, {gear.tail}, and {child.id} kept playing while {parent.label_word} listened from the doorway, smiling."
    )


def tell(place: Place, act: Act, hero_name: str, parent_type: str, trait: str) -> World:
    world = World(place)
    child = world.add(Entity(id="child", kind="character", type="boy" if hero_name in {"Noah", "Ben", "Leo", "Finn"} else "girl", label=hero_name, memes={trait: 1.0}))
    parent = world.add(Entity(id="grownup", kind="character", type=parent_type, label=f"the {parent_type}"))
    for iid, item in INSTRUMENTS.items():
        world.add(Entity(id=iid, type=item.type, label=item.label, phrase=item.phrase, plural=item.plural, owner="child"))
    intro(world, child, parent)
    world.para()
    love_music(world, child, act)
    setup_band(world, child)
    world.para()
    start_playing(world, child, act)
    warning(world, parent, child, act)
    joke_back(world, child, parent)
    gear = offer_fix(world, child, parent, act)
    world.para()
    if gear:
        accept_fix(world, child, parent, act, gear)
        world.facts["gear"] = gear
    world.facts.update(child=child, grownup=parent, act=act, place=place)
    return world


@dataclass
class StoryParams:
    place: str
    activity: str
    name: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [(p, a) for p, place in SETTINGS.items() for a in place.affords for _ in [0] if reasonableness_gate(place, ACTIVITIES[a])]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    act = f["act"]
    return [
        f'Write a short slice-of-life story for a child who wants to "{act.keyword}" in the apartment and makes a funny joke about it.',
        f"Tell a gentle rock'n'roll story where {child.label} wants to {act.verb} and a grown-up worries about the noise.",
        f'Write a small humorous dialogue story that includes the words "rock\'n\'roll" and ends with a quieter but still cheerful song.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["grownup"]
    act = f["act"]
    gear = f.get("gear")
    place = f["place"].label
    qa = [
        QAItem(
            question=f"What did {child.label} want to do in {place}?",
            answer=f"{child.label} wanted to {act.verb}, because {child.id} loved rock'n'roll music.",
        ),
        QAItem(
            question=f"Why did {parent.label_word} worry when {child.label} started playing?",
            answer=f"{parent.label_word.capitalize()} worried because the music was too loud for {place}, and the sound might bother the room.",
        ),
        QAItem(
            question=f"What funny thing did {child.label} say about being quiet?",
            answer=f"{child.label} joked that rock stars must come with volume knobs, which made the grown-up laugh.",
        ),
    ]
    if gear:
        qa.append(
            QAItem(
                question=f"How did {gear.label} help the music fit the room?",
                answer=f"{gear.label.capitalize()} made the sound smaller, so {child.label} could keep playing without making the whole place feel too loud.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is rock'n'roll?",
            answer="Rock'n'roll is a kind of lively music with strong rhythms, guitars, and a beat that makes people want to move.",
        ),
        QAItem(
            question="Why can loud music be hard in an apartment?",
            answer="Loud music can travel through walls and floors, so people nearby might hear it even when they did not choose to listen.",
        ),
        QAItem(
            question="What is a compromise?",
            answer="A compromise is a choice that helps different people get some of what they want without making things unfair.",
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
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  soundscape={world.soundscape}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
activity(A) :- act(A).
rock_story(P, A) :- affords(P, A), place(P), activity(A).

too_loud(P, A) :- quiet_limit(P, Q), sound_after(A, S), S > Q.
needs_fix(P, A) :- too_loud(P, A), has_gear_fix(A).

has_gear_fix(A) :- gear_fix(A, _).
usable_story(P, A) :- rock_story(P, A), has_gear_fix(A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        lines.append(asp.fact("quiet_limit", pid, int(p.quiet_limit * 10)))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("act", aid))
        lines.append(asp.fact("sound_after", aid, 20))
    for g in GEAR:
        lines.append(asp.fact("gear_fix", "rock", g.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show usable_story/2.")
    model = asp.one_model(program)
    clingo_set = set(asp.atoms(model, "usable_story"))
    python_set = set((p, a) for p, a in valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid story combinations exist.")
    place_id, act_id = rng.choice(sorted(combos))
    if args.place and args.place != place_id:
        raise StoryError("(No valid combination matches the given place.)")
    if args.activity and args.activity != act_id:
        raise StoryError("(No valid combination matches the given activity.)")
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENTS)
    trait = args.trait or rng.choice(TRAITS) if hasattr(args, "trait") else rng.choice(TRAITS)
    return StoryParams(place=place_id, activity=act_id, name=name, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], params.name, params.parent, params.trait)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life rock'n'roll humor storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=PARENTS)
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


CURATED = [
    StoryParams(place="apartment", activity="rock", name="Maya", parent="mother", trait="silly"),
    StoryParams(place="living_room", activity="practice", name="Leo", parent="father", trait="playful"),
    StoryParams(place="garage", activity="rock", name="Ivy", parent="mother", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show usable_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show usable_story/2."))
        combos = sorted(set(asp.atoms(model, "usable_story")))
        print(f"{len(combos)} usable story combos:\n")
        for p, a in combos:
            print(f"  {p:12} {a}")
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
            params = resolve_params(args, random.Random(seed))
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
