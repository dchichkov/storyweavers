#!/usr/bin/env python3
"""
storyworlds/worlds/adventure_ineffable_suspense_nursery_rhyme.py
=================================================================

A small nursery-rhyme story world about a tiny nighttime adventure with
gentle suspense: a child or little creature wants to follow a curious path,
a helper worries about safety, and a cozy resolution brings everyone home.

Seed image:
---
A little traveler hears a whispering path under the moon.
A lost keepsake must be found before the lantern goes dim.
A cautious helper warns of the dark, but a kind guide and a safe light
make the adventure possible.

World model:
---
Physical meters:
    - light: how bright the lantern is
    - distance: how far from home the traveler has gone
    - found: whether the keepsake has been recovered
    - tired: how worn out the traveler feels
    - safe: whether the path is safely guided

Emotional memes:
    - curiosity: the pull toward the adventure
    - worry: the helper's concern
    - suspense: the sense of "just ahead..."
    - courage: the traveler keeps going
    - relief: the ending warmth after the find

The story is generated from state changes, not from a frozen paragraph.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "rabbit"}
        male = {"boy", "father", "dad", "man", "fox"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the moonlit garden"
    detail: str = "The path was small and silver under the moon."
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    keyword: str
    risk_word: str
    reason: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    label: str
    phrase: str
    type: str
    carried_word: str


@dataclass
class Guide:
    id: str
    label: str
    kind_word: str
    safety_tool: str
    prep: str
    closing: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def join_list(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + ", and " + items[-1]


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "bright")
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved a quiet night walk.")


def love_adventure(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    world.say(
        f"{hero.pronoun().capitalize()} loved an {quest.keyword} adventure, "
        f"and the path felt {quest.reason}."
    )


def begin(world: World, hero: Entity, guide: Entity, gift: Entity, quest: Quest) -> None:
    world.say(
        f"One night, {hero.id} found {hero.pronoun('possessive')} {gift.label} was missing."
    )
    world.say(
        f"{guide.label.capitalize()} held up a lantern and said, "
        f'"We can look, but we must stay close to the light."'
    )


def warn(world: World, guide: Entity, hero: Entity, quest: Quest) -> None:
    hero.memes["suspense"] = hero.memes.get("suspense", 0.0) + 1
    guide.memes["worry"] = guide.memes.get("worry", 0.0) + 1
    world.say(
        f"{guide.label.capitalize()} worried that the dark would make the {quest.keyword} trail hard to follow."
    )
    world.say(f"Still, a tiny glow pointed onward, and the story held its breath.")


def travel(world: World, hero: Entity, guide: Entity, quest: Quest) -> None:
    hero.meters["distance"] = hero.meters.get("distance", 0.0) + 1
    hero.memes["courage"] = hero.memes.get("courage", 0.0) + 1
    world.say(
        f"{hero.id} took small steps by the lantern, following the {quest.keyword} trail."
    )
    world.say(
        f"Each step made the night feel more quiet, and more full of wonder."
    )


def find_sign(world: World, hero: Entity, quest: Quest, gift: Entity) -> None:
    hero.meters["found"] = hero.meters.get("found", 0.0) + 1
    world.say(
        f"Then {hero.id} saw a little shine beneath a leaf: {hero.pronoun('possessive')} {gift.label}!"
    )
    world.say(
        f"It had hidden near a stone, just where the {quest.keyword} path curled."
    )


def resolve(world: World, hero: Entity, guide: Entity, gift: Entity, quest: Quest) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    guide.memes["worry"] = 0.0
    hero.meters["safe"] = 1.0
    world.say(
        f"{guide.label.capitalize()} laughed softly, and {hero.id} hugged {hero.pronoun('possessive')} {gift.label} close."
    )
    world.say(
        f"Together they walked home, the lantern warm and the {quest.keyword} adventure done."
    )
    world.say(
        f"The moon still shone, but now the night felt peaceful, and the little keepsake was back where it belonged."
    )


def tell(world: World, hero: Entity, guide: Entity, gift: Entity, quest: Quest) -> World:
    world.facts["hero"] = hero
    world.facts["guide"] = guide
    world.facts["gift"] = gift
    world.facts["quest"] = quest

    introduce(world, hero)
    love_adventure(world, hero, quest)
    begin(world, hero, guide, gift, quest)
    world.para()
    warn(world, guide, hero, quest)
    travel(world, hero, guide, quest)
    find_sign(world, hero, quest, gift)
    world.para()
    resolve(world, hero, guide, gift, quest)
    return world


SETTINGS = {
    "garden": Setting(
        place="the moonlit garden",
        detail="The moon laid a silver ribbon across the little path.",
        affords={"search"},
    ),
    "orchard": Setting(
        place="the quiet orchard",
        detail="The trees stood like sleepy giants, and the grass whispered softly.",
        affords={"search"},
    ),
}


QUESTS = {
    "lantern": Quest(
        id="lantern",
        verb="follow the lantern trail",
        gerund="following the lantern trail",
        rush="hurry after the glow",
        keyword="lantern",
        risk_word="dark",
        reason="full of tiny sparkles and maybe one surprise",
        reveal="a lantern trail",
        tags={"light", "night"},
    ),
    "firefly": Quest(
        id="firefly",
        verb="follow the firefly trail",
        gerund="following the firefly trail",
        rush="dash after the flickers",
        keyword="firefly",
        risk_word="twilight",
        reason="so bright it looked like a string of stars",
        reveal="a firefly trail",
        tags={"bug", "night"},
    ),
    "rhyme": Quest(
        id="rhyme",
        verb="follow the nursery rhyme clues",
        gerund="following the rhyme clues",
        rush="skip to the next line",
        keyword="rhyme",
        risk_word="silence",
        reason="like a song hiding in the dark",
        reveal="a rhyme trail",
        tags={"song", "night"},
    ),
}

GIFTS = {
    "bell": Gift(label="little bell", phrase="a little bell on a blue string", type="bell", carried_word="carried"),
    "shell": Gift(label="shell charm", phrase="a shell charm with a smooth shine", type="shell", carried_word="worn"),
    "key": Gift(label="tiny key", phrase="a tiny key tied in a ribbon", type="key", carried_word="tucked"),
}

GUIDES = [
    Guide(id="Moss", label="Moss the rabbit", kind_word="rabbit", safety_tool="lantern", prep="lifted the lantern higher", closing="stayed close to the glow"),
    Guide(id="Pip", label="Pip the fox", kind_word="fox", safety_tool="lamp", prep="kept the lamp steady", closing="walked home beside the traveler"),
]

HEROES = [
    ("Lina", "girl"),
    ("Milo", "boy"),
    ("Nia", "girl"),
    ("Theo", "boy"),
    ("Poppy", "girl"),
]

TRAITS = ["curious", "brave", "spry", "gentle", "cheerful"]


@dataclass
class StoryParams:
    place: str
    quest: str
    gift: str
    hero_name: str
    hero_type: str
    guide: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, q, g) for p in SETTINGS for q in QUESTS for g in GIFTS]


def explain_rejection(place: str, quest: str, gift: str) -> str:
    return f"(No story: {quest} cannot be paired with {gift} at {place} in a safe, story-shaped way.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme adventure with suspense and a gentle ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide", choices=["Moss", "Pip"])
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
    if args.place and args.quest and args.gift:
        if (args.place, args.quest, args.gift) not in valid_combos():
            raise StoryError(explain_rejection(args.place, args.quest, args.gift))

    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.quest:
        combos = [c for c in combos if c[1] == args.quest]
    if args.gift:
        combos = [c for c in combos if c[2] == args.gift]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, quest, gift = rng.choice(sorted(combos))
    hero_name, hero_type = (args.name, args.gender) if args.name and args.gender else rng.choice(HEROES)
    if args.gender:
        hero_type = args.gender
    if not args.name:
        hero_name, _ = rng.choice([h for h in HEROES if h[1] == hero_type] or HEROES)
    guide = args.guide or rng.choice(list(GUIDES)).id
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, gift=gift, hero_name=hero_name, hero_type=hero_type, guide=guide, trait=trait)


def generation_prompts(sample: StorySample) -> list[str]:
    f = sample.world.facts
    hero, quest, gift, guide = f["hero"], f["quest"], f["gift"], f["guide"]
    return [
        f'Write a small nursery-rhyme adventure about {hero.id}, the {quest.keyword} trail, and a missing {gift.label}.',
        f"Tell a suspenseful but gentle bedtime story where {guide.label} helps {hero.id} follow {quest.verb}.",
        f'Compose a child-friendly tale using the words "adventure" and "ineffable" and ending with a found {gift.label}.',
    ]


def story_qa(sample: StorySample) -> list[QAItem]:
    f = sample.world.facts
    hero, quest, gift, guide = f["hero"], f["quest"], f["gift"], f["guide"]
    return [
        QAItem(
            question=f"What kind of story is this about {hero.id}?",
            answer=f"It is a little nighttime adventure with a quiet, nursery-rhyme feel and a soft suspenseful middle.",
        ),
        QAItem(
            question=f"What was {hero.id} looking for?",
            answer=f"{hero.id} was looking for {hero.pronoun('possessive')} {gift.label}.",
        ),
        QAItem(
            question=f"Who helped keep the adventure safe?",
            answer=f"{guide.label} helped by holding the light and staying close while {hero.id} followed the {quest.keyword} trail.",
        ),
        QAItem(
            question=f"Why did the story feel suspenseful?",
            answer=f"It felt suspenseful because the missing {gift.label} was hidden in the dark, and the path had to be followed carefully.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the {gift.label} was found, the worry faded, and {hero.id} went home feeling relieved.",
        ),
    ]


def world_knowledge_qa(sample: StorySample) -> list[QAItem]:
    return [
        QAItem(
            question="What is an adventure?",
            answer="An adventure is a trip or event that feels exciting because something new or tricky might happen.",
        ),
        QAItem(
            question="What does ineffable mean?",
            answer="Ineffable means so special or strange that it is hard to describe in words.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of wondering what will happen next, especially when something important is not resolved yet.",
        ),
        QAItem(
            question="What makes a nursery rhyme style?",
            answer="Nursery rhyme style often uses simple words, gentle rhythm, and a singing, storybook feel.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
hero(H) :- hero_name(H).
quest(Q) :- quest_id(Q).
gift(G) :- gift_id(G).
guide(N) :- guide_id(N).

compatible(P,Q,G) :- place(P), quest(Q), gift(G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for q in QUESTS:
        lines.append(asp.fact("quest_id", q))
    for g in GIFTS:
        lines.append(asp.fact("gift_id", g))
    for name, _ in HEROES:
        lines.append(asp.fact("hero_name", name))
    for g in GUIDES:
        lines.append(asp.fact("guide_id", g.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos()")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        traits=["little", params.trait],
        meters={"distance": 0.0},
        memes={"curiosity": 0.0, "worry": 0.0, "suspense": 0.0, "courage": 0.0, "relief": 0.0},
    ))
    guide_def = next(g for g in GUIDES if g.id == params.guide)
    guide = world.add(Entity(
        id=guide_def.id,
        kind="character",
        type=guide_def.kind_word,
        label=guide_def.label,
        meters={"light": 1.0},
        memes={"worry": 0.0},
    ))
    gift_def = GIFTS[params.gift]
    gift = world.add(Entity(
        id="gift",
        type=gift_def.type,
        label=gift_def.label,
        phrase=gift_def.phrase,
        owner=hero.id,
        carried_by=None,
        meters={"found": 0.0},
    ))
    quest = QUESTS[params.quest]
    world.facts.update(hero=hero, guide=guide, gift=gift, quest=quest)

    tell(world, hero, guide, gift, quest)

    story = world.render().replace(" a ineffable ", " an ineffable ")
    story = story.replace(" an adventure adventure", " an adventure")
    story = story.replace("ineffable", "ineffable")
    prompts = generation_prompts(StorySample(params=params, story=story, world=world))
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa(StorySample(params=params, story=story, world=world)),
        world_qa=world_knowledge_qa(StorySample(params=params, story=story, world=world)),
        world=world,
    )


CURATED = [
    StoryParams(place="garden", quest="lantern", gift="bell", hero_name="Lina", hero_type="girl", guide="Moss", trait="curious"),
    StoryParams(place="orchard", quest="firefly", gift="shell", hero_name="Milo", hero_type="boy", guide="Pip", trait="brave"),
    StoryParams(place="garden", quest="rhyme", gift="key", hero_name="Poppy", hero_type="girl", guide="Moss", trait="gentle"),
]


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
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples: list[StorySample] = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
            header = f"### {p.hero_name}: {p.quest} at {p.place} (gift: {p.gift})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
