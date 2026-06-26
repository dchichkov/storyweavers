#!/usr/bin/env python3
"""
A standalone story world for a small mystery about brimmed things, sound clues,
dialogue, and teamwork.

Seed premise:
A child loses a brimmed hat before a little outing. The search turns into a
tiny mystery: strange sounds, careful listening, a helpful partner, and a final
reveal that explains where the hat really was.

The world simulates a few physical and emotional meters:
- location and hiding spots
- sound clues and who notices them
- how worried or curious each character feels
- teamwork that can lower worry and uncover the hidden item
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
    owner: Optional[str] = None
    hidden_in: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    hiding_spots: list[str]
    ambient_sounds: list[str]


@dataclass
class MysteryItem:
    id: str
    label: str
    phrase: str
    hidden_spot: str
    sound_clue: str
    at_risk: bool = True


@dataclass
class HelperPlan:
    id: str
    label: str
    method: str
    teamwork_line: str
    reveal_line: str


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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "porch": Setting(
        place="the porch",
        hiding_spots=["under the bench", "behind the watering can", "inside the shoe basket"],
        ambient_sounds=["drip-drip", "tap-tap", "creak"],
    ),
    "garden": Setting(
        place="the garden",
        hiding_spots=["behind the flower pot", "under the table", "near the hose"],
        ambient_sounds=["rustle-rustle", "buzz-buzz", "drip-drip"],
    ),
    "attic": Setting(
        place="the attic",
        hiding_spots=["under the old trunk", "behind the quilt box", "next to the window"],
        ambient_sounds=["thump", "creak-creak", "whisper-whoosh"],
    ),
}

ITEMS = {
    "sunhat": MysteryItem(
        id="sunhat",
        label="sunhat",
        phrase="a straw sunhat with a wide brim",
        hidden_spot="under the bench",
        sound_clue="swish-swish",
    ),
    "cap": MysteryItem(
        id="cap",
        label="cap",
        phrase="a blue cap with a curved brim",
        hidden_spot="behind the watering can",
        sound_clue="flip-flip",
    ),
    "detective_hat": MysteryItem(
        id="detective_hat",
        label="hat",
        phrase="a little detective hat with a brim",
        hidden_spot="inside the shoe basket",
        sound_clue="scritch-scritch",
    ),
}

HELPERS = {
    "sister": HelperPlan(
        id="sister",
        label="older sister",
        method="listen at the same time",
        teamwork_line="One person listened, while the other checked each spot.",
        reveal_line="Together, they lifted the basket and looked underneath.",
    ),
    "mother": HelperPlan(
        id="mother",
        label="mom",
        method="shine a flashlight and move the boxes",
        teamwork_line="One voice called the clues, and the other hands searched carefully.",
        reveal_line="Together, they shone the light into the corner and moved the box aside.",
    ),
    "friend": HelperPlan(
        id="friend",
        label="best friend",
        method="follow the sounds and peek behind things",
        teamwork_line="They worked like a tiny detective team.",
        reveal_line="Together, they peeked behind the pot and found the answer.",
    ),
}

NAMES = {
    "girl": ["Mia", "Lily", "Ava", "Zoe", "Nora"],
    "boy": ["Leo", "Sam", "Ben", "Theo", "Max"],
}

TRAITS = ["curious", "careful", "brave", "gentle", "sharp-eyed"]


@dataclass
class StoryParams:
    setting: str
    item: str
    helper: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def _is_reasonable(setting: Setting, item: MysteryItem, helper: HelperPlan) -> bool:
    return bool(setting.hiding_spots) and item.at_risk and helper.method


def explain_rejection(setting: Setting, item: MysteryItem, helper: HelperPlan) -> str:
    return (
        f"(No story: the mystery needs a real hiding spot, a brimmed item to search for, "
        f"and a helper who can solve it with teamwork. This combination does not work.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery story world with brim clues and teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    setting_id = args.setting or rng.choice(sorted(SETTINGS))
    item_id = args.item or rng.choice(sorted(ITEMS))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    setting = SETTINGS[setting_id]
    item = ITEMS[item_id]
    helper = HELPERS[helper_id]
    if not _is_reasonable(setting, item, helper):
        raise StoryError(explain_rejection(setting, item, helper))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting_id, item=item_id, helper=helper_id, name=name, gender=gender, trait=trait)


def _hero_pronouns(gender: str) -> tuple[str, str, str]:
    return ("she", "her", "her") if gender == "girl" else ("he", "him", "his")


def tell(setting: Setting, item: MysteryItem, helper: HelperPlan, name: str, gender: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, label=name, meters={"worry": 0.0}, memes={"curiosity": 1.0, "worry": 0.0}))
    assistant = world.add(Entity(id="helper", kind="character", type="mother" if helper.id == "mother" else "girl", label=helper.label, meters={"focus": 1.0}, memes={"teamwork": 1.0}))
    lost_item = world.add(Entity(id=item.id, type="thing", label=item.label, phrase=item.phrase, owner=hero.id, hidden_in=item.hidden_spot))
    world.facts.update(hero=hero, helper=assistant, item=lost_item, plan=helper, trait=trait)

    subj, obj, pos = _hero_pronouns(gender)
    world.say(f"{name} was a {trait} little {gender} who loved puzzles and noticed tiny things.")
    world.say(f"One morning, {name} reached for {pos} {item.label}, but it was gone.")
    world.say(f'“Hmm,” {subj} said, looking around. “That is strange.”')

    world.para()
    world.say(f"{setting.place.capitalize()} was quiet except for {random.choice(setting.ambient_sounds)}.")
    world.say(f"{name} listened closely. {item.sound_clue} seemed to float from somewhere nearby.")
    world.say(f'“Did you hear that?” {subj} asked {helper.label}. “It sounds like a clue.”')
    world.say(f'“I heard it,” {helper.label} said. “Let’s work together.”')
    hero.memes["worry"] += 1.0

    world.para()
    world.say(helper.teamwork_line)
    world.say(f"{name} checked {setting.hiding_spots[0]}, then {setting.hiding_spots[1]}.")
    world.say(f"{helper.label} moved slowly and said, “No rush. Mystery clues like to hide where we can look twice.”")
    world.say(f"Then came a soft {item.sound_clue} again: {item.sound_clue}.")

    world.para()
    world.say(helper.reveal_line)
    world.say(f"Under the last spot, there it was: {item.phrase}.")
    lost_item.hidden_in = None
    lost_item.worn_by = hero.id
    hero.memes["worry"] = 0.0
    hero.memes["relief"] = 1.0
    hero.memes["joy"] = 1.0
    world.say(f'“Found it!” {subj} laughed. “We solved it!”')
    world.say(f'{helper.label} smiled. “Yes — by listening, talking, and helping each other.”')
    world.say(f"In the end, {name} wore the {item.label} again, and the brim made a neat shadow over {pos} eyes.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item = f["item"]
    plan = f["plan"]
    return [
        f'Write a short mystery story for a young child about {hero.id} losing {hero.pronoun("possessive")} {item.label}.',
        f'Tell a gentle detective story with sound clues, dialogue, and teamwork, and include the word "brim".',
        f'Write a child-friendly mystery where {hero.id} and {plan.label} solve a small problem by listening carefully.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    item: Entity = f["item"]
    plan: HelperPlan = f["plan"]
    return [
        QAItem(
            question=f"What was missing when {hero.id} reached for {hero.pronoun('possessive')} {item.label}?",
            answer=f"{hero.id} could not find {hero.pronoun('possessive')} {item.label}, so it became a little mystery.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} and {plan.label} search?",
            answer=f"They heard a soft sound clue, {ITEMS[item.id].sound_clue}, which pointed them to the hiding place.",
        ),
        QAItem(
            question=f"How did {hero.id} and {plan.label} solve the mystery?",
            answer=f"They solved it by listening carefully, talking about the clues, and working together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is the brim of a hat?",
            answer="The brim is the part that sticks out around the edge of a hat and helps shade the face.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do different jobs to reach the same goal.",
        ),
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps someone figure out what happened.",
        ),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A valid story needs a hero, a helper, and a brimmed item that can be found.
reasonable(S, I, H) :- setting(S), item(I), helper(H).

% A mystery is solvable when the item has a hidden spot and the helper can work with the hero.
solvable(S, I, H) :- reasonable(S, I, H), hidden_spot(I, _), teamwork(H).

#show reasonable/3.
#show solvable/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("hidden_spot", iid, item.hidden_spot))
        lines.append(asp.fact("sound_clue", iid, item.sound_clue))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("teamwork", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show reasonable/3.\n#show solvable/3."))
    atoms = asp.atoms(model, "reasonable")
    if atoms:
        print(f"OK: ASP produced {len(atoms)} reasonable combinations.")
        return 0
    print("MISMATCH: ASP did not produce any reasonable combinations.")
    return 1


def asp_friendly_list() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/3."))
    return sorted(set(asp.atoms(model, "reasonable")))


CURATED = [
    StoryParams(setting="porch", item="sunhat", helper="mother", name="Mia", gender="girl", trait="curious"),
    StoryParams(setting="garden", item="cap", helper="friend", name="Leo", gender="boy", trait="sharp-eyed"),
    StoryParams(setting="attic", item="detective_hat", helper="sister", name="Ava", gender="girl", trait="careful"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for i in ITEMS:
            for h in HELPERS:
                if _is_reasonable(SETTINGS[s], ITEMS[i], HELPERS[h]):
                    combos.append((s, i, h))
    return combos


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
    world = tell(SETTINGS[params.setting], ITEMS[params.item], HELPERS[params.helper], params.name, params.gender, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def explain_gender(gender: str, item_id: str) -> str:
    return f"(No story: this item is not a typical {gender} choice in this world.)"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable/3.\n#show solvable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_friendly_list()
        print(f"{len(combos)} reasonable combinations:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.setting}, {p.item}, {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
