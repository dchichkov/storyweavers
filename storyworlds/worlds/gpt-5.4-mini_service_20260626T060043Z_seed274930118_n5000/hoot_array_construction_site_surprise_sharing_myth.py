#!/usr/bin/env python3
"""
Story world: a mythic construction-site tale of hoots, an array, surprise, and sharing.

A small child-friendly myth:
- At a construction site, a clever little owl hoots at an array of beams.
- The workers expect a fallen beam or a broken plan, but instead find a hidden wind-chime.
- The owl shares the chime's song with everyone, and the site ends in a safer, happier rhythm.
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


@dataclass
class Thing:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.label in {"owl", "watcher"}:
                return {"subject": "it", "object": "it", "possessive": "its"}[case]
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class ConstructionSite:
    place: str = "the construction site"
    array_kind: str = "beam array"
    surprise_kind: str = "wind-chime"
    shared_kind: str = "song"
    myth_color: str = "golden"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, site: ConstructionSite) -> None:
        self.site = site
        self.entities: dict[str, Thing] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}

    def add(self, thing: Thing) -> Thing:
        self.entities[thing.id] = thing
        return thing

    def get(self, eid: str) -> Thing:
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
        w = World(self.site)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Mira"
    keeper: str = "foreman"
    owl_name: str = "Hoot"
    array_kind: str = "beam array"
    surprise_kind: str = "wind-chime"
    sharing_kind: str = "song"
    site_name: str = "the construction site"


SITES = {
    "construction site": ConstructionSite(place="the construction site",
                                          array_kind="beam array",
                                          surprise_kind="wind-chime",
                                          shared_kind="song",
                                          myth_color="golden")
}

NAMES = ["Mira", "Tao", "Nina", "Arlo", "Ivy", "Rafi"]
KEEPERS = ["foreman", "builder", "worker", "crane-keeper"]
OWL_NAMES = ["Hoot", "Pip", "Orin", "Sora"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld at a construction site.")
    ap.add_argument("--name")
    ap.add_argument("--keeper", choices=KEEPERS)
    ap.add_argument("--owl-name")
    ap.add_argument("--site", default="construction site", choices=list(SITES))
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
    return StoryParams(
        seed=None,
        name=args.name or rng.choice(NAMES),
        keeper=args.keeper or rng.choice(KEEPERS),
        owl_name=args.owl_name or rng.choice(OWL_NAMES),
        array_kind="beam array",
        surprise_kind="wind-chime",
        sharing_kind="song",
        site_name=args.site,
    )


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("site", "construction_site"),
        asp.fact("array", "beam_array"),
        asp.fact("surprise", "wind_chime"),
        asp.fact("sharing", "song"),
        asp.fact("has_word", "hoot"),
        asp.fact("has_word", "array"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
array_related(X) :- array(X).
surprise_related(X) :- surprise(X).
sharing_related(X) :- sharing(X).
mythic_story :- has_word(hoot), has_word(array), array_related(_), surprise_related(_), sharing_related(_).
#show mythic_story/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show mythic_story/0."))
    ok = any(s.name == "mythic_story" for s in model)
    if ok:
        print("OK: ASP confirms the mythic story shape.")
        return 0
    print("MISMATCH: ASP did not confirm the story shape.")
    return 1


def _sound(world: World, owl: Thing) -> None:
    world.say(f"{owl.label} gave a soft hoot that rang over the site like a tiny bell.")


def generate_story(world: World, hero: Thing, owl: Thing, keeper: Thing) -> None:
    site = world.site
    world.say(f"Long ago, at {site.place}, {hero.label} worked beneath {site.myth_color} dust and tall wooden frames.")
    world.say(f"Beside the cranes stood an array of beams, lined up straight as a river bank.")
    world.say(f"There also lived an owl named {owl.label}, and its hoot carried farther than a hammer tap.")
    world.para()
    world.say(f"One morning, everyone expected trouble from the array, because one beam looked oddly tilted.")
    _sound(world, owl)
    world.say(f"But the surprise was gentler than fear: tucked inside the beams was a small {site.surprise_kind}.")
    world.say(f"It had been hidden there by the wind, and when the owl hooted again, the chime answered back.")
    world.para()
    world.say(f"{hero.label} laughed, and {keeper.label} paused with a hand on the ladder.")
    world.say(f'The {site.surprise_kind} was not a danger after all; it was a gift, and the best gifts ask to be shared.')
    world.say(f"So {hero.label}, {keeper.label}, and {owl.label} listened together.")
    world.say(f"They shared the same {site.shared_kind}, and the whole construction site felt steadier, as if the beams themselves were breathing in time.")
    world.say(f"By dusk, the array stood safe and straight, and the owl's hoot had become part of the work song.")
    world.facts.update(hero=hero, owl=owl, keeper=keeper, site=site, surprise=site.surprise_kind, sharing=site.shared_kind)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    owl = f["owl"]
    return [
        'Write a short myth for a child about a construction site, a hoot, an array, surprise, and sharing.',
        f"Tell a gentle myth where {hero.label} hears {owl.label}'s hoot near an array of beams and discovers a surprise.",
        "Write a child-friendly myth set at a construction site that ends with everyone sharing a good thing they found.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    owl = f["owl"]
    keeper = f["keeper"]
    site = f["site"]
    return [
        QAItem(
            question=f"Who heard the owl's hoot at {site.place}?",
            answer=f"{hero.label} heard the owl's hoot at {site.place}, and {keeper.label} was there too.",
        ),
        QAItem(
            question=f"What surprise was hidden in the array?",
            answer=f"A {site.surprise_kind} was hidden in the array of beams, and it turned the worry into wonder.",
        ),
        QAItem(
            question=f"What did the people and the owl share at the end?",
            answer=f"They shared the {site.shared_kind} from the {site.surprise_kind}, so the whole place felt kinder and calmer.",
        ),
        QAItem(
            question=f"Why did the story end happily?",
            answer=f"It ended happily because the tilted-looking array was not broken in the end, and the surprise became something everyone could enjoy together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a construction site?",
            answer="A construction site is a place where people build houses, roads, towers, and other big things.",
        ),
        QAItem(
            question="What does hoot mean?",
            answer="A hoot is the sound an owl makes.",
        ),
        QAItem(
            question="What is an array?",
            answer="An array is a neat arrangement of things lined up in order.",
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting other people enjoy something with you.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that makes people stop and notice.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
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


def generate(params: StoryParams) -> StorySample:
    site = SITES[params.site_name]
    world = World(site)
    hero = world.add(Thing(id="hero", kind="character", label=params.name, tags={"sharing"}))
    owl = world.add(Thing(id="owl", kind="character", label=params.owl_name, tags={"hoot"}))
    keeper = world.add(Thing(id="keeper", kind="character", label=params.keeper, tags={"construction"}))
    world.facts["hero"] = hero
    world.facts["owl"] = owl
    world.facts["keeper"] = keeper
    generate_story(world, hero, owl, keeper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def valid_params(args: argparse.Namespace) -> None:
    if args.site not in SITES:
        raise StoryError("Unknown site.")
    if args.name is not None and not args.name.strip():
        raise StoryError("Name cannot be empty.")
    if args.owl_name is not None and not args.owl_name.strip():
        raise StoryError("Owl name cannot be empty.")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show mythic_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show mythic_story/0."))
        print("mythic_story" if any(s.name == "mythic_story" for s in model) else "no_model")
        return

    valid_params(args)
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(base_seed)

    samples: list[StorySample] = []
    if args.all:
        params = resolve_params(args, rng)
        params.seed = base_seed
        samples.append(generate(params))
    else:
        seen: set[str] = set()
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + i))
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
