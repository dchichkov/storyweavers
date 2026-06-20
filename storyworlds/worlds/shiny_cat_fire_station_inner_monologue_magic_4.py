#!/usr/bin/env python3
"""
shiny_cat_fire_station_inner_monologue_magic_4.py
=================================================

A small StoryWorld for the seed:

    words: shiny cat
    setting: fire station
    features: Inner Monologue, Magic
    style: Mystery

Internal source tale:
    A child spends a quiet evening in a fire station and notices that the
    station's shiny cat reacts to a strange sound before anyone else does. The
    child follows the cat through a small mystery, keeps an inner monologue
    running instead of shouting, and discovers that the cat's magic reveals the
    true cause of the whispering noise. The ending image shows the station
    changed back into a calm, knowable place.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class Area:
    key: str
    phrase: str
    landmark: str
    support_keys: tuple[str, ...]
    clue_distance_m: float


@dataclass(frozen=True)
class Mystery:
    key: str
    phrase: str
    sound: str
    support_key: str
    hidden_thing: str
    hiding_spot: str
    cause: str
    fix: str
    consequence: str
    proof_image: str
    risk: str


@dataclass(frozen=True)
class MagicMode:
    key: str
    phrase: str
    action: str
    support_keys: tuple[str, ...]
    reveal: str


@dataclass
class StoryParams:
    area: str
    mystery: str
    magic: str
    hero: str
    gender: str
    mentor: str
    seed: int


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: dict[str, str] = field(default_factory=dict)

    def add_meter(self, key: str, amount: float) -> None:
        self.meters[key] = round(self.meters.get(key, 0.0) + amount, 2)

    def set_meter(self, key: str, value: float) -> None:
        self.meters[key] = round(value, 2)

    def add_meme(self, key: str, amount: float) -> None:
        self.memes[key] = round(self.memes.get(key, 0.0) + amount, 2)

    def set_tag(self, key: str, value: str) -> None:
        self.tags[key] = value


@dataclass
class World:
    params: StoryParams
    area: Area
    mystery: Mystery
    magic: MagicMode
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[str] = field(default_factory=list)
    fired_rules: list[str] = field(default_factory=list)
    inner_opening: str = ""
    inner_turn: str = ""
    clue_text: str = ""
    reveal_text: str = ""
    lesson_text: str = ""

    def note(self, text: str) -> None:
        self.history.append(text)

    def trace(self) -> str:
        rows = ["--- world model state ---"]
        rows.append(
            f"area={self.area.key} mystery={self.mystery.key} magic={self.magic.key} "
            f"hero={self.params.hero} mentor={mentor_name(self.params.mentor)}"
        )
        for name, ent in self.entities.items():
            meters = ", ".join(f"{k}={v}" for k, v in sorted(ent.meters.items()))
            memes = ", ".join(f"{k}={v}" for k, v in sorted(ent.memes.items()))
            tags = ", ".join(f"{k}={v}" for k, v in sorted(ent.tags.items()))
            detail = "; ".join(part for part in (meters, memes, tags) if part)
            rows.append(f"  {name:<12} ({ent.kind:<10}) {detail}".rstrip())
        rows.append(f"  fired rules: {self.fired_rules}")
        rows.append("  history:")
        rows.extend(f"    - {item}" for item in self.history)
        return "\n".join(rows)


AREAS: dict[str, Area] = {
    "gear_room": Area(
        key="gear_room",
        phrase="the gear room beside the truck bay",
        landmark="a row of yellow boots under a wooden bench",
        support_keys=("floor", "draft"),
        clue_distance_m=2.4,
    ),
    "map_loft": Area(
        key="map_loft",
        phrase="the little map loft above the watch desk",
        landmark="a wall map crossed with blue string",
        support_keys=("draft",),
        clue_distance_m=3.2,
    ),
    "bell_nook": Area(
        key="bell_nook",
        phrase="the bell nook near the practice pole",
        landmark="an old brass practice bell hung by a red cord",
        support_keys=("bell",),
        clue_distance_m=1.8,
    ),
    "hose_bay": Area(
        key="hose_bay",
        phrase="the hose bay where the silver nozzles were drying",
        landmark="a shining hose rack and a floor fan",
        support_keys=("floor", "bell"),
        clue_distance_m=2.1,
    ),
}

MYSTERIES: dict[str, Mystery] = {
    "brass_key": Mystery(
        key="brass_key",
        phrase="a tiny ringing from a place that should have been still",
        sound="ting... ting...",
        support_key="floor",
        hidden_thing="the brass supply key",
        hiding_spot="the space beneath the boot bench",
        cause="the floor fan was nudging the lost key against the metal bench leg",
        fix="lifted the bench and pulled the key free before hanging it back on its hook",
        consequence="the supply drawer could open for the morning check",
        proof_image="the brass key hung quiet beside the helmets",
        risk="Without the key, the small supply drawer would stay shut when the firefighters needed it.",
    ),
    "moon_draft": Mystery(
        key="moon_draft",
        phrase="a lonely bell twitch from an empty corner",
        sound="shhh... ring...",
        support_key="draft",
        hidden_thing="the loose skylight latch",
        hiding_spot="the loose skylight latch above the wall map",
        cause="a moon-cold draft was slipping through a loose skylight latch and tugging the bell cord",
        fix="clicked the latch shut and tied a red ribbon there so the morning crew would repair it",
        consequence="the practice bell stopped giving nervous little rings",
        proof_image="the red ribbon rested still in the warm station air",
        risk="The draft would keep distracting everyone until the roof latch was repaired.",
    ),
    "ember_moth": Mystery(
        key="ember_moth",
        phrase="a secret chime from inside the practice bell",
        sound="tin... tin...",
        support_key="bell",
        hidden_thing="a silver ember moth",
        hiding_spot="inside the brass cup of the practice bell",
        cause="a silver ember moth had fluttered into the bell and brushed the brass with each wingbeat",
        fix="opened the bell cover and guided the little moth back outside",
        consequence="the practice bell became quiet again without hurting the tiny visitor",
        proof_image="the silver moth floated toward dawn while the bell stayed silent",
        risk="The moth would have worn itself out if it had stayed trapped in the bell.",
    ),
}

MAGICS: dict[str, MagicMode] = {
    "star_pawprints": MagicMode(
        key="star_pawprints",
        phrase="starry pawprints",
        action="left a line of silver pawprints across the floor",
        support_keys=("floor",),
        reveal="Each print shone for a breath and then faded, turning the floor into a trail.",
    ),
    "mirror_tail": MagicMode(
        key="mirror_tail",
        phrase="a mirror-bright tail",
        action="flicked his tail and sent a blade of light up toward the rafters",
        support_keys=("draft",),
        reveal="The reflected light made the hidden moving air visible for a moment.",
    ),
    "lantern_purr": MagicMode(
        key="lantern_purr",
        phrase="a lantern-deep purr",
        action="purred so deeply that the brass around the bell hummed back",
        support_keys=("bell",),
        reveal="The humming answered from the exact place where the secret was hiding.",
    ),
}

MENTORS = {
    "rosa": "Captain Rosa",
    "ellis": "Captain Ellis",
    "jo": "Firefighter Jo",
    "malik": "Firefighter Malik",
}

HERO_NAMES = {
    "girl": ("Mira", "Nora", "Lina", "June", "Tess"),
    "boy": ("Theo", "Finn", "Eli", "Sam", "Owen"),
}


def mentor_name(key: str) -> str:
    return MENTORS[key]


def pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "boy":
        return "he", "his", "him"
    return "she", "her", "her"


def valid_combo(area: str, mystery: str, magic: str) -> bool:
    if area not in AREAS or mystery not in MYSTERIES or magic not in MAGICS:
        return False
    support = MYSTERIES[mystery].support_key
    return support in AREAS[area].support_keys and support in MAGICS[magic].support_keys


def invalid_reason(area: str, mystery: str, magic: str) -> str:
    if area not in AREAS:
        return f"No story: unknown fire-station area {area!r}."
    if mystery not in MYSTERIES:
        return f"No story: unknown mystery {mystery!r}."
    if magic not in MAGICS:
        return f"No story: unknown magic style {magic!r}."
    support = MYSTERIES[mystery].support_key
    if support not in AREAS[area].support_keys:
        return (
            f"No story: {AREAS[area].phrase} does not suit {MYSTERIES[mystery].phrase}; "
            f"that mystery needs a {support} clue."
        )
    if support not in MAGICS[magic].support_keys:
        return (
            f"No story: {MAGICS[magic].phrase} cannot solve {MYSTERIES[mystery].phrase}; "
            f"try magic that matches a {support} clue."
        )
    return "No story: the requested fire-station mystery is not reasonable."


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for area in sorted(AREAS):
        for mystery in sorted(MYSTERIES):
            for magic in sorted(MAGICS):
                if valid_combo(area, mystery, magic):
                    combos.append((area, mystery, magic))
    return combos


def _pick_hero(rng: random.Random, gender: str) -> str:
    return rng.choice(HERO_NAMES[gender])


def _r_set_station_hush(world: World) -> bool:
    hero = world.entities["Hero"]
    cat = world.entities["Cat"]
    station = world.entities["Station"]
    mystery = world.entities["Mystery"]

    hero.add_meme("curiosity", 0.8)
    hero.add_meme("worry", 0.4)
    cat.add_meme("wonder", 0.9)
    station.add_meme("calm", 0.7)
    station.add_meme("mystery", 0.8)
    mystery.set_meter("sound_db", 17.0)

    world.inner_opening = (
        "That sound is too small for the big room. "
        "Small sounds are sometimes the ones that matter."
    )
    world.note(
        f"The fire station was quiet enough for {world.params.hero} to hear {world.mystery.sound} from {world.area.phrase}."
    )
    return True


def _r_cat_marks_clue(world: World) -> bool:
    hero = world.entities["Hero"]
    cat = world.entities["Cat"]
    mystery = world.entities["Mystery"]

    hero.add_meter("steps_m", world.area.clue_distance_m)
    hero.add_meme("attention", 0.7)
    cat.add_meter("steps_m", world.area.clue_distance_m)
    cat.add_meme("focus", 1.0)
    mystery.set_tag("hiding_spot", world.mystery.hiding_spot)
    mystery.set_tag("hidden_thing", world.mystery.hidden_thing)

    if world.magic.key == "star_pawprints":
        world.clue_text = (
            "Glint left a line of silver pawprints across the floor, ending beneath the boot bench."
        )
    elif world.magic.key == "mirror_tail":
        world.clue_text = (
            "Glint flicked his tail and sent a blade of light up toward the rafters, and the light caught the loose skylight latch high above the wall map."
        )
    else:
        world.clue_text = (
            f"Glint {world.magic.action}, and the humming answered from {world.mystery.hiding_spot}."
        )
    world.note(world.clue_text)
    return True


def _r_magic_reveals_truth(world: World) -> bool:
    hero = world.entities["Hero"]
    mentor = world.entities["Mentor"]
    cat = world.entities["Cat"]
    station = world.entities["Station"]
    mystery = world.entities["Mystery"]

    hero.add_meme("courage", 0.9)
    hero.add_meme("trust", 0.7)
    hero.add_meme("worry", -0.2)
    mentor.add_meme("approval", 0.8)
    cat.add_meme("wonder", 0.5)
    station.add_meme("calm", 0.9)
    station.add_meme("mystery", -0.6)
    mystery.set_tag("cause", world.mystery.cause)
    mystery.set_tag("fix", world.mystery.fix)
    mystery.set_tag("consequence", world.mystery.consequence)
    mystery.set_tag("proof", world.mystery.proof_image)
    mystery.set_meter("resolved", 1.0)

    world.inner_turn = "If I stay quiet and watch the cat, the answer might show itself."
    world.reveal_text = f"The truth was simple once the magic pointed at it: {world.mystery.cause}."
    world.lesson_text = (
        "The mystery opened because the child noticed a clue, trusted the shiny cat, "
        "and chose careful help over noisy guessing."
    )
    world.note(world.reveal_text)
    world.note(f"{mentor_name(world.params.mentor)} {world.mystery.fix}.")
    world.note(world.mystery.consequence)
    return True


RULES = [
    ("station_hush", _r_set_station_hush),
    ("cat_marks_clue", _r_cat_marks_clue),
    ("magic_reveals_truth", _r_magic_reveals_truth),
]


def build_world(params: StoryParams) -> World:
    if not valid_combo(params.area, params.mystery, params.magic):
        raise StoryError(invalid_reason(params.area, params.mystery, params.magic))

    world = World(
        params=params,
        area=AREAS[params.area],
        mystery=MYSTERIES[params.mystery],
        magic=MAGICS[params.magic],
    )
    world.entities["Hero"] = Entity(
        name=params.hero,
        kind=params.gender,
        meters={"height_m": 1.28, "steps_m": 0.0},
        memes={"curiosity": 0.2},
        tags={"role": "solver"},
    )
    world.entities["Mentor"] = Entity(
        name=mentor_name(params.mentor),
        kind="firefighter",
        meters={"height_m": 1.72},
        memes={"calm": 1.0},
        tags={"role": "guide"},
    )
    world.entities["Cat"] = Entity(
        name="Glint",
        kind="cat",
        meters={"shine": 0.98, "tail_height_m": 0.27, "steps_m": 0.0},
        memes={"wonder": 0.6},
        tags={"coat": "shiny", "magic": world.magic.phrase},
    )
    world.entities["Station"] = Entity(
        name="Fire Station",
        kind="place",
        meters={"lamp_glow_lux": 36.0, "quiet_db": 18.0},
        memes={"calm": 0.6},
        tags={"setting": "fire station", "area": world.area.phrase},
    )
    world.entities["Mystery"] = Entity(
        name=world.mystery.hidden_thing,
        kind="mystery",
        meters={"distance_m": world.area.clue_distance_m, "resolved": 0.0},
        memes={"hidden": 1.0},
        tags={"sound": world.mystery.sound},
    )

    for name, rule in RULES:
        rule(world)
        world.fired_rules.append(name)
    return world


def _opening(world: World) -> str:
    p = world.params
    mentor = mentor_name(p.mentor)
    return (
        f"At the fire station, the engines were washed and waiting, and the lamps made long red rivers on the floor. "
        f"{p.hero} stood with {mentor} in {world.area.phrase}, near {world.area.landmark}. "
        f"On top of a locker sat Glint, the shiny cat, and every blink of station light slid over his coat until he looked brushed with silver."
    )


def _mystery_paragraph(world: World) -> str:
    p = world.params
    return (
        f"Then the quiet broke with {world.mystery.sound} from somewhere nearby, {world.mystery.phrase}. "
        f"Glint's ears twitched before anyone spoke. \"{world.inner_opening}\" {p.hero} thought. "
        f"{p.hero} looked at the empty corners and wondered how a sound so small could feel so important."
    )


def _turn_paragraph(world: World) -> str:
    p = world.params
    mentor = mentor_name(p.mentor)
    return (
        f"Instead of calling out, {p.hero} followed Glint one careful step at a time. "
        f"{world.clue_text} {world.magic.reveal} "
        f"\"{world.inner_turn}\" {p.hero} thought. {mentor} saw the same clue at last and nodded for {p.hero} to keep looking."
    )


def _ending_paragraph(world: World) -> str:
    mentor = mentor_name(world.params.mentor)
    return (
        f"{world.reveal_text} {mentor} {world.mystery.fix}, and {world.mystery.consequence}. "
        f"When the mystery was over, {world.mystery.proof_image}. "
        f"{world.params.hero} smiled at Glint and knew the station had given up its secret because somebody stayed quiet long enough to listen."
    )


def render_story(world: World) -> str:
    return "\n\n".join([
        _opening(world),
        _mystery_paragraph(world),
        _turn_paragraph(world),
        _ending_paragraph(world),
    ])


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a child-friendly mystery set in a fire station that includes a shiny cat, magic, and an inner monologue.',
        f"Tell a quiet fire-station story where {world.params.hero} and {mentor_name(world.params.mentor)} follow Glint the shiny cat to solve {world.mystery.phrase}.",
        f"Write a magical mystery in {world.area.phrase} where the clue is {world.mystery.sound} and the answer appears through {world.magic.phrase}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    mentor = mentor_name(p.mentor)
    return [
        QAItem(
            "Who helped solve the mystery at the fire station?",
            f"{p.hero} solved it with Glint, the shiny cat, while {mentor} watched and helped at the end. "
            f"The child noticed the clue, and the cat's magic showed where to look.",
        ),
        QAItem(
            "What felt mysterious at first?",
            f"The mystery began with {world.mystery.sound} and {world.mystery.phrase}. "
            f"It felt strange because the room looked empty even though the sound kept returning.",
        ),
        QAItem(
            "What did the child think instead of shouting?",
            f"{p.hero} thought, \"{world.inner_opening}\" Later the child decided, \"{world.inner_turn}\" "
            f"Those thoughts slowed the search down enough for the real clue to appear.",
        ),
        QAItem(
            "How did Glint's magic help?",
            f"Glint used {world.magic.phrase}. {world.clue_text} That magical sign pointed straight toward {world.mystery.hiding_spot}.",
        ),
        QAItem(
            "What was really causing the strange sound?",
            f"The real cause was that {world.mystery.cause}. "
            f"Once the hidden cause was seen, the mystery stopped feeling spooky and started feeling solvable.",
        ),
        QAItem(
            "How did the ending prove the problem was solved?",
            f"{mentor} {world.mystery.fix}, so {world.mystery.consequence}. "
            f"The proof came in the final image: {world.mystery.proof_image}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    items = [
        QAItem(
            "Why can a fire station sound mysterious at night even when nothing is wrong?",
            "Big quiet rooms make small sounds stand out. A little ring, draft, or flutter can seem larger when the rest of the station is still.",
        ),
        QAItem(
            "Why might a cat notice a clue before a person does?",
            "Cats often react quickly to tiny sounds and movements. Their ears and eyes can catch details that people miss at first.",
        ),
        QAItem(
            "Why was it smart for the child to stay quiet and look carefully?",
            "A calm person can notice patterns more easily than a noisy, rushing one. Quiet attention helps turn a scary feeling into a solvable problem.",
        ),
    ]
    if world.mystery.key == "brass_key":
        items.append(
            QAItem(
                "Why does a loose key sometimes make a tapping sound?",
                "A metal key can tap or ring when moving air or vibration nudges it against something hard. The sound repeats if the push keeps happening.",
            )
        )
    elif world.mystery.key == "moon_draft":
        items.append(
            QAItem(
                "Why can a draft move a bell cord?",
                "Moving air can pull on light hanging things such as cords and ribbons. If the air comes again and again, the cord may twitch each time.",
            )
        )
    else:
        items.append(
            QAItem(
                "Why should someone free a small moth gently instead of swatting at it?",
                "A gentle rescue keeps the creature safe and stops the problem without harm. Small animals often need a way out more than they need force.",
            )
        )
    return items


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=render_story(world),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(A,M,G) :-
    area(A),
    mystery(M),
    magic(G),
    mystery_key(M,K),
    area_support(A,K),
    magic_support(G,K).

ok :- chosen_area(A), chosen_mystery(M), chosen_magic(G), valid(A,M,G).

#show valid/3.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from storyworlds.asp import fact

    rows: list[str] = []
    for area in AREAS.values():
        rows.append(fact("area", area.key))
        for key in area.support_keys:
            rows.append(fact("area_support", area.key, key))
    for mystery in MYSTERIES.values():
        rows.append(fact("mystery", mystery.key))
        rows.append(fact("mystery_key", mystery.key, mystery.support_key))
    for magic in MAGICS.values():
        rows.append(fact("magic", magic.key))
        for key in magic.support_keys:
            rows.append(fact("magic_support", magic.key, key))
    if params is not None:
        rows.append(fact("chosen_area", params.area))
        rows.append(fact("chosen_mystery", params.mystery))
        rows.append(fact("chosen_magic", params.magic))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None, *, show: str = "#show valid/3.\n#show ok/0.") -> str:
    return f"{asp_facts(params)}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> set[tuple[str, str, str]]:
    from storyworlds.asp import atoms, one_model

    model = one_model(asp_program())
    return set(atoms(model, "valid"))


def asp_accepts(params: StoryParams) -> bool:
    from storyworlds.asp import atoms, one_model

    model = one_model(asp_program(params, show="#show ok/0."))
    return bool(atoms(model, "ok"))


def _curated_cases() -> list[StoryParams]:
    names = {
        "girl": iter(("Mira", "Nora", "Lina", "June", "Tess")),
        "boy": iter(("Theo", "Finn", "Eli", "Sam", "Owen")),
    }
    cases: list[StoryParams] = []
    for index, combo in enumerate(valid_combos(), start=1):
        gender = "girl" if index % 2 else "boy"
        hero = next(names[gender], HERO_NAMES[gender][0])
        mentor = list(MENTORS)[(index - 1) % len(MENTORS)]
        cases.append(
            StoryParams(
                area=combo[0],
                mystery=combo[1],
                magic=combo[2],
                hero=hero,
                gender=gender,
                mentor=mentor,
                seed=100 + index,
            )
        )
    return cases


def _story_checks(sample: StorySample) -> list[str]:
    problems: list[str] = []
    text = sample.story
    if "shiny cat" not in text:
        problems.append("story lost the required shiny cat phrase")
    if "fire station" not in text:
        problems.append("story lost the required setting phrase")
    if "thought" not in text:
        problems.append("story lost visible inner monologue")
    if text.count("\n\n") < 3:
        problems.append("story is missing a clear beginning, middle turn, and ending paragraph shape")
    if "{" in text or "}" in text:
        problems.append("story leaked unresolved template markers")
    if "_" in text:
        problems.append("story leaked an internal id")
    if "No story:" in text:
        problems.append("story leaked an error string into prose")
    if len(sample.prompts) < 3 or len(sample.story_qa) < 6 or len(sample.world_qa) < 4:
        problems.append("prompt or QA sets are too thin")
    if not text.rstrip().endswith(("listen.", "listen")):
        problems.append("ending image or closing beat is too weak")
    for qa in sample.story_qa:
        if qa.answer.count(".") < 1:
            problems.append(f"story QA answer is too fragmentary: {qa.question}")
            break
    return problems


def verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = asp_valid_combos()
    if py_valid == asp_valid:
        print(f"OK: clingo gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("ASP/Python mismatch in valid combos:")
        if py_valid - asp_valid:
            print("  only in Python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in ASP:", sorted(asp_valid - py_valid))

    curated = _curated_cases()
    for params in curated:
        py_ok = valid_combo(params.area, params.mystery, params.magic)
        asp_ok = asp_accepts(params)
        if py_ok != asp_ok:
            rc = 1
            print("Acceptance mismatch:", params, py_ok, asp_ok)

    invalids = [
        StoryParams("map_loft", "brass_key", "star_pawprints", "Mira", "girl", "rosa", 1),
        StoryParams("bell_nook", "moon_draft", "lantern_purr", "Theo", "boy", "ellis", 2),
        StoryParams("gear_room", "ember_moth", "mirror_tail", "Lina", "girl", "jo", 3),
    ]
    for params in invalids:
        if asp_accepts(params):
            rc = 1
            print("ASP accepted invalid params:", params)
        try:
            generate(params)
        except StoryError:
            pass
        else:
            rc = 1
            print("Expected StoryError for invalid params but generation succeeded:", params)

    issues: list[str] = []
    for params in curated:
        sample = generate(params)
        issues.extend(f"{params.hero}: {problem}" for problem in _story_checks(sample))
    if not issues:
        print(f"OK: curated stories passed shape and QA checks ({len(curated)} samples).")
    else:
        rc = 1
        print("QUALITY CHECK FAILURES:")
        for issue in issues:
            print(" ", issue)

    return rc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a magical fire-station mystery about a shiny cat and a child listener."
    )
    parser.add_argument("--area", choices=sorted(AREAS))
    parser.add_argument("--mystery", choices=sorted(MYSTERIES))
    parser.add_argument("--magic", choices=sorted(MAGICS))
    parser.add_argument("--hero")
    parser.add_argument("--gender", choices=sorted(HERO_NAMES))
    parser.add_argument("--mentor", choices=sorted(MENTORS))
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random, index: int = 0) -> StoryParams:
    combos = [
        combo for combo in valid_combos()
        if (args.area is None or combo[0] == args.area)
        and (args.mystery is None or combo[1] == args.mystery)
        and (args.magic is None or combo[2] == args.magic)
    ]
    if not combos:
        if args.area and args.mystery and args.magic:
            raise StoryError(invalid_reason(args.area, args.mystery, args.magic))
        raise StoryError("No story: no valid fire-station mystery matches those filters.")

    area, mystery, magic = rng.choice(combos)
    gender = args.gender or rng.choice(sorted(HERO_NAMES))
    hero = args.hero or _pick_hero(rng, gender)
    mentor = args.mentor or rng.choice(sorted(MENTORS))
    return StoryParams(
        area=area,
        mystery=mystery,
        magic=magic,
        hero=hero,
        gender=gender,
        mentor=mentor,
        seed=args.seed + index,
    )


def format_qa(sample: StorySample) -> str:
    rows: list[str] = []
    rows.append("== (1) Generation prompts ==")
    for index, prompt in enumerate(sample.prompts, start=1):
        rows.append(f"{index}. {prompt}")
    rows.append("")
    rows.append("== (2) Story-grounded QA ==")
    for qa in sample.story_qa:
        rows.append(f"Q: {qa.question}")
        rows.append(f"A: {qa.answer}")
    rows.append("")
    rows.append("== (3) World-knowledge QA ==")
    for qa in sample.world_qa:
        rows.append(f"Q: {qa.question}")
        rows.append(f"A: {qa.answer}")
    return "\n".join(rows)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


def _sample_all(args: argparse.Namespace) -> list[StorySample]:
    samples: list[StorySample] = []
    for index, combo in enumerate(valid_combos(), start=1):
        rng = random.Random(args.seed + index)
        gender = args.gender or ("girl" if index % 2 else "boy")
        params = StoryParams(
            area=combo[0],
            mystery=combo[1],
            magic=combo[2],
            hero=args.hero or _pick_hero(rng, gender),
            gender=gender,
            mentor=args.mentor or sorted(MENTORS)[(index - 1) % len(MENTORS)],
            seed=args.seed + index,
        )
        samples.append(generate(params))
    return samples


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.show_asp:
            print(asp_program())
            return 0
        if args.verify:
            return verify()
        if args.asp:
            for combo in sorted(asp_valid_combos()):
                print("\t".join(combo))
            return 0

        if args.all:
            samples = _sample_all(args)
        else:
            samples = []
            for index in range(max(1, args.n)):
                rng = random.Random(args.seed + index)
                samples.append(generate(resolve_params(args, rng, index=index)))

        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return 0

        for index, sample in enumerate(samples):
            header = ""
            if args.all:
                p = sample.params
                header = f"### area={p.area} mystery={p.mystery} magic={p.magic}"
            elif len(samples) > 1:
                header = f"### variant {index + 1}"
            emit(sample, trace=args.trace, qa=args.qa, header=header)
            if index != len(samples) - 1:
                print("\n" + "=" * 72 + "\n")
        return 0
    except StoryError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
