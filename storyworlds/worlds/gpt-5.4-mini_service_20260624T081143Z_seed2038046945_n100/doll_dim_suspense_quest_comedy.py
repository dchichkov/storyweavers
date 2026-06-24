#!/usr/bin/env python3
"""
storyworlds/worlds/doll_dim_suspense_quest_comedy.py
=====================================================

A small standalone storyworld about a tiny doll-sized quest with a little
suspense and a comic finish.

Seed imagining:
---
A child loses a tiny doll accessory in a room full of big furniture. The doll
hero, brave but small, goes on a quest through ordinary household terrain. The
search feels suspenseful because the missing thing might be under something,
inside something, or carried away by a pet. The ending is comic: the "danger"
turns out to be a very silly hiding place, and the hero gets a triumphant
return.

World model:
---
- physical meters: distance, blockage, height, hiding, carried, found, tidy
- emotional memes: worry, courage, joy, relief, pride, confusion, suspense

The story is driven by state changes:
- a clue raises suspense
- a quest begins
- the hero searches likely places
- a helper reveals the missing item
- the ending proves the state changed: worry down, relief up, item found

This file follows the Storyweavers storyworld contract:
- standalone stdlib script
- eager import of results.py containers
- lazy import of asp.py in ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- support for default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    bearer: Optional[str] = None
    location: str = ""
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


@dataclass
class Setting:
    place: str
    indoors: bool
    spaces: list[str] = field(default_factory=list)
    helpers: list[str] = field(default_factory=list)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    clue: str
    suspense_event: str
    search_places: list[str]
    hiding_spots: list[str]
    twist: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    size: str
    type_hint: str = "tiny"


@dataclass
class Helper:
    id: str
    label: str
    role: str
    line: str
    reveal: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c


def _bump(entity: Entity, key: str, amount: float) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + amount


def _feel(entity: Entity, key: str, amount: float) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + amount


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for e in world.entities.values():
            if e.memes.get("confusion", 0.0) >= THRESHOLD and e.memes.get("suspense", 0.0) < 2.0:
                sig = ("suspense", e.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    _feel(e, "suspense", 1.0)
                    out.append(f"Every strange corner made the search feel a little more mysterious.")
                    changed = True
            if e.meters.get("found", 0.0) >= THRESHOLD and e.memes.get("relief", 0.0) < 1.0:
                sig = ("relief", e.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    _feel(e, "relief", 1.0)
                    _feel(e, "worry", -1.0)
                    out.append(f"That changed the whole room from worried to relieved.")
                    changed = True
    if narrate:
        for s in out:
            world.say(s)
    return out


def _quest_drive(world: World, hero: Entity, quest: Quest) -> None:
    _feel(hero, "courage", 1.0)
    _feel(hero, "worry", 1.0)
    _feel(hero, "confusion", 1.0)
    world.say(f"{hero.id} started a careful quest to {quest.verb}.")
    world.say(f"First came the clue: {quest.clue}.")


def _search(world: World, hero: Entity, quest: Quest) -> None:
    world.para()
    for place in quest.search_places:
        _bump(hero, "distance", 1.0)
        _feel(hero, "suspense", 0.5)
        world.say(
            f"{hero.id} peeked behind the {place}, because the missing thing might be there."
        )
    world.say(f"Still, {hero.id} found only {quest.twist}.")
    propagate(world)


def _reveal(world: World, hero: Entity, helper: Entity, prize: Entity, quest: Quest) -> None:
    world.para()
    world.say(helper.label + " came over with a grin.")
    world.say(helper.label + " said, " + repr(quest.suspense_event) + ".")
    prize.location = helper.id
    prize.bearer = hero.id
    _bump(prize, "found", 1.0)
    _feel(hero, "joy", 1.0)
    _feel(hero, "pride", 1.0)
    world.say(f"{helper.label} pointed at {quest.reveal if hasattr(quest, 'reveal') else quest.twist}.")
    world.say(f"Then {hero.id} found {prize.phrase} and laughed at the silly hiding place.")
    propagate(world)


def intro(world: World, hero: Entity, prize: Entity) -> None:
    world.say(
        f"{hero.id} was a tiny, brave doll who loved neat rooms and big adventures."
    )
    world.say(
        f"{hero.id} treasured {hero.pronoun('possessive')} {prize.label} because it made {hero.pronoun('object')} feel ready for play."
    )


def setting_line(world: World, quest: Quest) -> str:
    if world.setting.indoors:
        return f"The quest began inside {world.setting.place}, where every chair looked like a mountain to a doll."
    return f"The quest began at {world.setting.place}, where even a small step felt exciting."


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, prize, quest, helper = f["hero"], f["prize"], f["quest"], f["helper"]
    return [
        QAItem(
            question=f"What was {hero.id} looking for in the story?",
            answer=f"{hero.id} was looking for {prize.phrase}. It had gone missing, so the quest started to find it again."
        ),
        QAItem(
            question=f"Why did the search feel suspenseful?",
            answer=f"It felt suspenseful because the missing {prize.label} could have been hidden in several places, and {hero.id} did not know which one was right."
        ),
        QAItem(
            question=f"Who helped {hero.id} in the end?",
            answer=f"{helper.label} helped by pointing to the silly hiding place and showing where the {prize.label} was."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} finding {prize.phrase}, feeling relieved, and laughing because the hiding place was so funny."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a clue do in a mystery or quest?",
            answer="A clue gives a helpful hint that can guide someone toward the answer."
        ),
        QAItem(
            question="Why can a tiny doll feel like a hero?",
            answer="A tiny doll can feel like a hero because being brave matters more than being big."
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of wondering what will happen next."
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short comedic story for a child about a doll-sized quest that includes the word "{f["quest"].keyword}".',
        f"Tell a suspenseful but funny story where {f['hero'].id} searches for a missing {f['prize'].label} and ends up laughing.",
        f"Write a tiny adventure story set in {world.setting.place} where a small hero follows clues and finds something silly.",
    ]


SETTINGS = {
    "bedroom": Setting(place="the bedroom", indoors=True, spaces=["bed", "dresser", "lamp", "rug"], helpers=["cat"]),
    "playroom": Setting(place="the playroom", indoors=True, spaces=["toy box", "couch", "blocks", "blanket fort"], helpers=["teddy"]),
    "hallway": Setting(place="the hallway", indoors=True, spaces=["shoe rack", "coat hook", "umbrella stand", "mat"], helpers=["dog"]),
    "garden": Setting(place="the garden", indoors=False, spaces=["flower pot", "bench", "watering can", "bush"], helpers=["bird"]),
}

QUESTS = {
    "ribbon": Quest(
        id="ribbon",
        verb="find the missing ribbon",
        gerund="searching for the ribbon",
        clue="a tiny red thread fluttered near the shelf",
        suspense_event="Maybe the ribbon had slipped under the toy box!",
        search_places=["bed", "dresser", "rug"],
        hiding_spots=["toy box", "blanket", "pillow"],
        twist="a line of crumbs and a very suspicious sock",
        keyword="ribbon",
        tags={"tiny", "search", "toy"},
    ),
    "crown": Quest(
        id="crown",
        verb="recover the tiny crown",
        gerund="looking for the crown",
        clue="a shiny speck flashed by the lamp",
        suspense_event="Maybe the crown was hiding in the tallest place in the room!",
        search_places=["lamp", "blocks", "couch"],
        hiding_spots=["basket", "drawer", "hat"],
        twist="a tower of blocks that looked far too proud",
        keyword="crown",
        tags={"tiny", "royal", "search"},
    ),
    "boot": Quest(
        id="boot",
        verb="find the lost boot",
        gerund="hunting for the boot",
        clue="one tiny footprint pointed toward the mat",
        suspense_event="Maybe the boot had been borrowed by a sneaky corner!",
        search_places=["shoe rack", "mat", "umbrella stand"],
        hiding_spots=["bucket", "plant", "basket"],
        twist="a squeaky toy pretending to be a guard",
        keyword="boot",
        tags={"tiny", "search", "silly"},
    ),
}

PRIZES = {
    "ribbon": Prize(label="ribbon", phrase="a bright little ribbon", type="ribbon", size="tiny"),
    "crown": Prize(label="crown", phrase="a shiny cardboard crown", type="crown", size="tiny"),
    "boot": Prize(label="boot", phrase="one tiny boot", type="boot", size="tiny"),
}

HELPERS = {
    "cat": Helper(id="cat", label="the cat", role="helper", line="with a very serious whisker flick", reveal="under the cushion"),
    "teddy": Helper(id="teddy", label="the teddy bear", role="helper", line="as if solving a royal case", reveal="inside the blanket fort"),
    "dog": Helper(id="dog", label="the dog", role="helper", line="with a wag and a nose nudge", reveal="behind the shoe rack"),
    "bird": Helper(id="bird", label="the bird", role="helper", line="from a branch outside", reveal="near the flower pot"),
}


@dataclass
class StoryParams:
    setting: str
    quest: str
    prize: str
    hero: str
    hero_type: str
    helper: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(setting="bedroom", quest="ribbon", prize="ribbon", hero="Mina", hero_type="doll", helper="cat"),
    StoryParams(setting="playroom", quest="crown", prize="crown", hero="Toby", hero_type="doll", helper="teddy"),
    StoryParams(setting="hallway", quest="boot", prize="boot", hero="Pia", hero_type="doll", helper="dog"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny doll-dim quest story world with suspense and comedy.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero")
    ap.add_argument("--helper", choices=HELPERS)
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
    quest = args.quest or rng.choice(list(QUESTS))
    prize = args.prize or quest
    helper = args.helper or rng.choice(SETTINGS[setting].helpers)
    hero = args.hero or rng.choice(["Mina", "Toby", "Pia", "Nell", "Rory", "Lulu"])
    return StoryParams(setting=setting, quest=quest, prize=prize, hero=hero, hero_type="doll", helper=helper)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    quest = QUESTS[params.quest]
    prize = PRIZES[params.prize]
    helper = HELPERS[params.helper]

    world = World(setting)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type))
    prize_ent = world.add(Entity(id=prize.label, type=prize.type, label=prize.label, phrase=prize.phrase, owner=hero.id, location="missing"))
    helper_ent = world.add(Entity(id=helper.id, kind="character", type="helper", label=helper.label))

    world.facts.update(hero=hero, quest=quest, prize=prize_ent, helper=helper_ent, setting=setting)

    intro(world, hero, prize_ent)
    world.para()
    world.say(setting_line(world, quest))
    _quest_drive(world, hero, quest)
    _search(world, hero, quest)
    _reveal(world, hero, helper_ent, prize_ent, quest)

    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


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
        lines.append(
            f"  {e.id:10} ({e.type:8}) meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
hero(hero).
quest(q).
prize(p).
helper(h).

suspense(hero) :- clue_seen(hero), not found(p).
quest_started(hero) :- hero(hero), quest(q), prize(p).
comic_end(hero) :- found(p), laughter(hero).

#show suspense/1.
#show quest_started/1.
#show comic_end/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("hero", "hero"),
        asp.fact("quest", "q"),
        asp.fact("prize", "p"),
        asp.fact("helper", "h"),
        asp.fact("clue_seen", "hero"),
        asp.fact("found", "p"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show quest_started/1.\n#show comic_end/1."))
    names = {sym.name for sym in model}
    if {"quest_started", "comic_end"} <= names:
        print("OK: ASP twin produces the expected comic quest atoms.")
        return 0
    print("MISMATCH: ASP twin did not produce expected atoms.")
    return 1


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
        print(asp_program("#show suspense/1.\n#show quest_started/1.\n#show comic_end/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show suspense/1.\n#show quest_started/1.\n#show comic_end/1."))
        print(model)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            p = resolve_params(args, random.Random(seed))
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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
