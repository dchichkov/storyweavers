#!/usr/bin/env python3
"""
A small folk-tale storyworld about a curious child, a village karaoke night,
and the cautionary lesson that singing confidently is not the same as knowing
the words.

Seed tale used to shape the world:
---
A little child hears that the village is holding karaoke after supper. The child
wants to sing a famous folk song, but does not really know the lyrics. At first
the child feels sure that guessing will be fine. Then the music starts, the
words slip away, and the room grows quiet. A kind elder helps the child pause,
listen, and learn the song properly before trying again. In the end, the child
sings with care and remembers that it is wiser to know a thing before boasting
about it.

This script implements that premise as a tiny simulation with:
- a child hero
- a village elder
- a karaoke machine and a lyric scroll
- confidence, worry, and humility as emotional state
- a cautionary turn where overconfidence causes embarrassment
- a recovery where listening and learning restores the day
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

FOLK_OPENERS = [
    "Long ago, in a small village by the river,",
    "Once, when the lanterns were warm and the supper pots were quiet,",
    "In a little village where the wind knew every chimney,",
]

HERO_NAMES = ["Mina", "Tavi", "Sora", "Luna", "Pela", "Niko"]
ELDER_NAMES = ["Grandmother Reed", "Old Mara", "Aunt Willow", "Elder Bram"]
SONGS = [
    "the apple-tree song",
    "the lantern song",
    "the meadow song",
    "the river song",
]
GENTLE_ADJECTIVES = ["small", "curious", "brave", "earnest", "bright-eyed", "thoughtful"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: {"noise": 0.0, "skill": 0.0, "embarrassment": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"confidence": 0.0, "worry": 0.0, "humility": 0.0, "care": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the village hall"
    audience: str = "the neighbors"
    indoors: bool = True


@dataclass
class Props:
    karaoke_machine: str = "the karaoke machine"
    lyric_scroll: str = "the lyric scroll"
    bench: str = "the wooden bench"


@dataclass
class StoryParams:
    place: str
    hero_name: str
    elder_name: str
    song: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()
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


def make_world(params: StoryParams) -> World:
    world = World(Setting(place=params.place))
    hero = world.add(Entity(id=params.hero_name, kind="character", type="child"))
    elder = world.add(Entity(id=params.elder_name, kind="character", type="elder"))
    machine = world.add(Entity(id="karaoke_machine", type="machine", label="the karaoke machine"))
    scroll = world.add(Entity(id="lyric_scroll", type="scroll", label="the lyric scroll"))
    world.facts.update(hero=hero, elder=elder, machine=machine, scroll=scroll, params=params)
    return world


def intro(world: World) -> None:
    hero: Entity = world.facts["hero"]
    elder: Entity = world.facts["elder"]
    params: StoryParams = world.facts["params"]
    opener = random.choice(FOLK_OPENERS)
    trait = random.choice(GENTLE_ADJECTIVES)
    world.say(
        f"{opener} {hero.id} was a {trait} child who loved to listen when people sang at night."
    )
    world.say(
        f"That evening, {elder.id} brought out {world.setting.place}'s {world.facts['machine'].label} and set down {world.facts['scroll'].label}."
    )
    world.say(
        f"{hero.id} looked at {params.song} and felt a little thrill, because {hero.id} wanted to sing it for everyone."
    )


def inner_monologue(world: World) -> None:
    hero: Entity = world.facts["hero"]
    hero.memes["confidence"] += 1.0
    hero.memes["worry"] += 0.2
    world.say(
        f"In {hero.id}'s heart, a quick thought went, 'I know this song well enough. I can sing before supper grows cold.'"
    )
    world.say(
        f"Another quieter thought answered, 'Do I truly know it, or only the first line?'"
    )


def boast_and_warning(world: World) -> None:
    hero: Entity = world.facts["hero"]
    elder: Entity = world.facts["elder"]
    params: StoryParams = world.facts["params"]
    if "warned" in world.fired:
        return
    world.fired.add("warned")
    world.say(
        f"{hero.id} stepped forward and said they could sing {params.song} without any help."
    )
    world.say(
        f"{elder.id} smiled the way old trees smile at young birds and said, 'A song is kinder when you know it before you begin.'"
    )
    hero.memes["worry"] += 0.5
    hero.memes["humility"] += 0.3


def first_try_fails(world: World) -> None:
    hero: Entity = world.facts["hero"]
    params: StoryParams = world.facts["params"]
    if "fail" in world.fired:
        return
    world.fired.add("fail")
    hero.meters["noise"] += 1.0
    hero.meters["embarrassment"] += 1.0
    hero.memes["confidence"] -= 0.6
    hero.memes["worry"] += 1.0
    world.say(
        f"The music began, and at once {hero.id} stumbled on the second line of {params.song}."
    )
    world.say(
        f"The room went very still, because a half-known song can sound shaky when it is sung too boldly."
    )
    world.say(
        f"{hero.id}'s cheeks warmed, and the child wished the floor could hide them for a moment."
    )


def learn_properly(world: World) -> None:
    hero: Entity = world.facts["hero"]
    elder: Entity = world.facts["elder"]
    params: StoryParams = world.facts["params"]
    if "learned" in world.fired:
        return
    world.fired.add("learned")
    hero.memes["humility"] += 1.0
    hero.memes["care"] += 1.0
    hero.meters["skill"] += 1.0
    world.say(
        f"{elder.id} did not laugh. Instead, {elder.id} tapped the lyric scroll and sang one slow line at a time."
    )
    world.say(
        f"{hero.id} listened, repeated the words softly, and learned {params.song} the proper way, as carefully as one learns the path home."
    )
    world.say(
        f"With each line, the child's worry grew smaller and true knowing grew larger."
    )


def second_try_succeeds(world: World) -> None:
    hero: Entity = world.facts["hero"]
    params: StoryParams = world.facts["params"]
    if "succeeded" in world.fired:
        return
    world.fired.add("succeeded")
    hero.memes["confidence"] += 0.4
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 0.8)
    hero.meters["noise"] = max(0.0, hero.meters["noise"] - 0.5)
    world.say(
        f"When the music started again, {hero.id} sang {params.song} from beginning to end without rushing."
    )
    world.say(
        f"This time the words came like beads on a string, and the neighbors nodded with happy faces."
    )
    world.say(
        f"{hero.id} bowed shyly, glad to know the song at last."
    )


def tell(params: StoryParams) -> World:
    world = make_world(params)
    intro(world)
    world.para()
    inner_monologue(world)
    boast_and_warning(world)
    first_try_fails(world)
    world.para()
    learn_properly(world)
    second_try_succeeds(world)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f"Write a short folk tale about a child who wants to sing {p.song} at karaoke but must first learn the words.",
        f"Tell a cautionary story where {p.hero_name} thinks they know a song, then discovers that knowing is different from guessing.",
        f"Write a gentle village story with an inner monologue, karaoke, and a wise elder who helps a child try again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    hero: Entity = world.facts["hero"]
    elder: Entity = world.facts["elder"]
    return [
        QAItem(
            question=f"Why did {p.hero_name} feel brave at first?",
            answer=f"{p.hero_name} felt brave because they thought they knew {p.song} well enough to sing it right away."
        ),
        QAItem(
            question=f"What went wrong when {p.hero_name} first sang at karaoke?",
            answer=f"{p.hero_name} forgot part of {p.song}, so the first try sounded shaky and made them feel embarrassed."
        ),
        QAItem(
            question=f"How did {elder.id} help {p.hero_name}?",
            answer=f"{elder.id} sang the lines slowly from the lyric scroll and helped {p.hero_name} learn the song properly."
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {p.hero_name} knew {p.song} better, felt humbler and calmer, and could sing it from beginning to end."
        ),
        QAItem(
            question=f"How did {p.hero_name} think about singing before trying again?",
            answer=f"Inside, {p.hero_name} decided that it was better to know a song first than to boast and hope the words would come."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is karaoke?",
            answer="Karaoke is when people sing along with music that helps them keep the tune and remember the words."
        ),
        QAItem(
            question="Why is it wise to know the words before singing a song for others?",
            answer="It is wise because knowing the words helps a singer stay on the tune and avoid getting lost in front of everyone."
        ),
        QAItem(
            question="What does an elder do in a folk tale?",
            answer="An elder often teaches, warns, or helps a younger character choose the wiser path."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    parts.extend(sample.prompts)
    parts.append("")
    parts.append("== story QA ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== world QA ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


ASP_RULES = r"""
hero(H).
elder(E).
song(S).
karaoke_event :- wants_to_sing(H,S), not knows_words(H,S).
embarrassed(H) :- karaoke_event.
learns(H,S) :- listens(H,E), elder(E), song(S).
safe_try(H,S) :- learns(H,S), song(S).
"""

def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("hero", "hero"),
        asp.fact("elder", "elder"),
        asp.fact("song", "song"),
        asp.fact("wants_to_sing", "hero", "song"),
        asp.fact("knows_words", "hero", "song"),
        asp.fact("listens", "hero", "elder"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show karaoke_event/0. #show embarrassed/1. #show learns/2. #show safe_try/2."))
    atoms = set()
    for sym in model:
        if sym.name == "karaoke_event":
            atoms.add("karaoke_event")
        if sym.name == "embarrassed":
            atoms.add("embarrassed")
        if sym.name == "learns":
            atoms.add("learns")
        if sym.name == "safe_try":
            atoms.add("safe_try")
    ok = {"karaoke_event", "embarrassed", "learns", "safe_try"}
    if atoms == ok:
        print("OK: ASP twin produces the expected cautionary model.")
        return 0
    print("MISMATCH:", sorted(atoms), "expected", sorted(ok))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary folk-tale karaoke storyworld with inner monologue.")
    ap.add_argument("--place", choices=["village hall", "lantern room", "barn stage"], default=None)
    ap.add_argument("--name", choices=HERO_NAMES, default=None)
    ap.add_argument("--elder", choices=ELDER_NAMES, default=None)
    ap.add_argument("--song", choices=SONGS, default=None)
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
    place = args.place or rng.choice(["village hall", "lantern room", "barn stage"])
    name = args.name or rng.choice(HERO_NAMES)
    elder = args.elder or rng.choice(ELDER_NAMES)
    song = args.song or rng.choice(SONGS)
    return StoryParams(place=place, hero_name=name, elder_name=elder, song=song)


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
    if trace and sample.world is not None:
        print("--- trace ---")
        for line in sample.world.trace:
            print(line)
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="village hall", hero_name="Mina", elder_name="Old Mara", song="the lantern song"),
    StoryParams(place="barn stage", hero_name="Tavi", elder_name="Grandmother Reed", song="the river song"),
    StoryParams(place="lantern room", hero_name="Sora", elder_name="Aunt Willow", song="the meadow song"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show karaoke_event/0. #show embarrassed/1. #show learns/2. #show safe_try/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show karaoke_event/0. #show embarrassed/1. #show learns/2. #show safe_try/2."))
        print("ASP model:")
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
