#!/usr/bin/env python3
"""
storyworlds/worlds/lodge_bedroom_mystery_to_solve_quest_space.py
=================================================================

A standalone story world for a cozy space-adventure mystery set in a bedroom
at a lodge.

Seed tale inspiration:
---
A child stays in a lodge bedroom that feels like a tiny spaceship cabin. A
mystery appears when a small glowing star-map goes missing. The child follows
clues around the room, asks a trusted grown-up, and turns the search into a
quest. In the end, the missing item is found in an unexpected place, and the
bedroom feels like a safe launchpad again.

World premise:
---
A lodge bedroom can become a pretend starship. The child has a quest for a
lost moon key needed to open a wooden chest. The room offers a few simple
places to search: under the bed, in a boot tray, behind the curtain, and beside
the lamp. The tension comes from the missing key and the promise that the quest
will only succeed if the child follows clues carefully instead of rushing.

Narrative instruments:
---
- Mystery to solve: missing moon key
- Quest: search the lodge bedroom, gather clues, and open the chest
- Space adventure style: star maps, captain talk, launch pings, and calm awe

State model:
---
- Physical meters track location, hiding, discovered clues, and object ownership.
- Emotional memes track worry, curiosity, confidence, and relief.
- The simulated state drives the prose; the ending proves what changed.

ASP twin:
---
The inline ASP rules mirror the Python reasonableness gate, which only accepts
stories where the mystery object is plausibly hidden in the room and the quest
has a valid clue path.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, replace
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

ROOMS = ("bed", "desk", "lamp", "curtain", "boot_tray", "window", "shelf")


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    hidden_in: str = ""
    found_by: str = ""
    opened: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the bedroom in the lodge"
    indoors: bool = True


@dataclass
class Mystery:
    id: str
    name: str
    missing_phrase: str
    hiding_place: str
    clue_place: str
    final_place: str
    consequence: str


@dataclass
class Quest:
    id: str
    title: str
    start_line: str
    clue_line: str
    reveal_line: str
    end_line: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = {k: replace(v, meters=dict(v.meters), memes=dict(v.memes)) for k, v in self.entities.items()}
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


def meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def meme(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def add_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def reset_meme(ent: Entity, key: str, amount: float = 0.0) -> None:
    ent.memes[key] = amount


def clue_text(mystery: Mystery) -> str:
    return {
        "bed": "a small silver thread near the pillow",
        "desk": "a dusty ring drawn in the shape of a moon",
        "lamp": "a glow that pointed toward the shelf",
        "curtain": "a tiny rustle by the window",
        "boot_tray": "a dusty print beside the rain boots",
        "window": "a star sticker stuck to the glass",
        "shelf": "a hollow tap behind a book",
    }.get(mystery.clue_place, "a curious clue")


def reasonableness_gate(mystery: Mystery, quest: Quest) -> Optional[str]:
    if mystery.hiding_place not in ROOMS:
        return "The missing item needs a plausible hiding place inside the bedroom."
    if quest.title.strip() == "":
        return "The quest needs a title."
    if mystery.clue_place not in ROOMS or mystery.final_place not in ROOMS:
        return "The clue path must stay inside the room."
    if mystery.clue_place == mystery.hiding_place:
        return "The clue should not be identical to the hiding place; the search needs a turn."
    if mystery.final_place != mystery.hiding_place:
        return "The ending place should match the hiding place so the mystery can be solved."
    return None


def inspect(world: World, hero: Entity, place: str) -> str:
    add_meme(hero, "curiosity", 0.5)
    return f"{hero.id} checked {place} like a tiny captain scanning a starfield."


def discover_clue(world: World, hero: Entity, mystery: Mystery) -> str:
    add_meter(world.get(mystery.id), "clue_seen", 1)
    add_meme(hero, "confidence", 0.5)
    return f"There, {clue_text(mystery)} appeared, and {hero.id} knew the quest had a trail."


def find_mystery(world: World, hero: Entity, mystery: Mystery) -> str:
    obj = world.get(mystery.id)
    if obj.hidden_in != mystery.hiding_place:
        raise StoryError("The mystery object is not where the model expected it to be.")
    obj.found_by = hero.id
    add_meter(obj, "found", 1)
    add_meme(hero, "relief", 1)
    add_meme(hero, "joy", 1)
    return f"At last, {hero.id} found the {obj.label} tucked in {mystery.hiding_place}."


def open_chest(world: World, hero: Entity, chest: Entity) -> str:
    chest.opened = True
    add_meme(hero, "joy", 0.5)
    return f"The chest clicked open like a hatch on a little starship."


def tell(world: World, hero: Entity, grownup: Entity, mystery: Mystery, quest: Quest) -> World:
    star_object = world.get(mystery.id)
    chest = world.get("chest")

    world.say(f"{hero.id} was staying in {world.setting.place}, where the bedroom felt like a quiet space cabin.")
    world.say(f"{hero.id} loved the room because it had a bed, a lamp, and a window that could pretend to be a launch screen.")
    world.say(f"That morning, a mystery began: the {mystery.missing_phrase} was gone.")
    world.say(f"{hero.id} wanted to solve it fast, so {hero.pronoun('subject')} turned the search into a quest called {quest.title}.")

    world.para()
    world.say(quest.start_line)
    add_meme(hero, "worry", 1)
    add_meme(hero, "curiosity", 1)
    add_meme(grownup, "calm", 1)
    world.say(f"{grownup.id} pointed to the room and said, \"Slow steps, bright eyes, and one clue at a time.\"")

    for place in (mystery.clue_place, "window", mystery.hiding_place):
        world.para()
        world.say(inspect(world, hero, place))
        if place == mystery.clue_place:
            world.say(discover_clue(world, hero, mystery))
        elif place == "window":
            add_meme(hero, "worry", -0.5)
            world.say(f"The moon-light on the glass made the clue feel even more real.")
        elif place == mystery.hiding_place:
            world.say(find_mystery(world, hero, mystery))

    world.para()
    world.say(open_chest(world, hero, chest))
    world.say(f"Inside, the chest held a map and a small note, and the note fit the missing key exactly.")
    world.say(quest.reveal_line)
    world.say(quest.end_line)
    world.say(f"The bedroom felt cozy again, but now it also felt like a finished mission on a friendly starship.")

    add_meter(star_object, "restored", 1)
    add_meme(hero, "confidence", 0.5)
    add_meme(hero, "worry", -1)
    add_meme(hero, "relief", 0.5)

    world.facts.update(
        hero=hero,
        grownup=grownup,
        mystery=mystery,
        quest=quest,
        chest=chest,
        solved=True,
    )
    return world


SETTINGS = {
    "lodge_bedroom": Setting(place="the bedroom in the lodge"),
}

MYSTERIES = {
    "moon_key": Mystery(
        id="moon_key",
        name="moon key",
        missing_phrase="little moon key",
        hiding_place="boot_tray",
        clue_place="lamp",
        final_place="boot_tray",
        consequence="the chest can open",
    ),
    "star_compass": Mystery(
        id="star_compass",
        name="star compass",
        missing_phrase="star compass",
        hiding_place="shelf",
        clue_place="curtain",
        final_place="shelf",
        consequence="the map can be read",
    ),
    "signal_note": Mystery(
        id="signal_note",
        name="signal note",
        missing_phrase="signal note",
        hiding_place="bed",
        clue_place="desk",
        final_place="bed",
        consequence="the route can be followed",
    ),
}

QUESTS = {
    "find_the_key": Quest(
        id="find_the_key",
        title="Quest for the Moon Key",
        start_line="The first mission was simple: search the room like a careful explorer on a moonbase.",
        clue_line="A clue waited in plain sight, and the bedroom wanted someone patient enough to notice it.",
        reveal_line="The missing piece had been hiding the whole time, just not where the first look had searched.",
        end_line="With the key back in hand, the quest felt complete.",
    ),
    "open_the_chest": Quest(
        id="open_the_chest",
        title="Quest for the Quiet Chest",
        start_line="The mission was to find what could unlock the old chest without waking the whole lodge.",
        clue_line="Each corner of the room whispered a different hint.",
        reveal_line="The answer was smaller than a boot and brighter than a star sticker.",
        end_line="The chest was no longer a secret, only a treasure box.",
    ),
}

GROWNUPS = ["Mom", "Dad", "Aunt June", "Uncle Ray"]
HEROES = ["Mina", "Leo", "Tia", "Noah", "Iris", "Owen"]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    quest: str
    name: str
    grownup: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    quest = f["quest"]
    return [
        f'Write a gentle space-adventure mystery story set in a lodge bedroom where {hero.id} must solve the {mystery.name}.',
        f"Tell a story about {hero.id} turning a missing {mystery.name} into a quest called {quest.title}.",
        f'Write a child-friendly bedroom mystery with a cozy space-ship feeling and an ending that proves the {mystery.name} was found.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    grownup: Entity = f["grownup"]
    mystery: Mystery = f["mystery"]
    quest: Quest = f["quest"]
    chest: Entity = f["chest"]

    return [
        QAItem(
            question=f"Where was {hero.id} staying when the mystery began?",
            answer=f"{hero.id} was staying in {world.setting.place}, in a bedroom that felt like a little spaceship cabin.",
        ),
        QAItem(
            question=f"What was missing in the story?",
            answer=f"The missing thing was the {mystery.missing_phrase}. That was the mystery {hero.id} needed to solve.",
        ),
        QAItem(
            question=f"Who helped {hero.id} keep calm during the quest?",
            answer=f"{grownup.id} helped by reminding {hero.id} to move slowly and look for one clue at a time.",
        ),
        QAItem(
            question=f"What did the clue near the lamp help {hero.id} do?",
            answer=f"It helped {hero.id} know where to search next, which kept the quest moving toward the hiding place.",
        ),
        QAItem(
            question=f"What happened when {hero.id} found the missing item?",
            answer=f"{hero.id} found the {mystery.name} in {mystery.hiding_place}, and that solved the mystery.",
        ),
        QAItem(
            question=f"What opened after the quest was finished?",
            answer=f"The chest opened after the quest was finished, and the bedroom felt like a tiny starship again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something unknown that people try to figure out by looking for clues.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a purpose-driven search or journey to reach a goal.",
        ),
        QAItem(
            question="Why do people use clues?",
            answer="People use clues because clues help them make smart guesses and find answers.",
        ),
        QAItem(
            question="What is a lodge?",
            answer="A lodge is a cozy place where people can stay, often near woods, mountains, or a quiet getaway spot.",
        ),
        QAItem(
            question="Why can a bedroom feel calm?",
            answer="A bedroom can feel calm because it is usually a quiet place with soft things like a bed and pillow.",
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
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.found_by:
            bits.append(f"found_by={e.found_by}")
        if e.opened:
            bits.append("opened=True")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure bedroom mystery story world.")
    ap.add_argument("--setting", choices=SETTINGS, default="lodge_bedroom")
    ap.add_argument("--mystery", choices=MYSTERIES, default=None)
    ap.add_argument("--quest", choices=QUESTS, default=None)
    ap.add_argument("--name", choices=HEROES, default=None)
    ap.add_argument("--grownup", choices=GROWNUPS, default=None)
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
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    quest = args.quest or rng.choice(list(QUESTS))
    name = args.name or rng.choice(HEROES)
    grownup = args.grownup or rng.choice(GROWNUPS)
    err = reasonableness_gate(MYSTERIES[mystery], QUESTS[quest])
    if err:
        raise StoryError(err)
    return StoryParams(
        setting=args.setting,
        mystery=mystery,
        quest=quest,
        name=name,
        grownup=grownup,
    )


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    quest = QUESTS[params.quest]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type="boy" if params.name in {"Leo", "Noah", "Owen"} else "girl"))
    grownup = world.add(Entity(id=params.grownup, kind="character", type="adult"))
    obj = world.add(Entity(id=mystery.id, type="thing", label=mystery.name, phrase=mystery.missing_phrase, hidden_in=mystery.hiding_place))
    chest = world.add(Entity(id="chest", type="thing", label="wooden chest", phrase="a small wooden chest"))

    # Initialize state.
    add_meme(hero, "worry", 1)
    add_meme(hero, "curiosity", 1)
    add_meme(grownup, "calm", 1)
    add_meter(obj, "missing", 1)

    tell(world, hero, grownup, mystery, quest)

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


ASP_RULES = r"""
missing(M) :- mystery(M).
quest_ok(Q) :- quest(Q).
room(rbed) :- room_name("bed").
room(rdesk) :- room_name("desk").
room(rlamp) :- room_name("lamp").
room(rcurtain) :- room_name("curtain").
room(rboottray) :- room_name("boot_tray").
room(rwindow) :- room_name("window").
room(rshelf) :- room_name("shelf").

valid_mystery(M) :- mystery(M), hiding_place(M,H), clue_place(M,C), final_place(M,H2), H = H2, room(RH), room(RC), room(RF).
valid_story(M,Q) :- valid_mystery(M), quest(Q).
#show valid_mystery/1.
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for room in ROOMS:
        lines.append(asp.fact("room_name", room))
    for m in MYSTERIES.values():
        lines.append(asp.fact("mystery", m.id))
        lines.append(asp.fact("hiding_place", m.id, m.hiding_place))
        lines.append(asp.fact("clue_place", m.id, m.clue_place))
        lines.append(asp.fact("final_place", m.id, m.final_place))
    for q in QUESTS.values():
        lines.append(asp.fact("quest", q.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_mystery/1.\n#show valid_story/2."))
    shown = set((s.name, tuple(a.name if a.type != 1 else a.number for a in s.arguments)) for s in model)
    python_valid = set()
    for m in MYSTERIES.values():
        if reasonableness_gate(m, next(iter(QUESTS.values()))) is None:
            python_valid.add(("valid_mystery", (m.id,)))
    if shown:
        return 0
    raise StoryError("ASP verification failed: no model found.")


CURATED = [
    StoryParams(setting="lodge_bedroom", mystery="moon_key", quest="find_the_key", name="Mina", grownup="Mom"),
    StoryParams(setting="lodge_bedroom", mystery="star_compass", quest="open_the_chest", name="Leo", grownup="Dad"),
    StoryParams(setting="lodge_bedroom", mystery="signal_note", quest="find_the_key", name="Iris", grownup="Aunt June"),
]


def asp_valid() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_mystery/1.\n#show valid_story/2."))
    return sorted((sym.name, tuple(arg.name for arg in sym.arguments)) for sym in model)


def explain_rejection(mystery: Mystery, quest: Quest) -> str:
    return f"(No story: {reasonableness_gate(mystery, quest)})"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_mystery/1.\n#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_mystery/1.\n#show valid_story/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
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
