#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    name: str = ""
    title: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    setting: str = "the old mountain shrine"
    hero: str = "Aster"
    guide: str = "the old oracle"
    rival: str = "the king of smoke"
    indicator: str = "the bronze star-bell"
    monopoly: str = "the king of smoke"
    inquiry: str = "the oracle's question"
    quest: str = "to bring back the shared light"
    seed: Optional[int] = None


@dataclass
class Setting:
    place: str
    mood: str
    light_source: str
    weather: str


@dataclass
class Indicator:
    label: str
    signal: str
    hope: str
    plural: bool = False


@dataclass
class MythWorld:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "the old mountain shrine": Setting(
        place="the old mountain shrine",
        mood="hushed",
        light_source="a single flame",
        weather="windy",
    ),
    "the river temple": Setting(
        place="the river temple",
        mood="silver-bright",
        light_source="moonlight",
        weather="misty",
    ),
    "the thorn gate": Setting(
        place="the thorn gate",
        mood="sharp",
        light_source="a watchfire",
        weather="stormy",
    ),
}

INDICATORS = {
    "bronze_star_bell": Indicator(
        label="the bronze star-bell",
        signal="a clear ring that pointed travelers home",
        hope="the way back",
    ),
    "lantern_pulse": Indicator(
        label="the lantern pulse",
        signal="a warm blink that promised safe crossing",
        hope="the bridge path",
    ),
    "river_mirror": Indicator(
        label="the river mirror",
        signal="a shining ripple that showed hidden stones",
        hope="the shallow ford",
    ),
}

QUESTS = {
    "restore_light": "to bring back the shared light",
    "open_path": "to open the hidden path",
    "break_monopoly": "to end the lonely monopoly over the sign",
}

GUIDES = {
    "oracle": "the old oracle",
    "weaver": "the sky weaver",
    "gardener": "the ash gardener",
}


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for i in INDICATORS:
            for q in QUESTS:
                out.append((s, i, q))
    return out


def build_world(params: StoryParams) -> MythWorld:
    setting = SETTINGS[params.setting]
    world = MythWorld(setting=setting)

    hero = world.add(Entity(id=params.hero, kind="character", type="hero", name=params.hero))
    guide = world.add(Entity(id=params.guide, kind="character", type="guide", name=params.guide))
    rival = world.add(Entity(id=params.rival, kind="character", type="rival", name=params.rival))
    indicator = world.add(Entity(id=params.indicator, kind="thing", type="indicator", name=params.indicator))
    world.facts.update(hero=hero, guide=guide, rival=rival, indicator=indicator, params=params)
    return world


def intro(world: MythWorld, params: StoryParams) -> None:
    s = world.setting
    world.say(
        f"In {s.place}, where the air was {s.mood} and {s.light_source} could be seen from far away, "
        f"{params.hero} listened for the sign people had trusted since old time."
    )
    world.say(
        f"They called it {params.indicator}, and its meaning was simple: it showed {params.quest}."
    )


def monopoly_turn(world: MythWorld, params: StoryParams) -> None:
    world.say(
        f"But {params.monopoly} held a monopoly over the sign, and the villages below grew unsure."
    )
    world.say(
        f"When the bell stayed hidden, no one could tell whether the path was safe, and that fear spread like cold ash."
    )


def inquiry_scene(world: MythWorld, params: StoryParams) -> None:
    world.para()
    world.say(
        f"{params.hero} climbed the steps and asked {params.guide}, "
        f'"Why must one hand alone keep the sign?"'
    )
    world.say(
        f"{params.guide} answered, 'No road belongs to one voice forever. First come with inquiry, then with courage.'"
    )
    world.facts["inquiry"] = True


def quest_scene(world: MythWorld, params: StoryParams) -> None:
    world.say(
        f"So {params.hero} took {params.quest} and went through the wind to meet {params.rival}."
    )
    world.say(
        f"At the gate, {params.hero} carried no spear, only a question bright enough to share."
    )


def dialogue_scene(world: MythWorld, params: StoryParams) -> None:
    world.para()
    world.say(
        f'"Why keep the light to yourself?" {params.hero} asked.'
    )
    world.say(
        f'"Because I feared losing it," said {params.rival}. "I thought monopoly would make me safe."'
    )
    world.say(
        f"{params.guide} stepped beside them and said, 'A sign is strongest when many eyes may read it.'"
    )
    world.facts["dialogue"] = True


def transformation_scene(world: MythWorld, params: StoryParams) -> None:
    world.para()
    world.say(
        f"Then the old rule changed. {params.rival} opened their hand, and the sign was no longer trapped."
    )
    world.say(
        f"The bronze star-bell rang once, and its note turned into a thousand small lights over the valley."
    )
    world.say(
        f"Each house could see the path at last, and {params.hero} knew the monopoly had become a shared blessing."
    )
    world.facts["resolved"] = True


def generate_story(world: MythWorld, params: StoryParams) -> None:
    intro(world, params)
    monopoly_turn(world, params)
    inquiry_scene(world, params)
    quest_scene(world, params)
    dialogue_scene(world, params)
    transformation_scene(world, params)


def generation_prompts(world: MythWorld) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a mythic story about {p.hero} and {p.indicator}, where a monopoly causes trouble and an inquiry begins the cure.",
        f"Tell a child-friendly myth with a quest, a dialogue, and a transformation in {p.setting}.",
        f"Create a short legend in which a single keeper loses their monopoly over a sacred indicator.",
    ]


def story_qa(world: MythWorld) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(
            question=f"Who began the inquiry in the story?",
            answer=f"{p.hero} began the inquiry by asking {p.guide} why one hand should keep the sign alone.",
        ),
        QAItem(
            question=f"What problem did the story say about {p.monopoly}?",
            answer=f"It said {p.monopoly} held a monopoly over the sign, so other people could not trust the path.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"The sign was shared, and the lone light transformed into many lights over the valley.",
        ),
    ]


def world_qa(world: MythWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a brave journey to find, fix, or protect something important.",
        ),
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is when characters speak to one another and learn by talking.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is when something changes from one form or state into another.",
        ),
        QAItem(
            question="What is an indicator?",
            answer="An indicator is a sign that helps people notice what is happening or where to go.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: MythWorld) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type}")
    lines.append(f"facts={sorted(world.facts.keys())}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_setting(S) :- setting(S).
valid_indicator(I) :- indicator(I).
valid_quest(Q) :- quest(Q).
valid_story(S,I,Q) :- valid_setting(S), valid_indicator(I), valid_quest(Q).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for i in INDICATORS:
        lines.append(asp.fact("indicator", i))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP parity holds for {len(py)} combinations.")
        return 0
    print("MISMATCH between Python and ASP:")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in ASP:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic story world about an indicator, inquiry, and quest.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--indicator", choices=INDICATORS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--hero")
    ap.add_argument("--guide", choices=list(GUIDES.values()))
    ap.add_argument("--rival")
    ap.add_argument("--monopoly")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    indicator = args.indicator or rng.choice(list(INDICATORS))
    quest = args.quest or rng.choice(list(QUESTS))
    hero = args.hero or rng.choice(["Aster", "Mira", "Niko", "Lyra", "Tarin"])
    guide = args.guide or rng.choice(list(GUIDES.values()))
    rival = args.rival or rng.choice(["the king of smoke", "the queen of thorns", "the keeper of dusk"])
    monopoly = args.monopoly or rival
    return StoryParams(setting=setting, hero=hero, guide=guide, rival=rival, indicator=indicator, monopoly=monopoly, inquiry="the oracle's question", quest=quest)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    generate_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (setting, indicator, quest) combinations:")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for s in SETTINGS:
            for i in INDICATORS:
                for q in QUESTS:
                    samples.append(generate(StoryParams(setting=s, indicator=i, quest=q)))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: {p.setting} / {p.indicator} / {p.quest}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
