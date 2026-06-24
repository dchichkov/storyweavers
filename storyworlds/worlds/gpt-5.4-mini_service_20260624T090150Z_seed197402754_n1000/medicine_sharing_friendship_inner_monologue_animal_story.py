#!/usr/bin/env python3
"""
A small animal-story world about sharing medicine, friendship, and a worried
inner monologue that turns into a kind choice.
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
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    name: str = ""
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    given_to: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "animal":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def ref(self) -> str:
        return self.name or self.label or self.id


@dataclass
class Setting:
    place: str = "the little meadow"
    afford_share: bool = True


@dataclass
class Medicine:
    id: str
    label: str
    flavor: str
    doses: int
    helps: str
    container: str
    safe_to_share: bool = True


@dataclass
class AnimalSpec:
    kind: str
    name: str
    species: str
    friend_word: str
    trait: str
    voice: str


@dataclass
class StoryParams:
    setting: str
    medicine: str
    giver: str
    receiver: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


SETTINGS = {
    "meadow": Setting(place="the little meadow", afford_share=True),
    "barn": Setting(place="the warm barn", afford_share=True),
    "woods": Setting(place="the quiet woods", afford_share=True),
    "riverbank": Setting(place="the sunny riverbank", afford_share=True),
}

ANIMALS = {
    "rabbit": AnimalSpec(kind="animal", name="Ruby", species="rabbit", friend_word="friend", trait="gentle", voice="soft"),
    "fox": AnimalSpec(kind="animal", name="Finn", species="fox", friend_word="pal", trait="brave", voice="warm"),
    "bear": AnimalSpec(kind="animal", name="Bella", species="bear", friend_word="friend", trait="careful", voice="deep"),
    "mole": AnimalSpec(kind="animal", name="Milo", species="mole", friend_word="buddy", trait="quiet", voice="tiny"),
    "squirrel": AnimalSpec(kind="animal", name="Sunny", species="squirrel", friend_word="pal", trait="quick", voice="bright"),
}

MEDICINES = {
    "honey_syrup": Medicine(id="honey_syrup", label="honey syrup", flavor="sweet honey", doses=2, helps="a sore throat", container="a small spoon bottle", safe_to_share=True),
    "berry_drop": Medicine(id="berry_drop", label="berry drops", flavor="berry sweet", doses=3, helps="a sniffly nose", container="a tiny glass jar", safe_to_share=True),
    "mint_tonic": Medicine(id="mint_tonic", label="mint tonic", flavor="cool mint", doses=2, helps="a tummy ache", container="a round cup", safe_to_share=True),
    "sleep_tea": Medicine(id="sleep_tea", label="sleep tea", flavor="warm herbs", doses=1, helps="a tired cough", container="a little mug", safe_to_share=False),
}

VALID_COMBOS = [
    ("meadow", "honey_syrup"),
    ("barn", "berry_drop"),
    ("woods", "mint_tonic"),
    ("riverbank", "honey_syrup"),
]


def reasonableness_gate(setting: str, medicine: str) -> bool:
    return (setting, medicine) in VALID_COMBOS and MEDICINES[medicine].safe_to_share


def select_friend(giver: AnimalSpec, rng: random.Random) -> AnimalSpec:
    choices = [a for a in ANIMALS.values() if a.name != giver.name]
    return rng.choice(choices)


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    med = MEDICINES[params.medicine]
    giver = ANIMALS[params.giver]
    receiver = ANIMALS[params.receiver]
    world = World(setting)
    giver_e = world.add(Entity(id="giver", kind="animal", type=giver.species, name=giver.name))
    receiver_e = world.add(Entity(id="receiver", kind="animal", type=receiver.species, name=receiver.name))
    bottle = world.add(Entity(id="medicine", type=med.id, label=med.label, owner=giver_e.id, carried_by=giver_e.id))
    giver_e.meters["worry"] = 0
    giver_e.meters["care"] = 0
    giver_e.memes["friendship"] = 1
    receiver_e.meters["unwell"] = 1
    world.facts.update(
        setting=params.setting, medicine=med, giver=giver, receiver=receiver,
        giver_e=giver_e, receiver_e=receiver_e, bottle=bottle
    )
    return world


def predict_share(world: World) -> dict:
    med: Medicine = world.facts["medicine"]
    return {"enough": med.doses >= 1, "safe": med.safe_to_share, "happy": True}


def introduce(world: World) -> None:
    giver: AnimalSpec = world.facts["giver"]
    receiver: AnimalSpec = world.facts["receiver"]
    med: Medicine = world.facts["medicine"]
    world.say(
        f"In {world.setting.place}, {giver.name} the {giver.species} kept {med.label} safe in {med.container}."
    )
    world.say(
        f"{receiver.name} the {receiver.species} was nearby, looking under the weather, and the two were good {giver.friend_word}s."
    )


def inner_monologue(world: World) -> None:
    giver: AnimalSpec = world.facts["giver"]
    med: Medicine = world.facts["medicine"]
    receiver: AnimalSpec = world.facts["receiver"]
    giver_e: Entity = world.facts["giver_e"]
    giver_e.meters["worry"] += 1
    world.say(
        f"{giver.name} looked at the little bottle and thought, "
        f"\"{med.label} is for {med.helps}. What if {receiver.name} really needs it?\""
    )


def ask_and_share(world: World) -> None:
    giver: AnimalSpec = world.facts["giver"]
    receiver: AnimalSpec = world.facts["receiver"]
    med: Medicine = world.facts["medicine"]
    giver_e: Entity = world.facts["giver_e"]
    receiver_e: Entity = world.facts["receiver_e"]

    if not reasonableness_gate(world.facts["setting"], med.id):
        raise StoryError("This medicine cannot be shared safely in this setting.")

    pred = predict_share(world)
    if not pred["safe"]:
        raise StoryError("The story needs a medicine that can be shared safely.")

    giver_e.meters["care"] += 1
    world.say(
        f"{giver.name} padded over and asked, \"Do you want to share my {med.label}?\""
    )
    receiver_e.memes["hope"] = 1
    world.say(
        f"{receiver.name} smiled and nodded, because that kind offer felt like a hug made of words."
    )
    if med.doses > 1:
        med.doses -= 1
        world.say(
            f"{giver.name} kept one dose for later, and the two friends took the other dose together."
        )
    else:
        med.doses = 0
        world.say(
            f"{giver.name} gave the only dose to {receiver.name}, because friendship can be a careful kind of sharing."
        )
    receiver_e.meters["unwell"] = 0
    giver_e.memes["friendship"] += 1
    receiver_e.memes["friendship"] = 1
    world.say(
        f"Soon {receiver.name} felt a little better, and {giver.name} felt proud for choosing the kinder thought."
    )


def closing_image(world: World) -> None:
    giver: AnimalSpec = world.facts["giver"]
    receiver: AnimalSpec = world.facts["receiver"]
    med: Medicine = world.facts["medicine"]
    if world.facts["receiver_e"].meters.get("unwell", 0) <= 0:
        world.say(
            f"By the end, the {med.label} was almost gone, but {giver.name} and {receiver.name} were still close by, sharing a quiet smile in {world.setting.place}."
        )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    introduce(world)
    world.para()
    inner_monologue(world)
    ask_and_share(world)
    world.para()
    closing_image(world)
    return world


def generation_prompts(world: World) -> list[str]:
    giver: AnimalSpec = world.facts["giver"]
    receiver: AnimalSpec = world.facts["receiver"]
    med: Medicine = world.facts["medicine"]
    return [
        f"Write a gentle animal story about {giver.name} sharing {med.label} with {receiver.name}.",
        f"Tell a story where a {giver.species} thinks carefully inside its head before sharing medicine with a friend.",
        f"Write a short friendship story about medicine, kind thoughts, and a safe choice in {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    giver: AnimalSpec = world.facts["giver"]
    receiver: AnimalSpec = world.facts["receiver"]
    med: Medicine = world.facts["medicine"]
    return [
        QAItem(
            question=f"Who was the medicine story about?",
            answer=f"It was about {giver.name} the {giver.species} and {receiver.name} the {receiver.species}, two friends in {world.setting.place}.",
        ),
        QAItem(
            question=f"What was {giver.name} thinking about before sharing the medicine?",
            answer=f"{giver.name} wondered if {med.label} should be shared, because it was for {med.helps} and could help a friend who felt sick.",
        ),
        QAItem(
            question=f"What did {giver.name} do to show friendship?",
            answer=f"{giver.name} asked to share the {med.label}, and {receiver.name} accepted with a smile.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {receiver.name} feeling better and the two friends staying close in {world.setting.place}.",
        ),
    ]


KNOWLEDGE = {
    "medicine": [
        (
            "What is medicine?",
            "Medicine is something that can help a sick body feel better when it is used the right way.",
        ),
        (
            "Why should medicine be used carefully?",
            "Medicine should be used carefully because the right amount and the right kind matter for safety.",
        ),
    ],
    "sharing": [
        (
            "What does sharing mean?",
            "Sharing means letting someone else use or enjoy something with you, like a toy, snack, or turn.",
        ),
    ],
    "friendship": [
        (
            "What is friendship?",
            "Friendship is when people or animals care about each other, help each other, and enjoy being together.",
        ),
    ],
    "inner_monologue": [
        (
            "What is inner monologue?",
            "Inner monologue is the quiet thinking voice inside a character's head.",
        ),
    ],
    "animal": [
        (
            "What is an animal?",
            "An animal is a living creature such as a rabbit, fox, bear, or squirrel.",
        ),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for tag in ["medicine", "sharing", "friendship", "inner_monologue", "animal"] for q, a in KNOWLEDGE[tag]]


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
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} name={e.name or e.label} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
medicine_shareable(M) :- medicine(M), safe(M).
story_valid(S, M) :- setting(S), medicine(M), afford(S, share), medicine_shareable(M).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    out = []
    for sid, s in SETTINGS.items():
        out.append(asp.fact("setting", sid))
        if s.afford_share:
            out.append(asp.fact("afford", sid, "share"))
    for mid, m in MEDICINES.items():
        out.append(asp.fact("medicine", mid))
        if m.safe_to_share:
            out.append(asp.fact("safe", mid))
    return "\n".join(out)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show story_valid/2."))
    return sorted(set(asp.atoms(model, "story_valid")))


def asp_verify() -> int:
    py = sorted((s, m) for s, m in VALID_COMBOS if MEDICINES[m].safe_to_share)
    cl = asp_valid_combos()
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python:", py)
    print("asp:", cl)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="An animal-story world about medicine, sharing, friendship, and inner monologue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--medicine", choices=MEDICINES)
    ap.add_argument("--giver", choices=ANIMALS)
    ap.add_argument("--receiver", choices=ANIMALS)
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
    combos = [c for c in VALID_COMBOS if MEDICINES[c[1]].safe_to_share]
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.medicine:
        combos = [c for c in combos if c[1] == args.medicine]
    if not combos:
        raise StoryError("No valid medicine-sharing story matches those choices.")
    setting, medicine = rng.choice(sorted(combos))
    giver = args.giver or rng.choice(list(ANIMALS))
    receiver = args.receiver or select_friend(ANIMALS[giver], rng).species
    if receiver == giver:
        receiver = select_friend(ANIMALS[giver], rng).species
    return StoryParams(setting=setting, medicine=medicine, giver=giver, receiver=receiver)


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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(setting="meadow", medicine="honey_syrup", giver="rabbit", receiver="fox"),
    StoryParams(setting="barn", medicine="berry_drop", giver="bear", receiver="mole"),
    StoryParams(setting="woods", medicine="mint_tonic", giver="squirrel", receiver="rabbit"),
    StoryParams(setting="riverbank", medicine="honey_syrup", giver="fox", receiver="bear"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show story_valid/2."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
