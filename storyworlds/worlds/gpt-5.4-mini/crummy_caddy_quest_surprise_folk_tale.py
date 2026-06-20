#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/crummy_caddy_quest_surprise_folk_tale.py
=========================================================================

A small standalone storyworld in a folk-tale style: a child goes on a quest
with a crummy caddy, discovers a surprise, and ends with a useful change in the
world. The simulated domain is intentionally tiny: one helper object, one path,
one seeker, one elder, and one surprising reveal.

The seed words "crummy" and "caddy" are woven into the story, and the narrative
instruments are quest and surprise.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
        female = {"girl", "mother", "woman", "queen", "elder"}
        male = {"boy", "father", "man", "king", "elder"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    place: str
    mood: str
    path: str
    landmark: str
    ending_image: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Quest:
    id: str
    goal: str
    seek: str
    need: str
    reward: str
    tension: str
    path: str
    win: str
    fail: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Surprise:
    id: str
    reveal: str
    body: str
    gift: str
    solves: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Caddy:
    id: str
    label: str
    phrase: str
    crummy: str
    helps: str
    repair: str
    sturdy: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_fatigue(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["travel"] < THRESHOLD or e.meters["burden"] < THRESHOLD:
            continue
        sig = ("fatigue", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["tired"] += 1
        out.append("__fatigue__")
    return out


def _r_hope(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["hope"] < THRESHOLD:
            continue
        sig = ("hope", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["brave"] += 1
        out.append("__hope__")
    return out


CAUSAL_RULES = [Rule("fatigue", "social", _r_fatigue), Rule("hope", "social", _r_hope)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def small_reasonable_gate(quest: Quest, caddy: Caddy, surprise: Surprise) -> bool:
    return "carry" in caddy.tags and "quest" in quest.tags and "surprise" in surprise.tags


def caddy_can_help(caddy: Caddy) -> bool:
    return caddy.sturdy


def maybe_fix_caddy(world: World, seeker: Entity, caddy: Caddy, elder: Entity) -> None:
    seeker.memes["trust"] += 1
    world.say(
        f'{elder.label_word.capitalize()} smiled and said, "A caddy can be crummy '
        f'and still carry a brave heart, but this one needs a little mend."'
    )
    if caddy_can_help(caddy):
        caddy_state = "held together"
    else:
        caddy_state = "wobbled"
    world.say(f"The old caddy {caddy_state} in {seeker.id}'s hands.")


def journey(world: World, seeker: Entity, elder: Entity, quest: Quest, caddy: Caddy) -> None:
    seeker.meters["travel"] += 1
    seeker.memes["hope"] += 1
    world.say(
        f"Long ago, in a quiet village, {seeker.id} took up {caddy.phrase} for a quest. "
        f"It was a {caddy.crummy} little thing, but it was all {seeker.pronoun('subject')} had."
    )
    world.say(
        f"{seeker.id} set out along {quest.path}, where the reeds brushed the path "
        f"and the birds called like fiddles in the wind."
    )
    world.say(
        f"{seeker.id} sought {quest.goal} because {quest.need}, and the old tale said "
        f"the reward would be {quest.reward}."
    )


def warn(world: World, elder: Entity, seeker: Entity, quest: Quest, caddy: Caddy) -> None:
    world.say(
        f'At the gate, {elder.id} said, "{quest.tension}, child. '
        f'Even a {caddy.crummy} caddy must be watched, or your quest will spill its hope."'
    )
    seeker.memes["worry"] += 1


def refuse_or_go(world: World, seeker: Entity, elder: Entity, quest: Quest, caddy: Caddy) -> None:
    if caddy.sturdy:
        world.say(
            f'{seeker.id} tied the crooked handle and went on, because a quest is '
            f'not made by perfect tools, but by steady hands.'
        )
    else:
        world.say(
            f'{seeker.id} nearly turned back, yet the road ahead was bright with purpose, '
            f"so {seeker.pronoun('subject')} went anyway."
        )


def surprise_turn(world: World, seeker: Entity, elder: Entity, quest: Quest, surprise: Surprise, caddy: Caddy) -> None:
    world.say(
        f"By the river stones, the surprise appeared: {surprise.reveal}. "
        f"{surprise.body}"
    )
    seeker.memes["hope"] += 1
    seeker.meters["burden"] -= 1
    caddy.sturdy = True
    world.say(
        f"In the surprise was {surprise.gift}, and at once the {caddy.label} could {surprise.solves}."
    )


def homecoming(world: World, seeker: Entity, elder: Entity, quest: Quest, setting: Setting, caddy: Caddy) -> None:
    world.say(
        f"At last, {seeker.id} returned by {setting.ending_image}, carrying the caddy that was no longer quite so crummy."
    )
    world.say(
        f"{elder.label_word.capitalize()} laughed softly, and the village had a new story: "
        f"{quest.win}."
    )
    seeker.memes["joy"] += 1
    elder.memes["joy"] += 1


def tell(setting: Setting, quest: Quest, surprise: Surprise, caddy: Caddy,
         seeker_name: str = "Mina", seeker_gender: str = "girl",
         elder_name: str = "Gran", elder_gender: str = "elder") -> World:
    world = World()
    seeker = world.add(Entity(seeker_name, kind="character", type=seeker_gender, role="seeker"))
    elder = world.add(Entity(elder_name, kind="character", type=elder_gender, role="elder", label="the elder"))
    world.add(Entity("path", type="path", label=setting.path))
    world.add(Entity("landmark", type="landmark", label=setting.landmark))
    caddy_ent = world.add(Entity(caddy.id, type="thing", label=caddy.label))
    caddy_ent.meters["wear"] += 1
    caddy_ent.attrs["phrase"] = caddy.phrase

    journey(world, seeker, elder, quest, caddy)
    world.para()
    warn(world, elder, seeker, quest, caddy)
    refuse_or_go(world, seeker, elder, quest, caddy)

    world.para()
    surprise_turn(world, seeker, elder, quest, surprise, caddy)
    maybe_fix_caddy(world, seeker, caddy, elder)

    world.para()
    propagate(world)
    homecoming(world, seeker, elder, quest, setting, caddy)

    world.facts.update(
        seeker=seeker,
        elder=elder,
        quest=quest,
        surprise=surprise,
        caddy=caddy,
        setting=setting,
        outcome="changed",
        repaired=caddy.sturdy,
    )
    return world


SETTINGS = {
    "meadow": Setting("meadow", "the meadow", "folk-song quiet", "the green lane", "the old stone well", "the moon over the willow"),
    "woods": Setting("woods", "the woods", "pine-shadow quiet", "the deer trail", "the fox den", "the sun through the branches"),
    "hills": Setting("hills", "the hills", "wind-bright quiet", "the winding hill path", "the bell tree", "the ridge above the village"),
}

QUESTS = {
    "moss_star": Quest("moss_star", "the moss-star", "seek the moss-star", "the village lamp had gone dim", "a warm light for the hall", "the road would test a patient heart", "the winding lane beyond the mill", "the lantern would shine again", "the quest would fail without hope", {"quest"}),
    "lost_song": Quest("lost_song", "the lost song", "find the lost song", "the harvest feast had no music", "a song to wake the dancers", "the hills kept the tune hidden", "the path past the bee trees", "the dance would begin again", "the song would stay hidden", {"quest"}),
    "river_key": Quest("river_key", "the river key", "bring back the river key", "the gate to the spring was shut", "fresh water for the village", "the river would test a brave step", "the path along the reeds", "the spring would open", "the village would thirst", {"quest"}),
}

SURPRISES = {
    "bird_gift": Surprise("bird_gift", "a blue bird dropped a tiny charm at {seeker}'s feet", "The bird tilted its head as if it had been waiting for the right traveler.", "a silver pin", "carry the caddy without spilling", {"surprise"}),
    "hidden_patch": Surprise("hidden_patch", "a patch of moonflower cloth was tucked under a stone", "It was stitched with old luck and smelled like rain.", "a strong lining", "hold the caddy upright", {"surprise"}),
    "kind_mouse": Surprise("kind_mouse", "a little mouse dragged out a wooden peg", "The mouse twitched its whiskers, proud as a king.", "a new peg", "keep the handle steady", {"surprise"}),
}

CADDIES = {
    "basket": Caddy("basket", "a caddy", "a battered caddy", "crummy", "carry the quest-gatherings", "become sturdy", sturdy=False, tags={"carry"}),
    "tray": Caddy("tray", "a caddy tray", "a crummy caddy tray", "crummy", "hold the quest-things", "hold together", sturdy=False, tags={"carry"}),
    "cart": Caddy("cart", "a hand caddy", "a crummy hand caddy", "crummy", "hold the bright prize", "roll smoothly", sturdy=False, tags={"carry"}),
}

GIRL_NAMES = ["Mina", "Lina", "Rae", "Sela", "Tara"]
BOY_NAMES = ["Jon", "Perrin", "Wes", "Niko", "Bram"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, q, su) for s in SETTINGS for q in QUESTS for su in SURPRISES if small_reasonable_gate(QUESTS[q], CADDIES["basket"], SURPRISES[su])]


@dataclass
@dataclass
class StoryParams:
    setting: str
    quest: str
    surprise: str
    caddy: str
    seeker: str
    seeker_gender: str
    elder: str
    elder_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    q = f["quest"]
    c = f["caddy"]
    s = f["surprise"]
    return [
        f'Write a folk-tale style quest story for a small child that includes the words "{c.label}" and "crummy".',
        f"Tell a gentle quest story where {f['seeker'].id} carries {c.phrase}, meets a surprise, and keeps going.",
        f"Write a short folk tale with a surprise in the road and a caddy that starts crummy but becomes useful.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    seeker, elder, q, s, c = f["seeker"], f["elder"], f["quest"], f["surprise"], f["caddy"]
    return [
        QAItem(
            question="Who went on the quest?",
            answer=f"{seeker.id} went on the quest, with {elder.label_word} watching over the road."
        ),
        QAItem(
            question="What did the seeker carry?",
            answer=f"{seeker.id} carried {c.phrase}. It was crummy at first, but it was the only thing ready for the journey."
        ),
        QAItem(
            question="What surprise did they find?",
            answer=f"They found {s.reveal}. The surprise brought a useful gift that helped the caddy work better."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {seeker.id} coming home safely and the caddy no longer feeling so crummy. The quest changed a weak thing into a useful one."
        ),
    ]


KNOWLEDGE = {
    "quest": [("What is a quest?", "A quest is a journey with a goal. Someone goes out to find, bring back, or fix something important.")],
    "surprise": [("What is a surprise?", "A surprise is something you do not expect. It can be a person, a gift, or a helpful thing that suddenly appears.")],
    "caddy": [("What is a caddy?", "A caddy is a container or carrier used to hold things and move them from place to place.")],
    "crummy": [("What does crummy mean?", "Crummy means old, shabby, or not very good. A crummy thing can still be useful if someone mends it.")],
    "folk": [("What makes a story feel like a folk tale?", "A folk tale often feels old and gentle, with a brave traveler, a lesson, and a little bit of magic or wonder.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["quest"].tags) | set(world.facts["surprise"].tags) | {"caddy", "crummy", "folk"}
    out: list[QAItem] = []
    for k in ["folk", "quest", "surprise", "caddy", "crummy"]:
        if k in tags:
            q, a = KNOWLEDGE[k][0]
            out.append(QAItem(q, a))
    return out


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
    for e in list(world.entities.values()):
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
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("meadow", "moss_star", "bird_gift", "basket", "Mina", "girl", "Gran", "elder"),
    StoryParams("woods", "lost_song", "hidden_patch", "tray", "Jon", "boy", "Gran", "elder"),
    StoryParams("hills", "river_key", "kind_mouse", "cart", "Lina", "girl", "Gran", "elder"),
]


ASP_RULES = r"""
valid(S, Q, U) :- setting(S), quest(Q), surprise(U), quest(Q), surprise(U).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for u in SURPRISES:
        lines.append(asp.fact("surprise", u))
    for c in CADDIES:
        lines.append(asp.fact("caddy", c))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, quest=None, surprise=None, caddy=None, seeker=None, seeker_gender=None, elder=None, elder_gender=None, seed=None), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale quest world with a crummy caddy and a surprise.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--caddy", choices=CADDIES)
    ap.add_argument("--seeker")
    ap.add_argument("--seeker-gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["elder"])
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.quest is None or c[1] == args.quest)
              and (args.surprise is None or c[2] == args.surprise)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, surprise = rng.choice(sorted(combos))
    caddy = args.caddy or rng.choice(sorted(CADDIES))
    if not small_reasonable_gate(QUESTS[quest], CADDIES[caddy], SURPRISES[surprise]):
        raise StoryError("That caddy cannot support this quest and surprise.")
    gender = args.seeker_gender or rng.choice(["girl", "boy"])
    seeker = args.seeker or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or "Gran"
    elder_gender = "elder"
    return StoryParams(setting, quest, surprise, caddy, seeker, gender, elder, elder_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], QUESTS[params.quest], SURPRISES[params.surprise], CADDIES[params.caddy],
                 params.seeker, params.seeker_gender, params.elder, params.elder_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in [(i.question, i.answer) for i in story_qa(world)]],
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible quest combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
