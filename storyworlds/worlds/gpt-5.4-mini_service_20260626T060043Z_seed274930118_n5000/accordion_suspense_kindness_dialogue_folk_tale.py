#!/usr/bin/env python3
"""
storyworlds/worlds/accordion_suspense_kindness_dialogue_folk_tale.py
=====================================================================

A small folk-tale storyworld about an accordion, a tense little problem, and a
kindly fix.

Premise:
- In a village by the wood and river, someone treasures an accordion.
- The accordion can calm a crowd, wake courage, or guide a lonely walk home.
- A hush, a missing strap, a storm, or a wrong note can create suspense.
- Kindness and dialogue can turn the trouble into a warm ending.

The simulation tracks physical meters and emotional memes so the prose is
driven by world state rather than a frozen template.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother", "sister"}
        male = {"boy", "father", "man", "grandfather", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    def touch(self, key: str, delta: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + delta

    def feel(self, key: str, delta: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + delta


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Event:
    id: str
    verb: str
    gerund: str
    trouble: str
    risk: str
    stage: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    guards: set[str]
    fits: set[str]
    prep: str
    tail: str


@dataclass
class StoryParams:
    place: str
    event: str
    charm: str
    name: str
    gender: str
    kin: str
    trait: str
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

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        return c


EVENTS = {
    "market": Event(
        id="market",
        verb="play a tune at the market",
        gerund="playing bright market tunes",
        trouble="the crowd might grow nervous without music",
        risk="quiet",
        stage="market square",
        keyword="market",
        tags={"crowd", "music", "dialogue"},
    ),
    "bridge": Event(
        id="bridge",
        verb="cross the old bridge at dusk",
        gerund="walking the bridge path",
        trouble="the dark river might feel spooky",
        risk="suspense",
        stage="bridge",
        keyword="bridge",
        tags={"river", "night", "suspense"},
    ),
    "barn": Event(
        id="barn",
        verb="lead the barn dancers",
        gerund="dancing with the villagers",
        trouble="the steps could be forgotten",
        risk="dance",
        stage="barn",
        keyword="barn",
        tags={"dance", "crowd", "music"},
    ),
    "forest": Event(
        id="forest",
        verb="call the path-folk home",
        gerund="sending sound through the trees",
        trouble="the woods might swallow a weak sound",
        risk="echo",
        stage="forest path",
        keyword="forest",
        tags={"woods", "echo", "kindness"},
    ),
}

CHARMS = {
    "strap": Charm(
        id="strap",
        label="a braided strap",
        phrase="a braided strap with a soft knot",
        guards={"drop"},
        fits={"accordion"},
        prep="tie on the braided strap",
        tail="fastened the braided strap tight",
    ),
    "cloth": Charm(
        id="cloth",
        label="a dry cloth wrap",
        phrase="a dry cloth wrap for the bellows",
        guards={"rain"},
        fits={"accordion"},
        prep="wrap the accordion in dry cloth",
        tail="wrapped the accordion in dry cloth",
    ),
    "lantern": Charm(
        id="lantern",
        label="a little lantern",
        phrase="a little lantern with a warm flame",
        guards={"dark"},
        fits={"path"},
        prep="light a little lantern",
        tail="held the lantern high",
    ),
}

SETTINGS = {
    "village": Setting(place="the village green", indoor=False, affords={"market", "barn", "forest"}),
    "bridge": Setting(place="the old bridge", indoor=False, affords={"bridge"}),
    "path": Setting(place="the pine path", indoor=False, affords={"forest"}),
}

NAMES_GIRL = ["Mira", "Elsa", "Nina", "Tala", "Lina", "Anya"]
NAMES_BOY = ["Bram", "Oren", "Pavel", "Jory", "Kian", "Milo"]
TRAITS = ["gentle", "brave", "curious", "kind", "quiet", "lively"]


def event_at_risk(event: Event) -> bool:
    return True


def select_charm(event: Event) -> Optional[Charm]:
    if event.id == "bridge":
        return CHARMS["lantern"]
    if event.id == "market":
        return CHARMS["strap"]
    if event.id == "barn":
        return CHARMS["strap"]
    if event.id == "forest":
        return CHARMS["lantern"]
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for ev in setting.affords:
            charm = select_charm(EVENTS[ev])
            if charm is not None:
                combos.append((place, ev, charm.id))
    return combos


def create_world(setting: Setting, event: Event, charm: Charm, hero_name: str, gender: str, kin: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, meters={}, memes={"hope": 0.0, "fear": 0.0, "kindness": 0.0, "joy": 0.0}))
    elder = world.add(Entity(id="Elder", kind="character", type=kin, label=f"the {kin}", meters={}, memes={"worry": 0.0, "love": 0.0}))
    accordion = world.add(Entity(id="accordion", type="accordion", label="accordion", phrase="an old red accordion", owner=hero.id, caretaker=elder.id))
    world.facts.update(hero=hero, elder=elder, accordion=accordion, event=event, charm=charm, trait=trait)
    return world


def opening(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    elder: Entity = f["elder"]
    event: Event = f["event"]
    world.say(
        f"In a small village by the river, {hero.id} was a {f['trait']} little {hero.type} who loved an old red accordion."
    )
    world.say(
        f"{hero.pronoun().capitalize()} played {event.gerund}, and the notes could make a tired face wake up into a smile."
    )
    world.say(
        f"The {elder.label_word if hasattr(elder, 'label_word') else elder.label} had brought the accordion home long ago, and everyone said it had a brave little voice."
    )


def tension(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    elder: Entity = f["elder"]
    event: Event = f["event"]
    hero.feel("fear", 1.0)
    elder.feel("worry", 1.0)
    world.para()
    world.say(
        f"One dusk, {hero.id} went to {world.setting.place} for {event.verb}, but the wind slipped under the rooftops and made the path feel hush-quiet."
    )
    world.say(
        f"{hero.id} said, \"Do you hear that?\" and {elder.id} answered, \"I do. The night is near, and the tune must be careful.\""
    )
    world.say(
        f"Then the accordion gave a small, shaky sound, and {hero.id} worried that the song might fail just when it was needed most."
    )


def turn(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    elder: Entity = f["elder"]
    charm: Charm = f["charm"]
    event: Event = f["event"]
    world.para()
    world.say(
        f"{elder.id} did not scold. {elder.pronoun().capitalize()} only smiled and said, \"Tell me what you fear, child.\""
    )
    world.say(
        f"{hero.id} whispered, \"I fear the villagers will be lonely if the accordion stays silent.\""
    )
    world.say(
        f"{elder.id} answered, \"Then we will help it speak kindly.\""
    )
    world.say(
        f"{elder.pronoun().capitalize()} showed {hero.id} the {charm.label} and said, \"{charm.prep}, and I will walk beside you.\""
    )
    world.say(
        f"So {hero.id} {charm.tail}, and the accordion sat safer against {hero.pronoun('possessive')} chest."
    )
    hero.feel("kindness", 1.0)
    hero.feel("joy", 1.0)
    elder.feel("love", 1.0)


def resolution(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    elder: Entity = f["elder"]
    event: Event = f["event"]
    charm: Charm = f["charm"]
    world.para()
    world.say(
        f"At last, {hero.id} drew a deep breath and asked, \"Shall I play softly, or bold and bright?\""
    )
    world.say(
        f"{elder.id} said, \"Play softly first, so the dark may listen.\""
    )
    world.say(
        f"Then {hero.id} played a gentle tune for the villagers at {world.setting.place}, and the notes warmed the air like bread from the oven."
    )
    world.say(
        f"The shy ones came closer, the worried ones stopped trembling, and even the wind seemed to lean in."
    )
    world.say(
        f"In the end, the accordion was safe, the {charm.label} held fast, and {hero.id} was no longer afraid."
    )
    world.say(
        f"{hero.id} and {elder.id} walked home together under the darkening sky, while the last note followed them like a lantern."
    )
    hero.feel("fear", -1.0)
    hero.feel("joy", 1.0)
    elder.feel("worry", -1.0)


def tell(setting: Setting, event: Event, charm: Charm, hero_name: str, gender: str, kin: str, trait: str) -> World:
    world = create_world(setting, event, charm, hero_name, gender, kin, trait)
    opening(world)
    tension(world)
    turn(world)
    resolution(world)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    event: Event = f["event"]
    return [
        f'Write a short folk tale for a child about an accordion, kindness, and a little suspense.',
        f"Tell a gentle story where {hero.id} must use an accordion during {event.stage}, then solve a worried problem by talking kindly.",
        f'Write a simple village tale that includes the word "accordion" and ends with a warm, brave note.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    elder: Entity = f["elder"]
    event: Event = f["event"]
    charm: Charm = f["charm"]
    return [
        QAItem(
            question=f"What did {hero.id} love in the story?",
            answer=f"{hero.id} loved an old red accordion, because its music could brighten the village.",
        ),
        QAItem(
            question=f"Why did the night feel tense for {hero.id} at {world.setting.place}?",
            answer=f"The night felt tense because the path was hush-quiet and {hero.id} worried the accordion might fail when it was needed most.",
        ),
        QAItem(
            question=f"How did {elder.id} help {hero.id} solve the problem?",
            answer=f"{elder.id} stayed calm, spoke kindly, and gave {hero.id} the {charm.label} so the accordion would sit safer during the walk and song.",
        ),
        QAItem(
            question=f"What changed at the end of the tale?",
            answer=f"By the end, {hero.id} was not afraid anymore, the villagers heard a gentle tune, and the accordion became part of a warm, safe homeward walk.",
        ),
    ]


KNOWLEDGE = {
    "accordion": [
        QAItem(
            question="What is an accordion?",
            answer="An accordion is a musical instrument with keys or buttons and a middle part that opens and closes like a little box.",
        ),
        QAItem(
            question="How does an accordion make sound?",
            answer="An accordion makes sound when a player pushes and pulls the bellows and presses the keys or buttons so air moves through reeds.",
        ),
    ],
    "kindness": [
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and thoughtful to other people.",
        )
    ],
    "dialogue": [
        QAItem(
            question="What is dialogue in a story?",
            answer="Dialogue is when characters speak to each other using words in quotation marks.",
        )
    ],
    "suspense": [
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of wondering what will happen next, especially when something important might go wrong.",
        )
    ],
    "folk tale": [
        QAItem(
            question="What is a folk tale?",
            answer="A folk tale is a simple story that people have told again and again, often with a village, a lesson, and a little magic or wonder.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(KNOWLEDGE["accordion"] + KNOWLEDGE["kindness"] + KNOWLEDGE["dialogue"] + KNOWLEDGE["suspense"] + KNOWLEDGE["folk tale"])


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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place,Event,Charm) :- affords(Place,Event), needs_charm(Event,Charm).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for e in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, e))
    for eid, ev in EVENTS.items():
        lines.append(asp.fact("event", eid))
        lines.append(asp.fact("needs_charm", eid, select_charm(ev).id if select_charm(ev) else "none"))
    for cid, ch in CHARMS.items():
        lines.append(asp.fact("charm", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_story_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for ev in setting.affords:
            ch = select_charm(EVENTS[ev])
            if ch is not None:
                combos.append((place, ev, ch.id))
    return sorted(combos)


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_story_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about accordion, suspense, kindness, and dialogue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--kin", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_story_combos()
    if args.place or args.event or args.charm:
        combos = [c for c in combos if (args.place is None or c[0] == args.place) and (args.event is None or c[1] == args.event) and (args.charm is None or c[2] == args.charm)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, event_id, charm_id = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    kin = args.kin or rng.choice(["mother", "father", "grandmother", "grandfather"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    trait = args.trait or rng.choice(TRAITS)
    if args.charm and args.charm != charm_id:
        raise StoryError("Selected charm does not fit the event.")
    return StoryParams(place=place, event=event_id, charm=charm_id, name=name, gender=gender, kin=kin, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], EVENTS[params.event], CHARMS[params.charm], params.name, params.gender, params.kin, params.trait)
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
    StoryParams(place="village", event="market", charm="strap", name="Mira", gender="girl", kin="grandmother", trait="kind"),
    StoryParams(place="bridge", event="bridge", charm="lantern", name="Bram", gender="boy", kin="father", trait="brave"),
    StoryParams(place="path", event="forest", charm="lantern", name="Lina", gender="girl", kin="mother", trait="quiet"),
    StoryParams(place="village", event="barn", charm="strap", name="Oren", gender="boy", kin="grandfather", trait="lively"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} valid combos:")
        for v in vals:
            print(" ", v)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.event} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
