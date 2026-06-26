#!/usr/bin/env python3
"""
storyworlds/worlds/contemporary_bias_repetition_sharing_rhyming_story.py
=======================================================================

A standalone story world for a small contemporary rhyme-and-sharing tale.

Premise:
- In a modern classroom, children are preparing a tiny rhyme performance.
- One child is unfairly assumed to be the best because of a shiny device and a polished look.
- The main turn comes when the child with the simpler tool shares the turn, and everyone discovers the rhyme works better when it is repeated together.

The world model tracks:
- meters: physical objects, turn tokens, and shared props
- memes: confidence, worry, pride, fairness, delight, and belonging

The style aim is a child-facing rhyming story with repetition and sharing, not a frozen paragraph.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

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
    affords: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    kind: str
    praise: str
    shares: bool = False
    rhymes_with: str = ""


@dataclass
class StoryParams:
    place: str
    prop: str
    hero: str
    hero_type: str
    friend: str
    friend_type: str
    adult: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


SETTINGS = {
    "classroom": Setting(place="the classroom", affords={"mic"}),
    "library": Setting(place="the library corner", affords={"mic"}),
    "clubroom": Setting(place="the clubroom", affords={"mic"}),
}

PROPS = {
    "mic": Prop(
        id="mic",
        label="microphone",
        phrase="a shiny little microphone",
        kind="device",
        praise="bright and neat",
        shares=True,
        rhymes_with="click",
    ),
    "speaker": Prop(
        id="speaker",
        label="speaker",
        phrase="a small speaker",
        kind="device",
        praise="loud and neat",
        shares=True,
        rhymes_with="clear",
    ),
    "notebook": Prop(
        id="notebook",
        label="notebook",
        phrase="a paper notebook",
        kind="tool",
        praise="simple and sweet",
        shares=True,
        rhymes_with="note",
    ),
}

HERO_NAMES = ["Maya", "Noah", "Luna", "Eli", "Ava", "Theo", "Zuri", "Kai"]
FRIEND_NAMES = ["Nia", "Owen", "Ruby", "Milo", "Iris", "Finn"]
ADULT_NAMES = ["Ms. Park", "Mr. Lee", "Coach Sam", "Ms. Reed"]


def rhyme_line(name: str, prop_label: str) -> str:
    return f"{name} said, 'Let us sing with a ring and a ding by the {prop_label}.'"


def rhyme_chorus(prop_label: str) -> str:
    return f"Ring the thing, then share the tune; one soft voice can bloom like June."


def prop_line(prop: Prop) -> str:
    return f"The {prop.label} looked {prop.praise}, with a little {prop.rhymes_with} in its grin."


def fairness_line() -> str:
    return "That was not fair, and it did not feel right."


def sharing_line() -> str:
    return "So they shared the turn and took it one by one."


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_bias_to_worry(world: World) -> list[str]:
    hero = world.get("hero")
    adult = world.get("adult")
    prop = world.get("prop")
    out = []
    if hero.memes.get("overlooked", 0) >= THRESHOLD and ("bias_worry", hero.id) not in world.fired:
        world.fired.add(("bias_worry", hero.id))
        hero.memes["worry"] = hero.memes.get("worry", 0) + 1
        adult.memes["concern"] = adult.memes.get("concern", 0) + 1
        out.append(f"{hero.id} felt small beside the shiny {prop.label}.")
    return out


def _r_sharing_softens(world: World) -> list[str]:
    hero = world.get("hero")
    friend = world.get("friend")
    prop = world.get("prop")
    out = []
    if hero.memes.get("sharing", 0) >= THRESHOLD and ("share_soften", hero.id) not in world.fired:
        world.fired.add(("share_soften", hero.id))
        hero.memes["belonging"] = hero.memes.get("belonging", 0) + 1
        friend.memes["belonging"] = friend.memes.get("belonging", 0) + 1
        prop.meters["shared_turns"] = prop.meters.get("shared_turns", 0) + 1
        out.append(f"Sharing made the room feel warm and bright.")
    return out


CAUSAL_RULES = [Rule("bias_worry", _r_bias_to_worry), Rule("share_soften", _r_sharing_softens)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(setting: Setting, prop_def: Prop, hero_name: str, hero_type: str,
         friend_name: str, friend_type: str, adult_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name))
    friend = world.add(Entity(id="friend", kind="character", type=friend_type, label=friend_name))
    adult = world.add(Entity(id="adult", kind="character", type="adult", label=adult_name))
    prop = world.add(Entity(id="prop", kind="thing", type=prop_def.kind, label=prop_def.label, phrase=prop_def.phrase))
    prop.meters["clean"] = 1
    hero.memes["hope"] = 1
    friend.memes["curious"] = 1
    adult.memes["fairness"] = 1

    world.say(f"In {setting.place}, {hero_name} found {prop_def.phrase} on a bright school day.")
    world.say(f"{hero_name} loved its little click, and {friend_name} liked the neat, sweet trick.")
    world.say(prop_line(prop_def))
    world.say(f"{adult_name} smiled at the shiny {prop_def.label} and picked it first for the show.")
    hero.memes["overlooked"] = 1
    adult.memes["bias"] = 1
    world.say(fairness_line())

    world.para()
    world.say(f"{hero_name} wanted a turn, but the turn kept slipping away.")
    world.say(f"{hero_name} said, 'I can rhyme with a chime, on time, in line.'")
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(f"{friend_name} heard the rhyme and nodded in time.")
    world.say(f"{friend_name} said, 'Let's share the {prop_def.label}; let's hear each voice clear.'")

    hero.memes["sharing"] = 1
    friend.memes["sharing"] = 1
    prop.meters["shared_turns"] = prop.meters.get("shared_turns", 0) + 1
    propagate(world, narrate=False)

    world.para()
    world.say(sharing_line())
    world.say(f"Then {hero_name} sang, then {friend_name} sang, and the rhyme rang strong.")
    world.say(rhyme_chorus(prop_def.label))
    world.say(f"{adult_name} laughed and said the room sounded better when everyone could sing together.")
    hero.memes["delight"] = hero.memes.get("delight", 0) + 1
    friend.memes["delight"] = friend.memes.get("delight", 0) + 1
    adult.memes["pride"] = adult.memes.get("pride", 0) + 1
    hero.memes["belonging"] = hero.memes.get("belonging", 0) + 1

    world.facts.update(
        hero=hero,
        friend=friend,
        adult=adult,
        prop=prop,
        setting=setting,
        prop_def=prop_def,
        bias=True,
        sharing=True,
    )
    return world


KNOWLEDGE = {
    "microphone": [
        QAItem(
            question="What is a microphone for?",
            answer="A microphone helps a voice become louder so other people can hear it better."
        )
    ],
    "speaker": [
        QAItem(
            question="What does a speaker do?",
            answer="A speaker plays sound so a room can hear music, voices, or a story."
        )
    ],
    "notebook": [
        QAItem(
            question="What is a notebook for?",
            answer="A notebook is for writing ideas, lists, and little drawings."
        )
    ],
    "sharing": [
        QAItem(
            question="What does it mean to share a turn?",
            answer="Sharing a turn means letting other people have a fair chance too."
        )
    ],
    "bias": [
        QAItem(
            question="What is bias?",
            answer="Bias means choosing one person or thing unfairly before you really look at everyone."
        )
    ],
    "repeat": [
        QAItem(
            question="Why do people repeat a rhyme?",
            answer="People repeat a rhyme so it is easier to remember and fun to say together."
        )
    ],
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: contemporary bias, repetition, sharing, rhyming.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-type", choices=["girl", "boy"])
    ap.add_argument("--adult")
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


def valid_combos() -> list[tuple[str, str]]:
    return [("classroom", "mic"), ("library", "notebook"), ("clubroom", "speaker")]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place and args.prop and (args.place, args.prop) not in combos:
        raise StoryError("No reasonable story matches that place and prop.")
    place, prop = rng.choice([c for c in combos if (not args.place or c[0] == args.place) and (not args.prop or c[1] == args.prop)])
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or ("boy" if hero_type == "girl" else "girl")
    return StoryParams(
        place=place,
        prop=prop,
        hero=args.hero or rng.choice(HERO_NAMES),
        hero_type=hero_type,
        friend=args.friend or rng.choice(FRIEND_NAMES),
        friend_type=friend_type,
        adult=args.adult or rng.choice(ADULT_NAMES),
    )


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    adult = f["adult"]
    prop = f["prop"]
    prop_def = f["prop_def"]
    return [
        QAItem(
            question=f"Why did {adult.label} worry about {prop.label} at first?",
            answer=f"{adult.label} worried because the shiny {prop.label} seemed to get the first and best attention. That was bias, which is not fair."
        ),
        QAItem(
            question=f"What did {hero.label} and {friend.label} do to fix the problem?",
            answer=f"They shared the {prop.label} and took turns saying the rhyme. That made the story fairer and sweeter."
        ),
        QAItem(
            question=f"What made the rhyme sound best in the end?",
            answer=f"Repeating the rhyme together made it strong and easy to hear. The shared voices worked like one happy song."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    tags = {"bias", "sharing", "repeat", world.facts["prop_def"].id}
    out: list[QAItem] = []
    for tag in ["bias", "sharing", "repeat", world.facts["prop_def"].id]:
        if tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story for young children set in {f["setting"].place} about bias and sharing.',
        f"Tell a contemporary classroom story where {f['hero'].label} is overlooked at first, then gets a fair turn.",
        f"Write a gentle rhyme story using a {f['prop_def'].label} and repeating lines about taking turns.",
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
        lines.append(f"  {e.id:8} ({e.kind:9}) {e.label:12} {' '.join(bits)}")
    return "\n".join(lines)


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


ASP_RULES = r"""
valid_story(Place, Prop) :- place(Place), prop(Prop), affords(Place, Prop), fair_fix(Prop).
fair_fix(mic).
fair_fix(speaker).
fair_fix(notebook).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for p in sorted(setting.affords):
            lines.append(asp.fact("affords", place, p))
    for pid, prop in PROPS.items():
        lines.append(asp.fact("prop", pid))
        if prop.shares:
            lines.append(asp.fact("shares", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gate")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        PROPS[params.prop],
        params.hero,
        params.hero_type,
        params.friend,
        params.friend_type,
        params.adult,
    )
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


CURATED = [
    StoryParams(place="classroom", prop="mic", hero="Maya", hero_type="girl", friend="Nia", friend_type="girl", adult="Ms. Park"),
    StoryParams(place="library", prop="notebook", hero="Noah", hero_type="boy", friend="Milo", friend_type="boy", adult="Mr. Lee"),
    StoryParams(place="clubroom", prop="speaker", hero="Zuri", hero_type="girl", friend="Iris", friend_type="girl", adult="Ms. Reed"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for place, prop in triples:
            print(f"  {place:10} {prop}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
