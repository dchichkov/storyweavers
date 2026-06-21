#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/incessant_era_locker_surprise_humor_ghost_story.py
==================================================================================

A small storyworld for a ghost-story-flavored locker-room surprise with humor.

Premise:
- A child keeps hearing incessant tapping from an old locker in an old-era gym.
- The child, a friend, and a cautious grown-up investigate.
- The "ghost" turns out to be a surprisingly funny cause, and the ending image
  proves the locker is no longer mysterious.

This world is intentionally compact: one small domain, one tension beat, one
surprising reveal, and a gentle humorous resolution. It still follows the shared
StorySample / QAItem contract and includes a Python reasonableness gate plus an
inline ASP twin.

Seed words used in-world and/or prompts:
- incessant
- era
- locker

Style cues:
- Ghost Story
- Surprise
- Humor
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    era: str
    mood: str
    details: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    source: str
    label: str
    sound: str
    reveals: str
    surprising_cause: str
    humor_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Reveal:
    id: str
    label: str
    action: str
    effect: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_tap(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["tapping"] < THRESHOLD:
            continue
        sig = ("tap", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("locker").memes["mystery"] += 1
        world.get("child").memes["unease"] += 1
        out.append("__tap__")
    return out


def _r_laugh(world: World) -> list[str]:
    out: list[str] = []
    if world.get("child").memes["surprise"] < THRESHOLD:
        return out
    sig = ("laugh",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("child").memes["relief"] += 1
    world.get("friend").memes["relief"] += 1
    out.append("__laugh__")
    return out


RULES = [Rule("tap", _r_tap), Rule("laugh", _r_laugh)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def is_reasonable(setting: Setting, mystery: Mystery, reveal: Reveal) -> bool:
    return "locker" in setting.tags and "ghost" in mystery.tags and "humor" in reveal.tags


def outcome_image(world: World) -> str:
    return "open" if world.get("locker").memes["mystery"] < THRESHOLD else "mystery"


def intro(world: World, child: Entity, friend: Entity, setting: Setting) -> None:
    world.say(
        f"In the old {setting.era}, the school gym felt full of echoes and long shadows. "
        f"{setting.details}"
    )
    world.say(
        f"{child.id} and {friend.id} tiptoed past the rows of lockers, where one locker "
        f"kept making an incessant tap-tap-tap."
    )


def scare(world: World, child: Entity, friend: Entity, mystery: Mystery) -> None:
    child.memes["curiosity"] += 1
    child.memes["surprise"] += 1
    friend.memes["curiosity"] += 1
    world.say(
        f'"Did you hear that?" {child.id} whispered. "That locker sounds haunted."'
    )
    world.say(
        f'"Maybe it is a ghost from another era," {friend.id} said, trying to sound brave '
        f"and sounding mostly squeaky."
    )
    world.say(
        f"The sound went on and on -- incessant, steady, and just spooky enough to make "
        f"their knees feel wobbly."
    )


def clue(world: World, child: Entity, mystery: Mystery) -> None:
    world.say(
        f"{child.id} leaned closer and noticed a thin ribbon of paper stuck in the locker door."
        f" It fluttered every time the tap happened."
    )
    world.say(
        f'"A ghost with a timetable?" {child.id} said. "That would be the most organized ghost ever."'
    )


def reveal(world: World, child: Entity, friend: Entity, mystery: Mystery, reveal: Reveal) -> None:
    child.meters["investigating"] += 1
    child.memes["surprise"] += 2
    friend.memes["surprise"] += 1
    world.get("locker").meters["opened"] += 1
    world.get("locker").memes["mystery"] = 0
    world.say(
        f"They pulled the locker open, and the great secret tumbled out: {mystery.surprising_cause}."
    )
    world.say(
        f"{mystery.humor_line}"
    )
    world.say(
        f"The tapping stopped at once, because {reveal.action}. "
        f"Inside, there was only a silly little surprise, not a ghost at all."
    )


def ending(world: World, child: Entity, friend: Entity, reveal_cfg: Reveal) -> None:
    child.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"{child.id} shut the locker gently and grinned. {reveal_cfg.ending_image}"
    )
    world.say(
        f'"So the haunted locker was just {reveal_cfg.effect}?" {friend.id} asked.'
    )
    world.say(
        f'"Yep," {child.id} said. "The scariest ghost in the gym was a very silly noise."'
    )


def tell(setting: Setting, mystery: Mystery, reveal_cfg: Reveal,
         child_name: str = "Mina", child_gender: str = "girl",
         friend_name: str = "Beau", friend_gender: str = "boy") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    locker = world.add(Entity(id="locker", type="locker", label="the locker", role="mystery-object"))
    world.add(Entity(id="gym", type="room", label=setting.place))
    world.facts.update(setting=setting, mystery=mystery, reveal=reveal_cfg, child=child, friend=friend, locker=locker)

    intro(world, child, friend, setting)
    world.para()
    scare(world, child, friend, mystery)
    clue(world, child, mystery)
    locker.meters["tapping"] += 1
    propagate(world, narrate=False)
    world.para()
    reveal(world, child, friend, mystery, reveal_cfg)
    ending(world, child, friend, reveal_cfg)
    world.facts.update(outcome="revealed", child_surprised=child.memes["surprise"] >= THRESHOLD)
    return world


SETTINGS = {
    "gym": Setting(
        id="gym",
        place="old school gym",
        era="era of wooden floors and clattering pipes",
        mood="echoing",
        details="Even the rafters seemed to listen.",
        tags={"era", "locker"},
    ),
    "hall": Setting(
        id="hall",
        place="long school hallway",
        era="era of squeaky shoes and brass bells",
        mood="hushed",
        details="A line of dented lockers stood like sleepy giants.",
        tags={"era", "locker"},
    ),
}

MYSTERIES = {
    "broom": Mystery(
        id="broom",
        source="ghostly tapping",
        label="a haunted locker",
        sound="tap-tap-tap",
        reveals="a ghostly tapping sound",
        surprising_cause="a broom handle had slipped and was knocking the locker door from inside",
        humor_line="A broom was the ghost, which was rude but also very funny.",
        tags={"ghost", "surprise", "humor"},
    ),
    "ball": Mystery(
        id="ball",
        source="ghostly tapping",
        label="a haunted locker",
        sound="tap-tap-tap",
        reveals="a mysterious clatter",
        surprising_cause="a bouncy ball had been trapped inside and kept thumping like an impatient drum",
        humor_line="The 'ghost' was only a ball with a big attitude.",
        tags={"ghost", "surprise", "humor"},
    ),
    "metronome": Mystery(
        id="metronome",
        source="ghostly tapping",
        label="a haunted locker",
        sound="tap-tap-tap",
        reveals="a ghostly beat",
        surprising_cause="a tiny old metronome had been left in there by the music teacher",
        humor_line="It was not a ghost; it was a tiny drummer in disguise.",
        tags={"ghost", "surprise", "humor"},
    ),
}

REVEALS = {
    "laugh": Reveal(
        id="laugh",
        label="a laugh",
        action="the thing that made the noise was only a broom, a ball, or a metronome",
        effect="an ordinary object acting dramatic",
        ending_image="They laughed so hard the hallway echo laughed too.",
        tags={"humor"},
    ),
    "sneak": Reveal(
        id="sneak",
        label="a sneak",
        action="the noise came from something ridiculous, not a monster",
        effect="a harmless old thing",
        ending_image="The locker stood quiet and harmless, like it was embarrassed.",
        tags={"humor"},
    ),
}

GIRL_NAMES = ["Mina", "Nora", "Tia", "Lena", "Zoe"]
BOY_NAMES = ["Beau", "Finn", "Owen", "Jules", "Kai"]
TRAITS = ["brave", "curious", "careful", "sly", "sensible"]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    reveal: str
    child_name: str
    child_gender: str
    friend_name: str
    friend_gender: str
    trait: str = "curious"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for mid, mystery in MYSTERIES.items():
            for rid, reveal in REVEALS.items():
                if is_reasonable(setting, mystery, reveal):
                    combos.append((sid, mid, rid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting: Setting = f["setting"]
    mystery: Mystery = f["mystery"]
    child: Entity = f["child"]
    return [
        f'Write a child-friendly ghost story that includes the words "incessant", "era", and "locker".',
        f"Tell a humorous ghost story in an old {setting.place} where {child.id} hears incessant tapping from a locker and discovers the joke behind it.",
        f"Write a surprise ending story in the style of a ghost story: make the locker seem haunted, then reveal a funny cause.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child: Entity = f["child"]
    friend: Entity = f["friend"]
    mystery: Mystery = f["mystery"]
    setting: Setting = f["setting"]
    qa = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {friend.id}, two kids exploring an old locker in a spooky school setting. The story keeps the focus on their surprise and the funny reveal.",
        ),
        (
            "Why did the locker seem spooky at first?",
            f"It kept making an incessant tapping noise in an old era gym, so it felt like a ghost story. The sound went on long enough to make them guess the locker was haunted.",
        ),
        (
            "What was the surprise?",
            f"The surprise was that {mystery.surprising_cause}. It was not a ghost at all, just a silly ordinary thing making noise.",
        ),
        (
            "How did the story end?",
            f"It ended with the locker quiet and the children laughing. The spooky mystery turned into a harmless joke, which is why the ending feels funny instead of scary.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        (
            "What does incessant mean?",
            "Incessant means something keeps happening again and again without stopping. A noise that is incessant can feel hard to ignore.",
        ),
        (
            "What is an era?",
            "An era is a long stretch of time in history. People use it to talk about a certain age or time period.",
        ),
        (
            "What is a locker?",
            "A locker is a small box with a door where people keep their things safe. School lockers often line hallways or gym walls.",
        ),
        (
            "Why do ghost stories often feel spooky?",
            "Ghost stories feel spooky because they use dark places, strange sounds, and mysteries that are not explained right away. The surprise at the end can make the story fun too.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="gym", mystery="broom", reveal="laugh", child_name="Mina", child_gender="girl", friend_name="Beau", friend_gender="boy", trait="curious"),
    StoryParams(setting="hall", mystery="ball", reveal="sneak", child_name="Nora", child_gender="girl", friend_name="Finn", friend_gender="boy", trait="careful"),
    StoryParams(setting="gym", mystery="metronome", reveal="laugh", child_name="Kai", child_gender="boy", friend_name="Zoe", friend_gender="girl", trait="brave"),
]


def explain_rejection() -> str:
    return "(No story: this world only supports spooky locker mysteries with a humorous surprise reveal.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story locker world with surprise and humor.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--reveal", choices=REVEALS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    if args.setting and args.setting not in SETTINGS:
        raise StoryError(explain_rejection())
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.reveal is None or c[2] == args.reveal)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, reveal = rng.choice(sorted(combos))
    child_gender = "girl" if rng.random() < 0.5 else "boy"
    friend_gender = "boy" if child_gender == "girl" else "girl"
    child_name = args.name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    friend_name = args.friend or rng.choice(BOY_NAMES if friend_gender == "boy" else GIRL_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(setting=setting, mystery=mystery, reveal=reveal, child_name=child_name, child_gender=child_gender, friend_name=friend_name, friend_gender=friend_gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.mystery not in MYSTERIES or params.reveal not in REVEALS:
        raise StoryError("(Invalid parameters for this storyworld.)")
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], REVEALS[params.reveal], params.child_name, params.child_gender, params.friend_name, params.friend_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


ASP_RULES = r"""
ghost_story(S, M, R) :- setting(S), mystery(M), reveal(R).
reasonable(S, M, R) :- setting(S), mystery(M), reveal(R), has_tags(S, era), has_tags(S, locker),
                        mystery_tag(M, ghost), mystery_tag(M, surprise), reveal_tag(R, humor).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for tag in sorted(s.tags):
            lines.append(asp.fact("has_tags", sid, tag))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        for tag in sorted(m.tags):
            lines.append(asp.fact("mystery_tag", mid, tag))
    for rid, r in REVEALS.items():
        lines.append(asp.fact("reveal", rid))
        for tag in sorted(r.tags):
            lines.append(asp.fact("reveal_tag", rid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/3."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH: ASP gate differs from Python valid_combos().")
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:
        rc = 1
        print(f"FAIL: generate() smoke test crashed: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show reasonable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} reasonable story combinations:")
        for setting, mystery, reveal in combos:
            print(f"  {setting:6} {mystery:10} {reveal}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.child_name} in the {p.setting} ({p.mystery} -> {p.reveal})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
