#!/usr/bin/env python3
"""
storyworlds/worlds/fellow_ship_paw_rosemary_happy_ending_humor.py
=================================================================

A tiny pirate-tale storyworld about a fellow-ship, a paw, and rosemary.
The domain leans into a gentle pirate adventure: a crew wants a fragrant
herb for supper and a silly pawprint clue leads them to it. The tension is
small and child-facing, and every variant ends happily with a humorous image.

Story seed premise:
---
A little pirate crew sails with a clever fellow-ship. Their parrot paw keeps
stepping in rosemary plants and leaving green little hints. The crew needs
rosemary for stew, but the herb keeps blowing off course or hiding behind
barrels. They follow the pawprints, laugh at the silly mixups, and end with
a warm supper.

World shape:
---
- physical meters: distance, lost, found, wind, smell, soup
- emotional memes: joy, worry, humor, teamwork
- causal turn: if rosemary is not found before supper, the crew grows worried
  and the lookout tries a silly clue-hunt. A pawprint trail can reveal the herb.
- resolution: the crew finds rosemary, makes stew, and ends with a playful
  dinner image proving the change.

This file follows the Storyweavers contract with:
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- eager import of storyworlds.results containers
- lazy import of storyworlds.asp in ASP helpers
- inline ASP_RULES twin, asp_facts(), and --verify parity
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: str = ""
    role: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("distance", "lost", "found", "wind", "smell", "soup"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "worry", "humor", "teamwork"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the little harbor"
    weather: str = "breezy"


@dataclass
class Crew:
    name: str
    ship: str
    captain_title: str
    lookout_title: str
    crew_word: str
    soup_word: str
    joke_word: str
    cozy_end: str


@dataclass
class Herb:
    id: str
    label: str
    phrase: str
    scent: str
    use: str
    hiding_spots: list[str]


@dataclass
class Clue:
    id: str
    label: str
    trail_word: str
    silly_action: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
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
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


CREWS = {
    "fellow-ship": Crew(
        name="fellow-ship",
        ship="the Friend Ship",
        captain_title="Captain",
        lookout_title="Lookout",
        crew_word="crew",
        soup_word="stew",
        joke_word="joke",
        cozy_end="they all ate supper together",
    ),
    "sea-buds": Crew(
        name="sea-buds",
        ship="the Pebble Boat",
        captain_title="Captain",
        lookout_title="Scout",
        crew_word="buddies",
        soup_word="soup",
        joke_word="giggle",
        cozy_end="they shared bowls and smiles",
    ),
}

HERBS = {
    "rosemary": Herb(
        id="rosemary",
        label="rosemary",
        phrase="a little bunch of rosemary",
        scent="fresh and piney",
        use="make the stew smell nice",
        hiding_spots=["behind a barrel", "under the net", "near the galley door"],
    ),
    "mint": Herb(
        id="mint",
        label="mint",
        phrase="a sprig of mint",
        scent="cool and sweet",
        use="make the tea smell nice",
        hiding_spots=["in a tin cup", "beside a crate", "near the stern rope"],
    ),
}

CLUES = {
    "paw": Clue(
        id="paw",
        label="paw",
        trail_word="pawprints",
        silly_action="left green pawprints in the deck dust",
    ),
    "pawprint": Clue(
        id="pawprint",
        label="pawprint",
        trail_word="pawprints",
        silly_action="stamped pawprints on every plank",
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora", "Rose", "Ella"]
BOY_NAMES = ["Tom", "Leo", "Ben", "Max", "Finn", "Eli", "Sam"]
TRAITS = ["cheerful", "curious", "sly", "silly", "brave", "gentle"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(crew, herb, clue) for crew in CREWS for herb in HERBS for clue in CLUES]


@dataclass
class StoryParams:
    crew: str
    herb: str
    clue: str
    captain: str
    captain_gender: str
    lookout: str
    lookout_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def _maybe_article(word: str) -> str:
    return word if word.startswith(("a ", "an ", "the ")) else f"a {word}"


def setup_story(world: World, crew: Crew, herb: Herb, clue: Clue, captain: Entity, lookout: Entity, parent: Entity) -> None:
    captain.memes["joy"] += 1
    lookout.memes["joy"] += 1
    lookout.memes["humor"] += 1
    world.say(
        f"Once upon a breezy day at {world.setting.place}, the {crew.name} sailed "
        f"aboard {crew.ship} with {captain.id} and {lookout.id} at the helm."
    )
    world.say(
        f"{captain.id} was the {crew.captain_title.lower()}, and {lookout.id} was the "
        f"{crew.lookout_title.lower()} who loved a good {crew.joke_word}."
    )
    world.say(
        f"They needed {herb.phrase} to {herb.use}, but the little herb kept hiding."
    )


def worry_turn(world: World, crew: Crew, herb: Herb, clue: Clue, captain: Entity, lookout: Entity) -> None:
    captain.memes["worry"] += 1
    lookout.memes["worry"] += 1
    world.para()
    world.say(
        f"The galley smelled good, but the pot was still empty. {captain.id} frowned "
        f"and said, 'We cannot make {crew.soup_word} without {herb.label}.'"
    )
    world.say(
        f"Then {lookout.id} spotted something funny: {clue.silly_action}."
    )
    world.say(
        f"Everyone laughed, because the clue looked like a tiny map drawn by a clumsy crab."
    )


def find_herb(world: World, crew: Crew, herb: Herb, clue: Clue, captain: Entity, lookout: Entity) -> None:
    captain.memes["teamwork"] += 1
    lookout.memes["teamwork"] += 1
    lookout.memes["humor"] += 1
    world.say(
        f"{lookout.id} followed the {clue.trail_word} past the barrels and under the net."
    )
    world.say(
        f"There, tucked {herb.hiding_spots[0]}, was {_maybe_article(herb.phrase)}."
    )
    world.say(
        f"It smelled {herb.scent}, like the ocean had learned how to cook."
    )
    herb_entity = world.get("herb")
    herb_entity.meters["found"] += 1
    herb_entity.meters["lost"] = 0.0


def cook_end(world: World, crew: Crew, herb: Herb, captain: Entity, lookout: Entity, parent: Entity) -> None:
    world.para()
    captain.memes["joy"] += 1
    lookout.memes["joy"] += 1
    captain.memes["humor"] += 1
    world.get("pot").meters["soup"] += 1
    world.get("herb").meters["found"] += 1
    world.say(
        f"{captain.id} dropped the rosemary into the pot, and soon the {crew.soup_word} "
        f"was warm and bright."
    )
    world.say(
        f"{parent.label_word.capitalize()} smiled at the silly little crew and said, "
        f"'Now that is a fine supper.'"
    )
    world.say(
        f"At the end of the day, {crew.cozy_end}, and the {crew.joke_word} had a "
        f"fresh rosemary punchline."
    )
    world.say(
        f"The Friend Ship rocked gently, the kitchen glowed, and everyone went to bed full and happy."
    )


def tell(setting: Setting, crew: Crew, herb: Herb, clue: Clue,
         captain_name: str = "Tom", captain_gender: str = "boy",
         lookout_name: str = "Lily", lookout_gender: str = "girl",
         parent_type: str = "mother", trait: str = "silly") -> World:
    world = World(setting)
    captain = world.add(Entity(id=captain_name, kind="character", type=captain_gender))
    lookout = world.add(Entity(id=lookout_name, kind="character", type=lookout_gender))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    herb_ent = world.add(Entity(id="herb", type="thing", label=herb.label, phrase=herb.phrase))
    pot = world.add(Entity(id="pot", type="thing", label="pot"))
    world.facts.update(crew=crew, herb=herb, clue=clue, captain=captain, lookout=lookout, parent=parent, trait=trait)
    setup_story(world, crew, herb, clue, captain, lookout, parent)
    worry_turn(world, crew, herb, clue, captain, lookout)
    find_herb(world, crew, herb, clue, captain, lookout)
    cook_end(world, crew, herb, captain, lookout, parent)
    world.facts.update(herb_entity=herb_ent, pot=pot, resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short pirate-tale story for a young child about a {f["crew"].name}, a {f["clue"].label}, and {f["herb"].label}. Include the word "{f["herb"].label}".',
        f"Tell a gentle story where {f['captain'].id} and {f['lookout'].id} search for {f['herb'].phrase} so they can make {f['crew'].soup_word}, and a silly paw clue helps them.",
        f'Write a happy ending pirate adventure with humor, a missing herb, and a funny trail of {f["clue"].trail_word}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    crew: Crew = f["crew"]
    herb: Herb = f["herb"]
    clue: Clue = f["clue"]
    captain: Entity = f["captain"]
    lookout: Entity = f["lookout"]
    parent: Entity = f["parent"]
    return [
        QAItem(
            question=f"Who is the story about on {crew.ship}?",
            answer=f"It is about {captain.id}, {lookout.id}, and their {crew.name} pirate crew on {crew.ship}.",
        ),
        QAItem(
            question=f"What did the crew want to find for the {crew.soup_word}?",
            answer=f"They wanted {herb.phrase} so they could make the {crew.soup_word} smell nice and taste good.",
        ),
        QAItem(
            question=f"What clue helped {lookout.id} find the herb?",
            answer=f"A funny {clue.label} clue helped, because it left {clue.trail_word} across the deck like a tiny map.",
        ),
        QAItem(
            question=f"How did the parent feel at the end?",
            answer=f"{parent.label_word.capitalize()} smiled, because the little crew found the herb and ended with a happy supper.",
        ),
        QAItem(
            question=f"Why was the story funny?",
            answer=f"It was funny because the paw clue looked clumsy, but it still led them right to the herb.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    herb: Herb = world.facts["herb"]
    return [
        QAItem(
            question="What is rosemary?",
            answer="Rosemary is a fragrant herb. People use it to flavor food like soup, stew, and roasted potatoes.",
        ),
        QAItem(
            question="What is a pawprint?",
            answer="A pawprint is a mark left by an animal's paw when it steps on dust, sand, mud, or snow.",
        ),
        QAItem(
            question="Why do pirates use maps?",
            answer="Pirates use maps to help them find places, treasures, and hidden paths while they explore.",
        ),
    ] if herb.id == "rosemary" else [
        QAItem(
            question="What is mint?",
            answer="Mint is a fragrant herb with a cool smell. People use it in drinks and food.",
        )
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
found_herb(H) :- herb(H), trail(T), leads_to(T, H).
happy_end :- found_herb(H), herb(H).
humor :- funny_trail(T), trail(T).
"""

def asp_facts() -> str:
    import asp
    parts = [
        asp.fact("crew", "fellow_ship"),
        asp.fact("herb", "rosemary"),
        asp.fact("trail", "paw"),
        asp.fact("funny_trail", "paw"),
        asp.fact("leads_to", "paw", "rosemary"),
        asp.fact("happy_ending"),
        asp.fact("humor"),
    ]
    return "\n".join(parts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show found_herb/1.\n#show happy_end/0.\n#show humor/0."))
    return 0 if model else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-tale storyworld: fellow-ship, paw, and rosemary.")
    ap.add_argument("--crew", choices=CREWS)
    ap.add_argument("--herb", choices=HERBS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--captain")
    ap.add_argument("--lookout")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    crew = args.crew or rng.choice(list(CREWS))
    herb = args.herb or rng.choice(list(HERBS))
    clue = args.clue or rng.choice(list(CLUES))
    trait = args.trait or rng.choice(TRAITS)
    parent = args.parent or rng.choice(["mother", "father"])
    captain = args.captain or rng.choice(GIRL_NAMES + BOY_NAMES)
    lookout = args.lookout or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != captain])
    if crew == "fellow-ship" and herb != "rosemary":
        raise StoryError("The fellow-ship story wants rosemary for its stew.")
    return StoryParams(
        crew=crew,
        herb=herb,
        clue=clue,
        captain=captain,
        captain_gender="boy" if captain in BOY_NAMES else "girl",
        lookout=lookout,
        lookout_gender="boy" if lookout in BOY_NAMES else "girl",
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(CREWS[params.crew], HERBS[params.herb], CLUES[params.clue],
                 params.captain, params.captain_gender, params.lookout,
                 params.lookout_gender, params.parent, params.trait)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show found_herb/1.\n#show happy_end/0.\n#show humor/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show found_herb/1.\n#show happy_end/0.\n#show humor/0."))
        print(model)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        for crew in CREWS:
            for herb in HERBS:
                for clue in CLUES:
                    p = StoryParams(
                        crew=crew, herb=herb, clue=clue,
                        captain="Tom", captain_gender="boy",
                        lookout="Lily", lookout_gender="girl",
                        parent="mother", trait="silly",
                    )
                    samples.append(generate(p))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
