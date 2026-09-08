#!/usr/bin/env python3
"""A superhero storyworld about a quest, a grizzly problem, and a happy ending."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Scene:
    place: str
    weather: str
    mood: str


@dataclass
class StoryParams:
    place: str
    hero: str
    sidekick: str
    grizzly: str
    quest: str = ""
    seed: Optional[int] = None


@dataclass(frozen=True)
class QuestCase:
    trouble: str
    call: str
    search: str
    false_lead: str
    key_clue: str
    truth: str
    fix: str
    ending_image: str
    lesson: str


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


PLACES = {
    "sky_tower": Scene("Sky Tower", "windy", "bright and busy"),
    "river_bridge": Scene("River Bridge", "misty", "echoing"),
    "city_park": Scene("City Park", "sunlit", "leafy and alert"),
    "harbor_dock": Scene("Harbor Dock", "salt-bright", "shiny with puddles"),
}

HEROES = {
    "Nova": "girl",
    "Bolt": "boy",
    "Comet": "girl",
    "Flash": "boy",
}

SIDEKICKS = {
    "Pip": "girl",
    "Jace": "boy",
    "Mira": "girl",
    "Toby": "boy",
}

GRIZZLIES = {
    "bearbot": "robot bear",
    "grizzly": "grizzly bear",
    "shadow_grizzly": "shadow grizzly",
    "tin_bear": "tin bear",
}

QUESTS = {
    "find_signal": QuestCase(
        trouble="the rooftop signal lamp had gone dark",
        call="the mayor asked for help and pointed to the blank tower",
        search="scoured the stairs and the wind-swept roof for a hidden switch",
        false_lead="the first switch only lit a harmless fan, so the plan needed a better path",
        key_clue="a claw mark led from the lamp to a loose battery tray",
        truth="the grizzly trouble was not an attack at all; the battery tray had rattled loose during the storm",
        fix="locked the tray, relit the lamp, and guided the helpers back into a neat line",
        ending_image="the tower glowed gold again while the city waved from below",
        lesson="a careful quest asks what happened before it asks who to blame",
    ),
    "rescue_map": QuestCase(
        trouble="the rescue map had been torn in half",
        call="the captain sent the heroes to recover the missing half before sunset",
        search="scoured the mural hall and the ventilation grate for paper scraps",
        false_lead="the first scrap matched a poster, not the map, so the team kept looking",
        key_clue="a grizzly paw print crossed both edges of the torn paper",
        truth="the map had stuck to a kite string and drifted into the statue garden",
        fix="rejoined the halves, tied the map to a clip, and anchored the kite string",
        ending_image="the repaired map sat flat on the table like a brave little flag",
        lesson="matching clues is better than guessing from one big shape",
    ),
    "save_clock": QuestCase(
        trouble="the city clock had stopped at noon",
        call="the alarm from the plaza rang until the heroes arrived",
        search="scoured the gears behind the clock face with a flashlight and a mirror",
        false_lead="dust on the gears looked guilty, but brushing it away did not restart the hands",
        key_clue="a grizzly fur tuft hid in the cooling vent beside a bent pin",
        truth="the clock had jammed when a parade ribbon wound around the pin and froze the gears",
        fix="cut the ribbon, straightened the pin, and gave the gears a gentle turn",
        ending_image="the clock struck one and pigeons burst into a cheerful circle",
        lesson="the smallest snag can stop the biggest machine",
    ),
    "find_kit": QuestCase(
        trouble="the emergency first-aid kit had vanished from the hall",
        call="the school announcer asked every hero to search quietly and kindly",
        search="scoured the lockers and the equipment shelf for the bright red case",
        false_lead="one locker had scratch marks, but inside was only a soccer ball and a glove",
        key_clue="a grizzly-shaped sticker had peeled onto the vent cover near the stairs",
        truth="the kit had been moved by a janitor to dry after a spilled drink",
        fix="returned the kit, wiped the case clean, and added a dry shelf by the door",
        ending_image="the red case shone on its shelf like a badge after a mission",
        lesson="kind help often looks ordinary until the full story is known",
    ),
    "bridge_bell": QuestCase(
        trouble="the bridge bell used for emergencies would not ring",
        call="a bus full of children waited on the far side of the river",
        search="scoured the bridge rail and the bell rope for a broken knot",
        false_lead="the rope was frayed, but the bell still did not move when pulled",
        key_clue="a grizzly paw print in wet mud led under the bridge walkway",
        truth="the bell had slipped into a hollow beam when the wind shook the bridge",
        fix="fished out the bell with a hooked pole, tied a stronger rope, and tested it twice",
        ending_image="the bell rang clear above the water while the bus rolled safely across",
        lesson="a hero should follow the path of a clue, not just the loudest worry",
    ),
}

ROUTES = ("call_first", "scour_first", "quiet_first", "time_pressure", "two_theories", "inner_vow")


ASP_RULES = """
valid(Place, Hero, Sidekick, Grizzly, Quest) :- place(Place), hero(Hero), sidekick(Sidekick), grizzly(Grizzly), quest(Quest).
"""


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero quest world with a grizzly mystery and a happy ending.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--hero", choices=sorted(HEROES))
    ap.add_argument("--sidekick", choices=sorted(SIDEKICKS))
    ap.add_argument("--grizzly", choices=sorted(GRIZZLIES))
    ap.add_argument("--quest", choices=sorted(QUESTS))
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        ap.add_argument(f"--{flag}", action="store_true")
    return ap


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    return [(p, h, s, g, q) for p in sorted(PLACES) for h in sorted(HEROES) for s in sorted(SIDEKICKS) for g in sorted(GRIZZLIES) for q in sorted(QUESTS)]


def asp_facts() -> str:
    import asp
    parts = [
        *(asp.fact("place", p) for p in PLACES),
        *(asp.fact("hero", h) for h in HEROES),
        *(asp.fact("sidekick", s) for s in SIDEKICKS),
        *(asp.fact("grizzly", g) for g in GRIZZLIES),
        *(asp.fact("quest", q) for q in QUESTS),
    ]
    return "\n".join(parts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    return sorted(set(asp.atoms(asp.one_model(asp_program("#show valid/5.")), "valid")))


def asp_verify() -> int:
    py, cl = set(valid_combos()), set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:", sorted(py - cl), sorted(cl - py))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        c for c in valid_combos()
        if (not args.place or c[0] == args.place)
        and (not args.hero or c[1] == args.hero)
        and (not args.sidekick or c[2] == args.sidekick)
        and (not args.grizzly or c[3] == args.grizzly)
        and (not args.quest or c[4] == args.quest)
    ]
    if not combos:
        raise StoryError("No valid superhero quest fits those options.")
    place, hero, sidekick, grizzly, quest = rng.choice(combos)
    if hero == sidekick:
        raise StoryError("The hero and sidekick must be different characters.")
    return StoryParams(place=place, hero=hero, sidekick=sidekick, grizzly=grizzly, quest=quest)


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(str(x) for x in (params.seed, params.place, params.hero, params.sidekick, params.grizzly, params.quest))
    return random.Random(int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big"))


def tell(params: StoryParams) -> World:
    scene = PLACES[params.place]
    case = QUESTS[params.quest]
    rng = story_rng(params)
    world = World(scene)
    hero = world.add(Entity(id=params.hero, kind="character", type=HEROES[params.hero]))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type=SIDEKICKS[params.sidekick]))
    grizzly = world.add(Entity(id=params.grizzly, kind="character", type=GRIZZLIES[params.grizzly], label=params.grizzly))

    openings = {
        "call_first": f"At {scene.place}, {case.call}. {hero.id} tightened a bright cape and looked toward {case.trouble}.",
        "scour_first": f"{hero.id} and {sidekick.id} began by searching in silence. They knew {case.trouble}, so they set out to scour every corner of {scene.place}.",
        "quiet_first": f"Nothing felt ordinary at {scene.place}; even the wind seemed to wait. Then {case.trouble}, and the quest began.",
        "time_pressure": f"The clock was racing at {scene.place}. {case.trouble}, and {case.call}.",
        "two_theories": f"Two ideas fought for attention at {scene.place}: a prank or a problem. But {case.trouble} made {hero.id} search for the real answer.",
        "inner_vow": f'"I will not give up," {hero.id} thought. {case.trouble}, and {case.call}.',
    }
    route = rng.choice(ROUTES)
    world.say(openings[route])
    world.say(f'"We will scour the area together," {sidekick.id} said. "And we will keep the grizzly safe while we do it."')
    world.say(f'"Good," {hero.id} said. "A hero does not terminate a worry with shouting. A hero solves it with proof."')
    world.para()
    world.say(case.search + ".")
    world.say(case.false_lead + ".")
    world.say(f'Inside, {hero.id} heard an inner monologue: "Stay calm. A clue can be small, but it can still lead home."')
    world.say(f"{sidekick.id} replied, \"Then let's keep going until the truth steps out.\"")
    world.para()
    world.say(f"The grizzly at the center of the trouble was {grizzly.label}, but the clue showed it had not caused the damage by choice.")
    world.say(f"{case.key_clue.capitalize()} helped the heroes connect the trail to the real cause.")
    world.say(f"The truth was that {case.truth}.")
    world.say(f'"That means we can terminate the mistake, not the friend," {hero.id} said, and {sidekick.id} nodded.')
    world.say(f"They {case.fix}.")
    world.say(f"{hero.id} wrote the lesson in the quest journal: {case.lesson}.")
    world.say(f"At the end, {case.ending_image}.")
    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        grizzly=grizzly,
        scene=scene,
        case=case,
        route=route,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c = f["case"]
    return [
        f"Write a superhero quest story about {f['hero'].id} and {f['sidekick'].id} who must {c.trouble} at {f['scene'].place}.",
        f"Include an inner monologue, a grizzly clue, and a happy ending where the heroes {c.fix}.",
        f"Tell a child-facing superhero story that uses the words terminate, grizzly, and scour while ending with {c.ending_image}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c = f["case"]
    return [
        QAItem(
            question=f"What trouble started the quest at {f['scene'].place}?",
            answer=f"The quest began because {c.trouble}. That is why {f['hero'].id} and {f['sidekick'].id} had to search carefully."
        ),
        QAItem(
            question=f"What did the heroes say before they began to scour the area?",
            answer=f"{f['sidekick'].id} said they would scour the area together, and {f['hero'].id} said to solve the problem with proof instead of shouting."
        ),
        QAItem(
            question="What did the inner monologue help the hero remember?",
            answer="The hero reminded themselves to stay calm, because a small clue can still lead to the truth."
        ),
        QAItem(
            question="What clue revealed the real cause of the problem?",
            answer=f"The clue was {c.key_clue}. It helped the heroes connect the trail to what really happened."
        ),
        QAItem(
            question="How did the story end happily?",
            answer=f"The heroes {c.fix}, and the ending image was {c.ending_image}."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to scour a place?",
            answer="To scour a place means to search it very carefully from one end to the other."
        ),
        QAItem(
            question="Why is an inner monologue useful in a story?",
            answer="An inner monologue shows what a character is thinking, which can guide their choices and make the story feel personal."
        ),
        QAItem(
            question="What makes a happy ending feel complete?",
            answer="A happy ending feels complete when the main problem is solved and the final image shows the change."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id} ({e.kind}/{e.type}) meters={e.meters} memes={e.memes}")
    lines.append(f"  route={world.facts.get('route')}")
    lines.append(f"  truth={world.facts['case'].truth}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


CURATED = [
    StoryParams(place="sky_tower", hero="Nova", sidekick="Pip", grizzly="bearbot", quest="find_signal", seed=11),
    StoryParams(place="city_park", hero="Bolt", sidekick="Mira", grizzly="grizzly", quest="find_kit", seed=22),
    StoryParams(place="harbor_dock", hero="Comet", sidekick="Toby", grizzly="shadow_grizzly", quest="bridge_bell", seed=33),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for place, hero, sidekick, grizzly, quest in combos:
            print(f"  {place:12} {hero:8} {sidekick:8} {grizzly:14} {quest}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(args.n * 50, 50):
            seed = base_seed + attempts
            attempts += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as error:
                print(error)
                return
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
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header="### curated story" if args.all else (f"### variant {i + 1}" if len(samples) > 1 else ""),
        )
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
