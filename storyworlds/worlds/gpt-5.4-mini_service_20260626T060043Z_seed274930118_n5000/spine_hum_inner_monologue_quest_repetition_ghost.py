#!/usr/bin/env python3
"""
storyworlds/worlds/spine_hum_inner_monologue_quest_repetition_ghost.py
======================================================================

A small ghost-story world with:
- spine-sense fear and shivers
- a low hum that repeats through the rooms
- an inner monologue that helps the hero keep going
- a quest to uncover the source of the sound
- repetition as a deliberate narrative instrument

The domain is child-facing and constrained: a quiet place, a strange hum,
a hesitant search, and a gentle reveal that changes the air of the story.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    placed_in: str = ""
    carries: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"dust": 0.0, "glow": 0.0}
        if not self.memes:
            self.memes = {"fear": 0.0, "curiosity": 0.0, "resolve": 0.0, "comfort": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    mood: str
    rooms: list[str]
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    room: str
    hum_words: list[str]
    ghostly: bool = False


@dataclass
class Quest:
    id: str
    seek: str
    method: str
    repeat_line: str
    reveal: str
    ending: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    active_hum: float = 0.0
    active_room: str = ""
    repeats: int = 0

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.active_hum = self.active_hum
        clone.active_room = self.active_room
        clone.repeats = self.repeats
        return clone


SETTINGS = {
    "old_house": Setting(
        place="the old house",
        mood="quiet",
        rooms=["hall", "stairs", "attic", "nursery"],
        affords={"listen", "search", "remember"},
    ),
    "sleeping_school": Setting(
        place="the sleeping school",
        mood="still",
        rooms=["hall", "music room", "library", "stage"],
        affords={"listen", "search", "remember"},
    ),
    "moon_garden": Setting(
        place="the moon garden",
        mood="silver",
        rooms=["path", "shed", "bench", "gate"],
        affords={"listen", "search", "remember"},
    ),
}

CLUES = {
    "music_box": Clue(
        id="music_box",
        label="a tiny music box",
        room="attic",
        hum_words=["hum", "humming", "soft notes"],
        ghostly=False,
    ),
    "vent_pipe": Clue(
        id="vent_pipe",
        label="a loose vent pipe",
        room="hall",
        hum_words=["hum", "drone", "buzz"],
        ghostly=False,
    ),
    "ghost_lamp": Clue(
        id="ghost_lamp",
        label="a pale lamp left on behind a curtain",
        room="library",
        hum_words=["hum", "murmur", "white light"],
        ghostly=True,
    ),
}

QUESTS = {
    "find_sound": Quest(
        id="find_sound",
        seek="the source of the hum",
        method="follow the sound room by room",
        repeat_line="The hum came again, low and patient.",
        reveal="The sound was not a warning at all; it was a small, lonely thing trying to be heard.",
        ending="The house felt less empty once the noise had a name.",
    ),
    "return_memory": Quest(
        id="return_memory",
        seek="the lost note of a memory",
        method="walk slowly and listen for the next clue",
        repeat_line="The hum slipped past the walls again.",
        reveal="The repeating sound was leading the child toward a forgotten keepsake.",
        ending="What had felt spooky turned into something tender and close.",
    ),
}

NAMES = ["Mina", "Noah", "Iris", "Eli", "June", "Theo", "Ada", "Finn"]


def reasonableness_gate(setting: Setting, clue: Clue, quest: Quest) -> Optional[str]:
    if "listen" not in setting.affords or "search" not in setting.affords:
        return "This setting does not support a listening-and-searching ghost story."
    if clue.room not in setting.rooms:
        return f"The clue room {clue.room!r} does not exist in {setting.place}."
    if not quest.seek:
        return "The quest needs a clear thing to seek."
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CLUES:
            for q in QUESTS:
                err = reasonableness_gate(SETTINGS[s], CLUES[c], QUESTS[q])
                if err is None:
                    combos.append((s, c, q))
    return combos


@dataclass
class StoryParams:
    setting: str
    clue: str
    quest: str
    name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with spine, hum, inner monologue, quest, and repetition.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name", choices=NAMES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.quest is None or c[2] == args.quest)]
    if not combos:
        raise StoryError("No valid ghost story matches the given options.")
    setting, clue, quest = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        clue=clue,
        quest=quest,
        name=args.name or rng.choice(NAMES),
    )


def _inner_monologue(hero: Entity, line: str) -> str:
    hero.memes["resolve"] += 0.5
    return f"{hero.pronoun('subject').capitalize()} thought, \"{line}\""


def _spine_react(hero: Entity, strength: float) -> str:
    hero.memes["fear"] += strength
    return f"A prickly feeling ran up {hero.pronoun('possessive')} spine."


def _hum(world: World, clue: Clue, room: str) -> str:
    world.active_room = room
    world.active_hum += 1
    world.repeats += 1
    return clue.hum_words[world.repeats % len(clue.hum_words)].capitalize() + "."

def tell(setting: Setting, clue: Clue, quest: Quest, hero_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="child"))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label="a quiet ghost"))
    item = world.add(Entity(id=clue.id, type="thing", label=clue.label, placed_in=clue.room))
    world.facts.update(hero=hero, ghost=ghost, item=item, quest=quest, clue=clue, setting=setting)

    world.say(f"{hero_name} entered {setting.place}, where everything felt {setting.mood} and still.")
    world.say(_spine_react(hero, 1.0))
    world.say(_inner_monologue(hero, "It's only a house. It's only a house. I can listen carefully."))

    world.para()
    world.say(f"{hero_name} had a quest: to find {quest.seek}.")
    world.say(f"{hero_name} decided to {quest.method}.")
    world.say(_hum(world, clue, setting.rooms[0]))
    world.say(quest.repeat_line)

    for room in setting.rooms[1:]:
        world.para()
        world.say(f"{hero_name} went to the {room}.")
        if room == clue.room:
            world.say(_hum(world, clue, room))
            world.say(_inner_monologue(hero, "The sound is closer now. It is leading me somewhere, not chasing me."))
            world.say(f"In the {room}, {hero_name} found {clue.label}.")
            if clue.ghostly:
                ghost.meters["glow"] += 1
                ghost.memes["comfort"] += 1
                world.say(f"Near it, the ghost gave off a pale glow and nodded, as if relieved.")
            else:
                world.say(f"The small thing kept the hum alive, gentle and repetitive, like a song that was trying to remember itself.")
            break
        else:
            world.say(_hum(world, clue, room))
            world.say(_inner_monologue(hero, "Keep going. Listen again. The next room may know."))

    world.para()
    world.say(quest.reveal)
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 0.5)
    hero.memes["comfort"] += 1.0
    world.say(f"{hero_name} felt the prickling in {hero_name}'s spine soften.")
    world.say(quest.ending)
    world.say(f"{hero_name} left with the hum turned into a memory, and the dark place seemed less lonely than before.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a ghost story for a child about {f['hero'].id} hearing a hum in {f['setting'].place}.",
        f"Tell a gentle spooky story with an inner monologue, a quest, and repetition that leads to {f['item'].label}.",
        f"Write a story where a child follows a hum room by room until the sound makes sense.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    clue = f["clue"]
    quest = f["quest"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"What was {hero.id}'s quest in {setting.place}?",
            answer=f"{hero.id} wanted to find {quest.seek} by following the hum room by room.",
        ),
        QAItem(
            question=f"What kept repeating as {hero.id} searched?",
            answer=f"The hum kept coming back, low and patient, which made the search feel spooky but calm.",
        ),
        QAItem(
            question=f"What did {hero.id} find in the room where the sound was strongest?",
            answer=f"{hero.id} found {clue.label} in the {clue.room}, and that made the repeating sound make sense.",
        ),
        QAItem(
            question=f"How did {hero.id} feel when the story began?",
            answer=f"{hero.id} felt scared at first, because {setting.place} was quiet and the strange hum touched {hero.pronoun('possessive')} spine.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The place felt less lonely, and the hum became a sign of something small and understandable instead of something scary.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a spine?",
            answer="A spine is the row of bones down the middle of your back that helps hold your body up.",
        ),
        QAItem(
            question="What does a hum sound like?",
            answer="A hum is a soft, steady sound, like something quietly singing without words.",
        ),
        QAItem(
            question="Why do people repeat a line in a story?",
            answer="Repetition can make a story feel memorable, rhythmic, and a little mysterious.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the silent thinking a character does inside their own head.",
        ),
        QAItem(
            question="What is a quest in a story?",
            answer="A quest is a story goal where a character looks for something, solves a problem, or tries to discover an answer.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: type={e.type} meters={{{', '.join(f'{k}:{v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}:{v}' for k, v in e.memes.items() if v)}}}"
        )
    lines.append(f"active_room={world.active_room}")
    lines.append(f"repeats={world.repeats}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- set(S).
clue(C) :- clue_id(C).
quest(Q) :- quest_id(Q).

valid(S,C,Q) :- set(S), clue_id(C), quest_id(Q), rooms(S,R), clue_room(C,R), afford(S,listen), afford(S,search).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("set", sid))
        for room in s.rooms:
            lines.append(asp.fact("rooms", sid, room))
        for a in sorted(s.affords):
            lines.append(asp.fact("afford", sid, a))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue_id", cid))
        lines.append(asp.fact("clue_room", cid, c.room))
    for qid in QUESTS:
        lines.append(asp.fact("quest_id", qid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def build_story_params_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    clue = CLUES[params.clue]
    quest = QUESTS[params.quest]
    world = tell(setting, clue, quest, params.name)
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


CURATED = [
    StoryParams(setting="old_house", clue="music_box", quest="find_sound", name="Mina"),
    StoryParams(setting="sleeping_school", clue="ghost_lamp", quest="return_memory", name="Theo"),
    StoryParams(setting="moon_garden", clue="vent_pipe", quest="find_sound", name="Iris"),
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
        print(f"{len(combos)} compatible stories:\n")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
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
