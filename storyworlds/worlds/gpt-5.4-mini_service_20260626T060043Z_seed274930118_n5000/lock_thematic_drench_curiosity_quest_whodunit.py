#!/usr/bin/env python3
"""
storyworlds/worlds/lock_thematic_drench_curiosity_quest_whodunit.py
===================================================================

A small whodunit story world about a curious quest, a locked door, and a
thematic drench of evidence that helps solve the mystery.

The seed idea:
---
A child is warned not to open a locked box during a rainy visit. Curiosity
pulls them into a little quest to find the key, and a sudden drench reveals
the final clue. The ending should feel like a whodunit: someone noticed the
wrong detail, followed the trail, and solved the puzzle.

World model:
- Physical meters track things like dry/wet, locked/unlocked, open/closed,
  hidden/revealed, and evidence strength.
- Emotional memes track curiosity, worry, relief, and confidence.
- The story advances by world state, not by swapping nouns in a fixed paragraph.

Narrative instruments:
- Curiosity: a gentle urge that pushes the hero to investigate.
- Quest: a search for a missing key, clue, or answer.
- Drench: a sudden soaking rain or spill that reveals hidden evidence.
- Whodunit tone: observation, suspicion, clue-trail, reveal, resolution.
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
    carries: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["wet", "dry", "locked", "open", "hidden", "revealed", "evidence"]:
            self.meters.setdefault(k, 0.0)
        for k in ["curiosity", "worry", "relief", "confidence", "alarm", "doubt"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool
    rain_prone: bool = False


@dataclass
class Mystery:
    id: str
    clue_word: str
    locked_thing: str
    missing_item: str
    drench_kind: str
    reveal_method: str
    end_image: str


class World:
    def __init__(self, setting: Setting, mystery: Mystery) -> None:
        self.setting = setting
        self.mystery = mystery
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        for line in self.lines:
            if line == "":
                if out and out[-1] != "":
                    out.append("")
            else:
                out.append(line)
        return "\n".join(out).replace("\n\n\n", "\n\n")


def _speak(name: str, kind: str, pos: str = "subject") -> str:
    return {"subject": name, "object": name, "possessive": name + "'s"}[pos]


def join_names(names: list[str]) -> str:
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return ", ".join(names[:-1]) + f", and {names[-1]}"


def wet_enough(e: Entity) -> bool:
    return e.meters["wet"] >= THRESHOLD


def locked(e: Entity) -> bool:
    return e.meters["locked"] >= THRESHOLD


def hidden(e: Entity) -> bool:
    return e.meters["hidden"] >= THRESHOLD and e.meters["revealed"] < THRESHOLD


def reveal(e: Entity) -> None:
    e.meters["hidden"] = 0.0
    e.meters["revealed"] = 1.0


def unlock(e: Entity) -> None:
    e.meters["locked"] = 0.0
    e.meters["open"] = 1.0


def apply_drench(world: World, hero: Entity, target: Entity, clue: Entity) -> None:
    hero.meters["wet"] += 1
    target.meters["wet"] += 1
    clue.meters["wet"] += 1
    hero.memes["alarm"] += 1
    if hidden(clue):
        reveal(clue)
        clue.meters["evidence"] += 1
        world.say(
            f"A sudden {world.mystery.drench_kind} drench splashed the scene, and a dark mark "
            f"showed up on the {clue.label}."
        )
    else:
        world.say(f"A sudden {world.mystery.drench_kind} drench swept through the room.")


def build_world(setting: Setting, mystery: Mystery, hero_name: str, hero_type: str,
                helper_name: str, helper_type: str, suspect_name: str, suspect_type: str) -> World:
    w = World(setting, mystery)

    hero = w.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        phrase=f"a curious little {hero_type}",
    ))
    helper = w.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        label=helper_name,
        phrase=f"a careful {helper_type}",
    ))
    suspect = w.add(Entity(
        id=suspect_name,
        kind="character",
        type=suspect_type,
        label=suspect_name,
        phrase=f"a watchful {suspect_type}",
    ))
    lockbox = w.add(Entity(
        id="lockbox",
        type="box",
        label=mystery.locked_thing,
        phrase=f"the {mystery.locked_thing}",
    ))
    lockbox.meters["locked"] = 1.0
    lockbox.meters["open"] = 0.0
    lockbox.meters["hidden"] = 1.0

    key = w.add(Entity(
        id="key",
        type="key",
        label="key",
        phrase="the missing key",
        owner=helper.id,
        caretaker=helper.id,
    ))
    key.meters["hidden"] = 1.0

    clue = w.add(Entity(
        id="clue",
        type="note",
        label="note",
        phrase=f"a small {mystery.clue_word} clue",
    ))
    clue.meters["hidden"] = 1.0

    hero.carries = False
    helper.carries = False
    suspect.carries = False

    # Initial state
    hero.memes["curiosity"] = 1.0
    helper.memes["worry"] = 0.5
    suspect.memes["doubt"] = 0.5
    lockbox.meters["wet"] = 0.0

    w.facts.update(
        hero=hero,
        helper=helper,
        suspect=suspect,
        lockbox=lockbox,
        key=key,
        clue=clue,
        setting=setting,
        mystery=mystery,
    )
    return w


def tell(world: World) -> World:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    suspect: Entity = f["suspect"]
    lockbox: Entity = f["lockbox"]
    key: Entity = f["key"]
    clue: Entity = f["clue"]
    m: Mystery = f["mystery"]

    # Act 1: setup and the locked mystery.
    world.say(
        f"On a {('rainy' if world.setting.rain_prone else 'quiet')} day at {world.setting.place}, "
        f"{hero.label} noticed the locked {m.locked_thing} and stared at it for a long moment."
    )
    world.say(
        f"{hero.label} had a big streak of curiosity, and that made {hero.pronoun('object')} wonder "
        f"what could be hiding inside."
    )
    world.say(
        f"{helper.label} warned that the {m.locked_thing} should stay shut until the missing key was found."
    )

    world.para()

    # Act 2: the quest.
    world.say(
        f"So {hero.label} started a little quest through {world.setting.place}, searching under cloth, behind jars, "
        f"and around every corner for the key."
    )
    hero.memes["curiosity"] += 1
    hero.memes["confidence"] += 0.5

    # A clue trail.
    if hidden(key):
        key.meters["hidden"] = 0.0
        key.meters["revealed"] = 1.0
        world.say(
            f"Near a bright window, {hero.label} spotted a tiny shine, and there was the key tucked under a napkin."
        )
        world.say(
            f"{helper.label} smiled, because the search was turning into a proper whodunit clue trail."
        )

    # The suspect adds doubt.
    suspect.memes["doubt"] += 1
    world.say(
        f"Still, {suspect.label} looked uneasy, as if {suspect.pronoun('subject')} knew more than {suspect.pronoun('subject')} was saying."
    )

    world.para()

    # The drench reveal.
    if world.setting.rain_prone:
        apply_drench(world, hero, lockbox, clue)
    else:
        # Even indoors, the drench can come from a tipped pitcher or leaking roof.
        apply_drench(world, hero, lockbox, clue)

    # The clue matters if wet.
    if clue.meters["revealed"] >= THRESHOLD:
        world.say(
            f"The wet mark pointed straight to the underside of the clue, and that showed why the lock had not been opened earlier."
        )

    # The reveal and resolution.
    if key.meters["revealed"] >= THRESHOLD:
        unlock(lockbox)
        lockbox.meters["open"] = 1.0
        hero.memes["curiosity"] += 0.5
        hero.memes["relief"] += 1.0
        helper.memes["worry"] = 0.0
        world.say(
            f"{hero.label} used the key and the lock clicked open at last."
        )
        world.say(
            f"Inside the {m.locked_thing} was the missing {m.missing_item}, and the clue made sense at once: "
            f"{suspect.label} had not stolen anything, only hidden the key to keep the surprise safe."
        )
        world.say(
            f"{helper.label} laughed softly, and the whole puzzle ended with {m.end_image}."
        )
    else:
        world.say(
            f"The key never turned up, so the mystery stayed closed and the story had no honest ending."
        )
    return world


SETTINGS = {
    "reading_room": Setting(place="the reading room", indoors=True, rain_prone=False),
    "attic": Setting(place="the attic", indoors=True, rain_prone=True),
    "porch": Setting(place="the porch", indoors=False, rain_prone=True),
}

MYSTERIES = {
    "music_box": Mystery(
        id="music_box",
        clue_word="thematic",
        locked_thing="music box",
        missing_item="silver button",
        drench_kind="rain",
        reveal_method="wet mark",
        end_image="a little silver button glinting in the open box",
    ),
    "cabinet": Mystery(
        id="cabinet",
        clue_word="lock",
        locked_thing="display cabinet",
        missing_item="toy compass",
        drench_kind="spill",
        reveal_method="water stain",
        end_image="a toy compass resting beside the open shelf",
    ),
    "chest": Mystery(
        id="chest",
        clue_word="curiosity",
        locked_thing="wooden chest",
        missing_item="red ribbon",
        drench_kind="drench",
        reveal_method="dark stain",
        end_image="a red ribbon shining on the chest floor",
    ),
}


@dataclass
class StoryParams:
    setting: str
    mystery: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    suspect_name: str
    suspect_type: str
    seed: Optional[int] = None


HEROES = [
    ("Mina", "girl"),
    ("Theo", "boy"),
    ("Lina", "girl"),
    ("Owen", "boy"),
    ("Nora", "girl"),
]
HELPERS = [
    ("Marta", "woman"),
    ("Pip", "boy"),
    ("Eli", "boy"),
    ("June", "girl"),
    ("Ada", "girl"),
]
SUSPECTS = [
    ("Mr. Bell", "man"),
    ("Aunt Sera", "woman"),
    ("Nell", "girl"),
    ("Sam", "boy"),
    ("Mr. Fox", "man"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit story world about a locked mystery, curiosity, quest, and a drench reveal.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--suspect-name")
    ap.add_argument("--suspect-type", choices=["girl", "boy", "woman", "man"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    hero_name, hero_type = (args.hero_name, args.hero_type) if args.hero_name and args.hero_type else rng.choice(HEROES)
    helper_name, helper_type = (args.helper_name, args.helper_type) if args.helper_name and args.helper_type else rng.choice(HELPERS)
    suspect_name, suspect_type = (args.suspect_name, args.suspect_type) if args.suspect_name and args.suspect_type else rng.choice(SUSPECTS)

    if args.hero_type and args.hero_name is None:
        hero_name = rng.choice([n for n, t in HEROES if t == args.hero_type])
    if args.helper_type and args.helper_name is None:
        helper_name = rng.choice([n for n, t in HELPERS if t == args.helper_type])
    if args.suspect_type and args.suspect_name is None:
        suspect_name = rng.choice([n for n, t in SUSPECTS if t == args.suspect_type])

    if hero_name == helper_name or hero_name == suspect_name or helper_name == suspect_name:
        raise StoryError("Choose distinct names for the hero, helper, and suspect.")

    return StoryParams(
        setting=setting,
        mystery=mystery,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        suspect_name=suspect_name,
        suspect_type=suspect_type,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    m: Mystery = f["mystery"]
    return [
        f'Write a short whodunit story for a young child that includes the words "lock", "curiosity", and "quest".',
        f"Tell a gentle mystery where {hero.label} follows curiosity, searches for a key, and opens the {m.locked_thing}.",
        f"Write a simple mystery story with a rainy drench that reveals a clue and helps solve what happened.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    suspect: Entity = f["suspect"]
    m: Mystery = f["mystery"]
    lockbox: Entity = f["lockbox"]
    clue: Entity = f["clue"]
    return [
        QAItem(
            question=f"What made {hero.label} start looking around the room?",
            answer=f"{hero.label} had a lot of curiosity, so {hero.pronoun('subject')} wanted to know what was hidden in the locked {m.locked_thing}.",
        ),
        QAItem(
            question=f"What was the little quest about?",
            answer=f"It was a search for the missing key, so {hero.label} could open the {m.locked_thing} without guessing.",
        ),
        QAItem(
            question=f"What clue showed up after the drench?",
            answer=f"A wet mark appeared on the {clue.label}, and that clue helped point to why the mystery had been kept secret.",
        ),
        QAItem(
            question=f"What happened when the key was finally used?",
            answer=f"The lock clicked open, the {m.locked_thing} opened, and the hidden item inside could be seen at last.",
        ),
        QAItem(
            question=f"Was {suspect.label} the thief?",
            answer=f"No. {suspect.label} only looked suspicious for a moment. The ending showed {suspect.pronoun('subject')} had hidden the key to protect the surprise, not to steal it.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a lock do?",
            answer="A lock keeps a door, box, or cabinet shut until the right key or latch is used.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, ask, and learn more about something.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search for something important, like a missing key or a hidden clue.",
        ),
        QAItem(
            question="What can a drench do in a mystery story?",
            answer="A drench can soak a clue and make a hidden mark easy to see, which can help solve the puzzle.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
thing(lockbox).
thing(key).
thing(clue).

can_open(H) :- curiosity(H), has_key(H), locked(lockbox).
drench_reveals(clue) :- wet(clue), hidden(clue).
resolved :- can_open(hero), revealed(clue), open(lockbox).

#show can_open/1.
#show drench_reveals/1.
#show resolved/0.
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("thing", "lockbox"))
    lines.append(asp.fact("thing", "key"))
    lines.append(asp.fact("thing", "clue"))
    lines.append(asp.fact("curiosity", "hero"))
    lines.append(asp.fact("locked", "lockbox"))
    lines.append(asp.fact("hidden", "clue"))
    lines.append(asp.fact("wet", "clue"))
    lines.append(asp.fact("has_key", "hero"))
    lines.append(asp.fact("open", "lockbox"))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    atoms = set((s.name, tuple(a.name if a.type != a.type.Number else a.number for a in s.arguments)) for s in model)
    expected = {("can_open", ("hero",)), ("drench_reveals", ("clue",)), ("resolved", ())}
    if atoms == expected:
        print("OK: ASP twin matches the Python reasonability gate.")
        return 0
    print("MISMATCH:", sorted(atoms), sorted(expected))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = build_world(
        SETTINGS[params.setting],
        MYSTERIES[params.mystery],
        params.hero_name,
        params.hero_type,
        params.helper_name,
        params.helper_type,
        params.suspect_name,
        params.suspect_type,
    )
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


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
    StoryParams("reading_room", "music_box", "Mina", "girl", "Marta", "woman", "Mr. Bell", "man"),
    StoryParams("attic", "chest", "Theo", "boy", "Ada", "girl", "Aunt Sera", "woman"),
    StoryParams("porch", "cabinet", "Nora", "girl", "Eli", "boy", "Sam", "boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.hero_name}: {p.mystery} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
